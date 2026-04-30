"""Yandex AppMetrica funnel analysis tool."""

import asyncio
import json
from collections import defaultdict

from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...formatters.appmetrica import format_appmetrica_funnel_markdown
from ...models.appmetrica import AppMetricaFunnelInput
from ...models.common import ResponseFormat
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register funnel analysis tools."""

    @mcp.tool(
        name="appmetrica_get_funnel",
        annotations={
            "title": "Build AppMetrica Conversion Funnel",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def appmetrica_get_funnel(params: AppMetricaFunnelInput) -> str:
        """Build a conversion funnel from app events.

        Exports raw event data via Logs API and calculates conversion
        between sequential steps. Each step is an event name. A user
        counts for step N only if they also completed steps 1..N-1
        (in any order within the period).

        Optional publisher_filter / tracker_filter restricts the funnel
        to users whose attributed install came from a given AppMetrica
        publisher (e.g. "Yandex.Direct") or tracker (substring match
        against tracker_name). When set we additionally pull the
        installations log and intersect by appmetrica_device_id.

        Note: Logs API is asynchronous — the helper polls until ready.
        Large date ranges may take 30s–10min to prepare. If you hit a
        timeout, narrow date_since/date_until or raise max_wait_seconds.
        """
        try:
            need_install_filter = bool(
                params.publisher_filter or params.tracker_filter
            )

            if need_install_filter:
                installs_task = api_client.appmetrica_logs_export(
                    export_type="installations",
                    application_id=params.app_id,
                    date_since=params.date_since,
                    date_until=params.date_until,
                    fields=[
                        "appmetrica_device_id",
                        "publisher_name",
                        "tracker_name",
                    ],
                    max_wait_seconds=params.max_wait_seconds,
                )
                events_task = api_client.appmetrica_logs_export(
                    export_type="events",
                    application_id=params.app_id,
                    date_since=params.date_since,
                    date_until=params.date_until,
                    fields=[
                        "appmetrica_device_id",
                        "event_name",
                        "event_datetime",
                    ],
                    max_wait_seconds=params.max_wait_seconds,
                )
                gather_results = await asyncio.gather(
                    installs_task, events_task, return_exceptions=True
                )
                for r in gather_results:
                    if isinstance(r, BaseException):
                        raise r
                installs, rows = gather_results

                allowed_devices: set[str] | None = set()
                for inst in installs:
                    device = inst.get("appmetrica_device_id", "")
                    if not device:
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
                    allowed_devices.add(device)
            else:
                rows = await api_client.appmetrica_logs_export(
                    export_type="events",
                    application_id=params.app_id,
                    date_since=params.date_since,
                    date_until=params.date_until,
                    fields=[
                        "appmetrica_device_id",
                        "event_name",
                        "event_datetime",
                    ],
                    max_wait_seconds=params.max_wait_seconds,
                )
                allowed_devices = None

            user_events: dict[str, set[str]] = defaultdict(set)
            for row in rows:
                device_id = row.get("appmetrica_device_id", "")
                event_name = row.get("event_name", "")
                if not device_id or not event_name:
                    continue
                if allowed_devices is not None and device_id not in allowed_devices:
                    continue
                user_events[device_id].add(event_name)

            total_users = len(user_events)

            step_users: list[int] = []
            required_events: set[str] = set()
            for step_name in params.steps:
                required_events.add(step_name)
                count = sum(
                    1
                    for events in user_events.values()
                    if required_events.issubset(events)
                )
                step_users.append(count)

            if params.response_format == ResponseFormat.JSON:
                funnel_data = {
                    "total_users": total_users,
                    "filters": {
                        "publisher_filter": params.publisher_filter,
                        "tracker_filter": params.tracker_filter,
                    },
                    "steps": [
                        {
                            "step": i + 1,
                            "event": name,
                            "users": users,
                            "conversion_from_prev": (
                                round(users / step_users[i - 1] * 100, 1)
                                if i > 0 and step_users[i - 1] > 0
                                else None
                            ),
                        }
                        for i, (name, users) in enumerate(
                            zip(params.steps, step_users, strict=True)
                        )
                    ],
                }
                return json.dumps(funnel_data, indent=2, ensure_ascii=False)

            return format_appmetrica_funnel_markdown(
                params.steps,
                step_users,
                total_users,
                publisher_filter=params.publisher_filter,
                tracker_filter=params.tracker_filter,
            )

        except Exception as e:
            return handle_api_error(e)
