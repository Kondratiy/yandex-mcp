"""Yandex AppMetrica attribution-join tool: installs × events × revenue."""

import asyncio
import json
from collections import defaultdict
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...formatters.appmetrica import format_appmetrica_attribution_markdown
from ...models.appmetrica import (
    AppMetricaAttributionInput,
    AttributionAggregateBy,
)
from ...models.common import ResponseFormat
from ...utils import handle_api_error


def _key_function(
    aggregate_by: AttributionAggregateBy,
) -> Callable[[dict[str, str]], str]:
    """Build a grouping key function from the chosen aggregation axis."""
    if aggregate_by == AttributionAggregateBy.PUBLISHER:
        return lambda info: info["publisher"] or "(none)"
    if aggregate_by == AttributionAggregateBy.TRACKER_NAME:
        return lambda info: info["tracker"] or "(none)"
    return lambda info: (
        f"{info['publisher'] or '(none)'} / {info['tracker'] or '(none)'}"
    )


def _safe_float(value) -> float:
    """Coerce Logs API revenue field to float, treating missing/garbage as 0."""
    if value in (None, "", "null"):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def register(mcp: FastMCP) -> None:
    """Register attribution-join tool."""

    @mcp.tool(
        name="appmetrica_attribution_join",
        annotations={
            "title": "AppMetrica Attribution Join (installs × events × revenue)",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def appmetrica_attribution_join(
        params: AppMetricaAttributionInput,
    ) -> str:
        """Join AppMetrica installs, events and (optionally) revenue logs locally.

        Pulls 2-3 Logs API exports in parallel, builds an
        appmetrica_device_id → install map, then aggregates events and
        revenue per (publisher, tracker_name). This bypasses the
        Reporting API limitation where ym:ce: events cannot be sliced
        by ym:i:publisher and lets you answer questions like:

            "Which Yandex.Direct campaign drove not just installs but
            registrations and purchases?"

        Workflow:
          1. installations log → device_id, publisher_name, tracker_name
          2. events log        → device_id, event_name (filtered to
             conversion_events if provided)
          3. revenue_events    → device_id, revenue_price, revenue_quantity
             (only if include_revenue=True)
          4. Local hash-join on appmetrica_device_id, group by
             aggregate_by axis, sort by install count desc, keep top_n.

        Notes:
          - Only conversions from devices installed within
            [date_since, date_until] are counted. To analyse retention
            of older cohorts, expand the date range.
          - Logs API is async — each export polls until ready
            (max_wait_seconds per export).
          - publisher_filter / tracker_filter pre-filter installs before
            the join to keep the result focused.
        """
        try:
            install_fields = [
                "appmetrica_device_id",
                "publisher_name",
                "tracker_name",
                "click_url_parameters",
                "install_datetime",
            ]
            event_fields = [
                "appmetrica_device_id",
                "event_name",
                "event_datetime",
            ]
            revenue_fields = [
                "appmetrica_device_id",
                "event_datetime",
                "revenue_quantity",
                "revenue_price",
                "revenue_currency",
            ]

            tasks = [
                api_client.appmetrica_logs_export(
                    export_type="installations",
                    application_id=params.app_id,
                    date_since=params.date_since,
                    date_until=params.date_until,
                    fields=install_fields,
                    max_wait_seconds=params.max_wait_seconds,
                ),
                api_client.appmetrica_logs_export(
                    export_type="events",
                    application_id=params.app_id,
                    date_since=params.date_since,
                    date_until=params.date_until,
                    fields=event_fields,
                    max_wait_seconds=params.max_wait_seconds,
                ),
            ]
            if params.include_revenue:
                tasks.append(
                    api_client.appmetrica_logs_export(
                        export_type="revenue_events",
                        application_id=params.app_id,
                        date_since=params.date_since,
                        date_until=params.date_until,
                        fields=revenue_fields,
                        max_wait_seconds=params.max_wait_seconds,
                    )
                )

            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, BaseException):
                    raise r
            installs: list[dict] = results[0]
            events: list[dict] = results[1]
            revenues: list[dict] = results[2] if params.include_revenue else []

            # 1. Build device → install info, applying pre-filters
            device_to_install: dict[str, dict[str, str]] = {}
            for inst in installs:
                device_id = inst.get("appmetrica_device_id") or ""
                if not device_id:
                    continue
                publisher = (inst.get("publisher_name") or "").strip()
                tracker = (inst.get("tracker_name") or "").strip()
                if (
                    params.publisher_filter
                    and publisher != params.publisher_filter
                ):
                    continue
                if (
                    params.tracker_filter
                    and params.tracker_filter not in tracker
                ):
                    continue
                device_to_install[device_id] = {
                    "publisher": publisher,
                    "tracker": tracker,
                    "click_url_parameters": (
                        inst.get("click_url_parameters") or ""
                    ),
                }

            key_fn = _key_function(params.aggregate_by)

            # 2. installs per group
            installs_per_key: dict[str, int] = defaultdict(int)
            for info in device_to_install.values():
                installs_per_key[key_fn(info)] += 1

            # 3. events per group per event_name (unique users + total)
            events_filter = (
                set(params.conversion_events) if params.conversion_events else None
            )
            unique_per_key: dict[str, dict[str, set]] = defaultdict(
                lambda: defaultdict(set)
            )
            total_per_key: dict[str, dict[str, int]] = defaultdict(
                lambda: defaultdict(int)
            )

            for ev in events:
                device_id = ev.get("appmetrica_device_id") or ""
                event_name = ev.get("event_name") or ""
                if not device_id or not event_name:
                    continue
                if events_filter is not None and event_name not in events_filter:
                    continue
                info = device_to_install.get(device_id)
                if not info:
                    continue
                k = key_fn(info)
                unique_per_key[k][event_name].add(device_id)
                total_per_key[k][event_name] += 1

            # 4. revenue per group
            revenue_per_key: dict[str, float] = defaultdict(float)
            payers_per_key: dict[str, set] = defaultdict(set)
            currencies_per_key: dict[str, set] = defaultdict(set)
            if params.include_revenue:
                for rev in revenues:
                    device_id = rev.get("appmetrica_device_id") or ""
                    if not device_id:
                        continue
                    info = device_to_install.get(device_id)
                    if not info:
                        continue
                    k = key_fn(info)
                    # Default qty to 1.0 only when missing/empty,
                    # not when it's literally 0 (legitimate zero-qty
                    # purchase event would otherwise inflate revenue).
                    qty_raw = rev.get("revenue_quantity")
                    if qty_raw in (None, ""):
                        qty = 1.0
                    else:
                        qty = _safe_float(qty_raw)
                    price = _safe_float(rev.get("revenue_price"))
                    revenue_per_key[k] += qty * price
                    payers_per_key[k].add(device_id)
                    cur = (rev.get("revenue_currency") or "").strip()
                    if cur:
                        currencies_per_key[k].add(cur)

            # 5. Sort + top_n
            sorted_keys = sorted(
                installs_per_key.keys(),
                key=lambda k: -installs_per_key[k],
            )[: params.top_n]

            # Collect distinct event names for column headers
            event_columns: list[str] = []
            seen: set = set()
            if params.conversion_events:
                for name in params.conversion_events:
                    if name not in seen:
                        event_columns.append(name)
                        seen.add(name)
            else:
                for k in sorted_keys:
                    for name in unique_per_key[k]:
                        if name not in seen:
                            event_columns.append(name)
                            seen.add(name)

            # 6. Build output
            rows = []
            for k in sorted_keys:
                row = {
                    "key": k,
                    "installs": installs_per_key[k],
                    "events_unique_users": {
                        name: len(unique_per_key[k].get(name, set()))
                        for name in event_columns
                    },
                    "events_total": {
                        name: total_per_key[k].get(name, 0)
                        for name in event_columns
                    },
                }
                if params.include_revenue:
                    row["revenue"] = round(revenue_per_key[k], 2)
                    row["payers"] = len(payers_per_key[k])
                    row["currencies"] = sorted(currencies_per_key[k])
                rows.append(row)

            summary = {
                "app_id": params.app_id,
                "date_since": params.date_since,
                "date_until": params.date_until,
                "aggregate_by": params.aggregate_by.value,
                "filters": {
                    "publisher_filter": params.publisher_filter,
                    "tracker_filter": params.tracker_filter,
                    "conversion_events": params.conversion_events,
                },
                "totals": {
                    "matched_installs": sum(installs_per_key.values()),
                    "groups_total": len(installs_per_key),
                    "groups_shown": len(sorted_keys),
                },
                "include_revenue": params.include_revenue,
                "rows": rows,
                "event_columns": event_columns,
            }

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(summary, indent=2, ensure_ascii=False)

            return format_appmetrica_attribution_markdown(summary)

        except Exception as e:
            return handle_api_error(e)
