"""Markdown formatters for Yandex AppMetrica API responses."""

from typing import Any


def format_appmetrica_applications_markdown(apps: list[dict[str, Any]]) -> str:
    """Format AppMetrica applications list as markdown."""
    if not apps:
        return "No applications found."

    lines = ["# AppMetrica Applications\n"]
    for app in apps:
        app_id = app.get("id", "N/A")
        lines.append(f"## {app.get('name', 'Unnamed')} (ID: {app_id})")
        lines.append(f"- **Time Zone**: {app.get('time_zone_name', 'N/A')}")
        lines.append(f"- **Create Date**: {app.get('create_date', 'N/A')}")

        if app.get("permission"):
            lines.append(f"- **Permission**: {app['permission']}")

        lines.append("")

    return "\n".join(lines)


def format_appmetrica_application_markdown(app: dict[str, Any]) -> str:
    """Format a single AppMetrica application as markdown."""
    lines = [f"# {app.get('name', 'Unnamed')} (ID: {app.get('id', 'N/A')})\n"]
    lines.append(f"- **Time Zone**: {app.get('time_zone_name', 'N/A')}")
    lines.append(f"- **Create Date**: {app.get('create_date', 'N/A')}")
    lines.append(f"- **Permission**: {app.get('permission', 'N/A')}")

    if app.get("label"):
        lines.append(f"- **Label**: {app['label']}")

    return "\n".join(lines)


def format_appmetrica_report_markdown(data: dict[str, Any]) -> str:
    """Format AppMetrica report data as markdown."""
    lines = ["# AppMetrica Report\n"]

    query = data.get("query", {})
    lines.append("## Query Parameters")
    lines.append(f"- **Period**: {query.get('date1', 'N/A')} - {query.get('date2', 'N/A')}")

    if query.get("dimensions"):
        dims = query["dimensions"]
        lines.append(f"- **Dimensions**: {', '.join(dims) if isinstance(dims, list) else dims}")
    if query.get("metrics"):
        mets = query["metrics"]
        lines.append(f"- **Metrics**: {', '.join(mets) if isinstance(mets, list) else mets}")

    lines.append("")

    totals = data.get("totals", [])
    if totals:
        lines.append("## Totals")
        metrics = query.get("metrics", [])
        if isinstance(metrics, str):
            metrics = metrics.split(",")
        for i, total in enumerate(totals):
            metric_name = metrics[i] if i < len(metrics) else f"Metric {i + 1}"
            lines.append(f"- **{metric_name}**: {total:,.2f}")
        lines.append("")

    rows = data.get("data", [])
    if rows:
        lines.append(f"## Data ({len(rows)} rows)")
        for row in rows[:50]:
            dims = row.get("dimensions", [])
            metrics_vals = row.get("metrics", [])

            dim_str = " / ".join(
                str(d.get("name", d.get("id", "N/A"))) if isinstance(d, dict) else str(d)
                for d in dims
            ) if dims else "Total"

            metrics_str = ", ".join(f"{v:,.2f}" for v in metrics_vals)
            lines.append(f"- **{dim_str}**: {metrics_str}")

        if len(rows) > 50:
            lines.append(f"\n*...and {len(rows) - 50} more rows*")

    return "\n".join(lines)


def format_appmetrica_drilldown_markdown(data: dict[str, Any]) -> str:
    """Format AppMetrica drilldown report as markdown."""
    lines = ["# AppMetrica Drilldown Report\n"]

    query = data.get("query", {})
    lines.append(f"- **Period**: {query.get('date1', 'N/A')} - {query.get('date2', 'N/A')}")
    lines.append("")

    rows = data.get("data", [])
    if rows:
        for row in rows[:50]:
            dims = row.get("dimensions", [])
            metrics_vals = row.get("metrics", [])

            dim_str = " / ".join(
                str(d.get("name", d.get("id", "N/A"))) if isinstance(d, dict) else str(d)
                for d in dims
            ) if dims else "Total"

            metrics_str = ", ".join(f"{v:,.2f}" for v in metrics_vals)
            expand = " (expandable)" if row.get("expand", False) else ""
            lines.append(f"- **{dim_str}**: {metrics_str}{expand}")

        if len(rows) > 50:
            lines.append(f"\n*...and {len(rows) - 50} more rows*")
    else:
        lines.append("No data found.")

    return "\n".join(lines)


def format_appmetrica_logs_markdown(data: dict[str, Any], export_type: str) -> str:
    """Format AppMetrica Logs API response as markdown."""
    lines = [f"# AppMetrica Logs Export: {export_type}\n"]

    rows = data.get("data", [])
    if not rows:
        lines.append("No data found for the specified period.")
        return "\n".join(lines)

    lines.append(f"**Total rows**: {len(rows)}\n")

    if rows:
        headers = list(rows[0].keys())
        preview = rows[:20]

        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join("---" for _ in headers) + " |")
        for row in preview:
            vals = [str(row.get(h, ""))[:40] for h in headers]
            lines.append("| " + " | ".join(vals) + " |")

        if len(rows) > 20:
            lines.append(f"\n*...and {len(rows) - 20} more rows*")

    return "\n".join(lines)


def format_appmetrica_events_markdown(data: dict[str, Any]) -> str:
    """Format AppMetrica events report as markdown."""
    lines = ["# AppMetrica Events\n"]

    query = data.get("query", {})
    lines.append(f"**Period**: {query.get('date1', 'N/A')} - {query.get('date2', 'N/A')}\n")

    rows = data.get("data", [])
    if not rows:
        lines.append("No events found.")
        return "\n".join(lines)

    lines.append("| Event | Users |")
    lines.append("| --- | ---: |")
    for row in rows[:100]:
        dims = row.get("dimensions", [])
        metrics = row.get("metrics", [0])
        event_name = dims[0].get("name", "N/A") if dims and isinstance(dims[0], dict) else "N/A"
        users = metrics[0] if len(metrics) > 0 else 0
        lines.append(f"| {event_name} | {users:,.0f} |")

    if len(rows) > 100:
        lines.append(f"\n*...and {len(rows) - 100} more events*")

    return "\n".join(lines)


def format_appmetrica_crashes_markdown(data: dict[str, Any]) -> str:
    """Format AppMetrica crashes report as markdown."""
    lines = ["# AppMetrica Crashes\n"]

    query = data.get("query", {})
    lines.append(f"**Period**: {query.get('date1', 'N/A')} - {query.get('date2', 'N/A')}\n")

    totals = data.get("totals", [])
    if totals:
        lines.append(f"**Total crashes**: {totals[0]:,.0f}\n")

    rows = data.get("data", [])
    if not rows:
        lines.append("No crashes found.")
        return "\n".join(lines)

    for row in rows[:50]:
        dims = row.get("dimensions", [])
        metrics = row.get("metrics", [0])

        dim_str = " / ".join(
            str(d.get("name", d.get("id", "N/A"))) if isinstance(d, dict) else str(d)
            for d in dims
        ) if dims else "Total"

        crash_count = metrics[0] if metrics else 0
        lines.append(f"- **{dim_str}**: {crash_count:,.0f} crashes")

    if len(rows) > 50:
        lines.append(f"\n*...and {len(rows) - 50} more rows*")

    return "\n".join(lines)


def format_appmetrica_funnel_markdown(
    steps: list[str],
    step_users: list[int],
    total_users: int,
    publisher_filter: str | None = None,
    tracker_filter: str | None = None,
) -> str:
    """Format funnel analysis as markdown."""
    lines = ["# AppMetrica Funnel\n"]

    if publisher_filter or tracker_filter:
        filter_parts = []
        if publisher_filter:
            filter_parts.append(f"publisher = `{publisher_filter}`")
        if tracker_filter:
            filter_parts.append(f"tracker contains `{tracker_filter}`")
        lines.append(f"**Filters**: {' AND '.join(filter_parts)}\n")

    if not step_users:
        lines.append("No data found for the specified events and period.")
        return "\n".join(lines)

    lines.append(f"**Total unique users in period**: {total_users:,}\n")
    lines.append("| Step | Event | Users | % of Total | Conversion |")
    lines.append("| ---: | --- | ---: | ---: | ---: |")

    for i, (step_name, users) in enumerate(zip(steps, step_users, strict=True)):
        pct_total = (users / total_users * 100) if total_users > 0 else 0
        if i == 0:
            conversion = "—"
        else:
            prev = step_users[i - 1]
            conversion = f"{users / prev * 100:.1f}%" if prev > 0 else "0%"

        lines.append(
            f"| {i + 1} | {step_name} | {users:,} | {pct_total:.1f}% | {conversion} |"
        )

    if len(step_users) >= 2 and step_users[0] > 0:
        overall = step_users[-1] / step_users[0] * 100
        lines.append(f"\n**Overall conversion**: {overall:.1f}%")

    return "\n".join(lines)


def format_appmetrica_attribution_markdown(summary: dict[str, Any]) -> str:
    """Format attribution-join report as markdown."""
    lines = ["# AppMetrica Attribution Join\n"]

    lines.append(
        f"- **Period**: {summary.get('date_since')} → {summary.get('date_until')}"
    )
    lines.append(f"- **Aggregate by**: `{summary.get('aggregate_by')}`")

    filters = summary.get("filters") or {}
    if filters.get("publisher_filter"):
        lines.append(f"- **Publisher filter**: `{filters['publisher_filter']}`")
    if filters.get("tracker_filter"):
        lines.append(f"- **Tracker filter**: `{filters['tracker_filter']}`")
    if filters.get("conversion_events"):
        events_str = ", ".join(f"`{e}`" for e in filters["conversion_events"])
        lines.append(f"- **Conversion events**: {events_str}")

    totals = summary.get("totals", {})
    lines.append(
        f"- **Matched installs**: {totals.get('matched_installs', 0):,} "
        f"across {totals.get('groups_total', 0):,} groups "
        f"(showing top {totals.get('groups_shown', 0):,})"
    )
    lines.append("")

    rows = summary.get("rows") or []
    if not rows:
        lines.append("No installs matched the filters in this period.")
        return "\n".join(lines)

    event_columns: list[str] = summary.get("event_columns") or []
    include_revenue = bool(summary.get("include_revenue"))

    headers = ["#", "Group", "Installs"]
    for ev in event_columns:
        headers.append(f"{ev} (uniq)")
    if include_revenue:
        headers += ["Payers", "Revenue", "Cur."]

    lines.append("| " + " | ".join(headers) + " |")
    aligns = ["---:", "---", "---:"] + ["---:"] * len(event_columns)
    if include_revenue:
        aligns += ["---:", "---:", "---"]
    lines.append("| " + " | ".join(aligns) + " |")

    for idx, row in enumerate(rows, start=1):
        installs = row.get("installs", 0)
        cells = [str(idx), str(row.get("key", "")), f"{installs:,}"]
        unique = row.get("events_unique_users") or {}
        for ev in event_columns:
            count = unique.get(ev, 0)
            cr = (count / installs * 100) if installs else 0
            cells.append(f"{count:,} ({cr:.1f}%)")
        if include_revenue:
            cells.append(f"{row.get('payers', 0):,}")
            cells.append(f"{row.get('revenue', 0):,.2f}")
            cells.append(", ".join(row.get("currencies") or []) or "—")
        lines.append("| " + " | ".join(cells) + " |")

    if event_columns:
        lines.append("")
        lines.append(
            "_Cell format: unique users with the event (conversion-rate vs installs)._"
        )

    return "\n".join(lines)


def format_appmetrica_install_attribution_markdown(summary: dict[str, Any]) -> str:
    """Format live install attribution report as markdown."""
    lines = ["# AppMetrica Install Attribution (live)\n"]
    lines.append(
        f"- **Period**: {summary.get('date1')} → {summary.get('date2')}"
    )
    lines.append(f"- **Aggregate by**: `{summary.get('aggregate_by')}`")
    if summary.get("publisher_filter"):
        lines.append(f"- **Publisher filter**: `{summary['publisher_filter']}`")
    events = summary.get("conversion_events") or []
    if events:
        ev_str = ", ".join(f"`{e}`" for e in events)
        lines.append(f"- **Conversion events**: {ev_str}")

    totals = summary.get("totals", {})
    lines.append(
        f"- **Installs (total in scope)**: {totals.get('installs_total', 0):,} "
        f"across {totals.get('groups_total', 0):,} groups "
        f"(showing top {totals.get('groups_shown', 0):,})"
    )
    ev_tot = totals.get("events_totals", {}) or {}
    if ev_tot:
        parts = [f"`{k}`: {v:,}" for k, v in ev_tot.items()]
        lines.append(f"- **Conversion totals**: {', '.join(parts)}")
    lines.append("")

    rows = summary.get("rows") or []
    if not rows:
        lines.append("No installs in this period.")
        return "\n".join(lines)

    headers = ["#", "Group", "Installs"]
    for ev in events:
        headers.append(f"{ev}")
    aligns = ["---:", "---", "---:"] + ["---:"] * len(events)
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(aligns) + " |")

    for idx, row in enumerate(rows, start=1):
        installs = row.get("installs", 0)
        cells = [str(idx), str(row.get("key", "")), f"{installs:,}"]
        ev_data = row.get("events") or {}
        for ev in events:
            d = ev_data.get(ev) or {}
            users = d.get("users", 0)
            cr = d.get("conversion_rate_pct", 0.0)
            cells.append(f"{users:,} ({cr:.1f}%)")
        lines.append("| " + " | ".join(cells) + " |")

    if events:
        lines.append("")
        lines.append(
            "_Cell format: unique devices that fired the event "
            "(conversion-rate vs installs in the same group)._"
        )

    return "\n".join(lines)


def format_appmetrica_push_group_markdown(group: dict[str, Any]) -> str:
    """Format push group as markdown."""
    lines = ["# Push Group Created\n"]
    lines.append(f"- **Group ID**: {group.get('id', 'N/A')}")
    lines.append(f"- **App ID**: {group.get('app_id', 'N/A')}")
    lines.append(f"- **Name**: {group.get('name', 'N/A')}")
    return "\n".join(lines)


def format_appmetrica_push_status_markdown(transfer: dict[str, Any]) -> str:
    """Format push transfer status as markdown."""
    lines = ["# Push Transfer Status\n"]
    lines.append(f"- **Transfer ID**: {transfer.get('id', 'N/A')}")
    lines.append(f"- **Status**: {transfer.get('status', 'N/A')}")
    lines.append(f"- **Tag**: {transfer.get('tag', 'N/A')}")
    lines.append(f"- **Group ID**: {transfer.get('group_id', 'N/A')}")
    lines.append(f"- **Created**: {transfer.get('creation_date', 'N/A')}")

    errors = transfer.get("errors", [])
    if errors:
        lines.append("\n## Errors")
        for err in errors:
            lines.append(f"- {err}")

    return "\n".join(lines)
