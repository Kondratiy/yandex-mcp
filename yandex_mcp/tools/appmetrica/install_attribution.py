"""Live install attribution via Reporting API (no Logs API polling)."""

import asyncio
import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...formatters.appmetrica import format_appmetrica_install_attribution_markdown
from ...models.appmetrica import (
    AppMetricaInstallAttributionInput,
    InstallAttributionAxis,
)
from ...models.common import ResponseFormat
from ...utils import handle_api_error


def _row_key(row: dict[str, Any], n_dims: int) -> tuple[tuple[str, str], ...]:
    """Stable tuple key for matching rows across queries.

    Each dim is encoded as (id, name) so rows with same id but
    differing display names still merge correctly.
    """
    dims = row.get("dimensions") or []
    return tuple(
        (
            str(d.get("id", "")) if isinstance(d, dict) else str(d),
            str(d.get("name", "")) if isinstance(d, dict) else "",
        )
        for d in dims[:n_dims]
    )


def _row_label(key: tuple[tuple[str, str], ...]) -> str:
    """Human-readable group label from the tuple key."""
    parts = []
    for _, name in key:
        parts.append(name or "(none)")
    return " / ".join(parts) if parts else "(total)"


def _row_devices(row: dict[str, Any]) -> int:
    metrics = row.get("metrics") or []
    if not metrics:
        return 0
    try:
        return int(metrics[0])
    except (TypeError, ValueError):
        return 0


def _build_filter(event_label: str | None) -> str | None:
    """Build filter clause. publisher_filter is applied post-hoc in code,
    not via API filters — combining ym:i:publisher with ym:ce:eventLabel
    in a single filters= triggers error 4009 on Reporting API.

    event_label charset is constrained by the input model validator
    ([A-Za-z0-9_.-]) so it's safe to interpolate directly.
    """
    if not event_label:
        return None
    return f"ym:ce:eventLabel=='{event_label}'"


def register(mcp: FastMCP) -> None:
    """Register live install_attribution tool."""

    @mcp.tool(
        name="appmetrica_install_attribution",
        annotations={
            "title": "AppMetrica Install Attribution (live, Reporting API)",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def appmetrica_install_attribution(
        params: AppMetricaInstallAttributionInput,
    ) -> str:
        """Install attribution by publisher / tracker with conversion rates.

        Builds N+1 parallel /stat/v1/data calls: 1 baseline (installs
        per group) + 1 per conversion event (installs per group whose
        users also fired that event). Returns a table with installs and
        per-event unique users + conversion-rates.

        This is the FAST path: results in seconds via Reporting API.
        Use appmetrica_attribution_join when you need revenue or
        click_url_parameters (UTM/Direct macros from the trackable URL).

        Example for 3 days × 2 events × 1 app: ~3 API calls in parallel,
        ~1-3 seconds total runtime.
        """
        try:
            n_dims = (
                2
                if params.aggregate_by == InstallAttributionAxis.PUBLISHER_AND_CAMPAIGN
                else 1
            )
            dims_str = (
                "ym:i:publisher,ym:i:campaign"
                if n_dims == 2
                else "ym:i:publisher"
            )
            metric = "ym:i:devices"

            base_query: dict[str, Any] = {
                "ids": params.app_id,
                "date1": params.date1,
                "date2": params.date2,
                "metrics": metric,
                "dimensions": dims_str,
                "limit": 1000,
            }

            tasks = [
                api_client.appmetrica_request(
                    "/stat/v1/data",
                    params=base_query,
                )
            ]
            for event in params.conversion_events:
                q = dict(base_query)
                q["filters"] = _build_filter(event)
                tasks.append(
                    api_client.appmetrica_request(
                        "/stat/v1/data",
                        params=q,
                    )
                )

            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, BaseException):
                    raise r
            base_resp = results[0]
            event_resps = results[1:]

            # Post-hoc publisher filter predicate (publisher is always
            # the FIRST dimension in our queries).
            def passes_publisher_filter(row: dict[str, Any]) -> bool:
                if not params.publisher_filter:
                    return True
                dims = row.get("dimensions") or []
                if not dims:
                    return False
                first = dims[0]
                name = first.get("name") if isinstance(first, dict) else ""
                return name == params.publisher_filter

            # Build base map
            base_rows = [
                r for r in (base_resp.get("data") or []) if passes_publisher_filter(r)
            ]
            base_total = sum(_row_devices(r) for r in base_rows)
            base_map: dict[tuple[tuple[str, str], ...], int] = {}
            for row in base_rows:
                k = _row_key(row, n_dims)
                base_map[k] = _row_devices(row)

            # Per-event maps
            event_maps: list[dict[tuple[tuple[str, str], ...], int]] = []
            event_totals: list[int] = []
            for resp in event_resps:
                rows = [
                    r for r in (resp.get("data") or []) if passes_publisher_filter(r)
                ]
                m: dict[tuple[tuple[str, str], ...], int] = {}
                total = 0
                for row in rows:
                    k = _row_key(row, n_dims)
                    devices = _row_devices(row)
                    m[k] = devices
                    total += devices
                event_maps.append(m)
                event_totals.append(total)

            # Sort base groups by install count desc, take top_n
            sorted_keys = sorted(
                base_map.keys(),
                key=lambda k: -base_map[k],
            )[: params.top_n]

            rows_out: list[dict[str, Any]] = []
            for k in sorted_keys:
                installs = base_map[k]
                row: dict[str, Any] = {
                    "key": _row_label(k),
                    "ids": [pair[0] for pair in k],
                    "installs": installs,
                    "events": {},
                }
                for ev_name, ev_map in zip(
                    params.conversion_events, event_maps, strict=True
                ):
                    devices = ev_map.get(k, 0)
                    cr = (devices / installs * 100) if installs else 0.0
                    row["events"][ev_name] = {
                        "users": devices,
                        "conversion_rate_pct": round(cr, 2),
                    }
                rows_out.append(row)

            summary = {
                "app_id": params.app_id,
                "date1": params.date1,
                "date2": params.date2,
                "aggregate_by": params.aggregate_by.value,
                "publisher_filter": params.publisher_filter,
                "conversion_events": params.conversion_events,
                "totals": {
                    "installs_total": base_total,
                    "groups_total": len(base_map),
                    "groups_shown": len(sorted_keys),
                    "events_totals": dict(
                        zip(params.conversion_events, event_totals, strict=True)
                    ),
                },
                "rows": rows_out,
            }

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(summary, indent=2, ensure_ascii=False)

            return format_appmetrica_install_attribution_markdown(summary)

        except Exception as e:
            return handle_api_error(e)
