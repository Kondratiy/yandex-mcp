"""Markdown formatters for Yandex Metrika responses."""

from typing import Dict, List


def format_metrika_counters_markdown(counters: List[Dict]) -> str:
    """Format Metrika counters as markdown."""
    if not counters:
        return "No counters found."

    lines = ["# Metrika Counters\n"]
    for counter in counters:
        lines.append(f"## {counter.get('name', 'Unnamed')} (ID: {counter.get('id')})")

        site = counter.get("site2", {}).get("site", "N/A")
        lines.append(f"- **Site**: {site}")
        lines.append(f"- **Status**: {counter.get('status', 'N/A')}")
        lines.append(f"- **Code Status**: {counter.get('code_status', 'N/A')}")
        lines.append(f"- **Owner**: {counter.get('owner_login', 'N/A')}")

        if counter.get("favorite"):
            lines.append("- **Favorite**: Yes")

        lines.append("")

    return "\n".join(lines)


def format_metrika_report_markdown(data: Dict) -> str:
    """Format Metrika report data as markdown."""
    lines = ["# Metrika Report\n"]

    query = data.get("query", {})
    lines.append("## Query Parameters")
    lines.append(f"- **Period**: {query.get('date1', 'N/A')} - {query.get('date2', 'N/A')}")

    if query.get("dimensions"):
        lines.append(f"- **Dimensions**: {', '.join(query['dimensions'])}")
    if query.get("metrics"):
        lines.append(f"- **Metrics**: {', '.join(query['metrics'])}")

    lines.append("")

    # Totals
    totals = data.get("totals", [])
    if totals:
        lines.append("## Totals")
        metrics = query.get("metrics", [])
        for i, total in enumerate(totals):
            metric_name = metrics[i] if i < len(metrics) else f"Metric {i+1}"
            lines.append(f"- **{metric_name}**: {total:,.2f}")
        lines.append("")

    # Data rows
    rows = data.get("data", [])
    if rows:
        lines.append(f"## Data ({len(rows)} rows)")
        for row in rows[:50]:  # Limit to 50 rows in markdown
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


def format_metrika_goals_markdown(goals: List[Dict], counter_id: int) -> str:
    """Format Metrika goals as markdown."""
    if not goals:
        return "No goals configured for this counter."

    lines = [f"# Goals for Counter {counter_id}\n"]
    for goal in goals:
        lines.append(f"## {goal.get('name', 'Unnamed')} (ID: {goal.get('id')})")
        lines.append(f"- **Type**: {goal.get('type', 'N/A')}")

        conditions = goal.get("conditions", [])
        if conditions:
            lines.append("- **Conditions**:")
            for cond in conditions:
                lines.append(f"  - {cond.get('type', 'N/A')}: {cond.get('url', cond.get('value', 'N/A'))}")

        lines.append("")

    return "\n".join(lines)


def format_metrika_segments_markdown(segments: List[Dict], counter_id: int) -> str:
    """Format Metrika segments as markdown."""
    if not segments:
        return "No segments found for this counter."

    lines = [f"# Segments for Counter {counter_id}\n"]
    for segment in segments:
        lines.append(f"## {segment.get('name', 'Unnamed')} (ID: {segment.get('segment_id')})")
        lines.append(f"- **Expression**: `{segment.get('expression', 'N/A')}`")
        lines.append(f"- **Created**: {segment.get('create_time', 'N/A')}")

        lines.append("")

    return "\n".join(lines)


def format_metrika_filters_markdown(filters: List[Dict], counter_id: int) -> str:
    """Format Metrika filters as markdown."""
    if not filters:
        return "No filters found for this counter."

    lines = [f"# Filters for Counter {counter_id}\n"]
    for f in filters:
        lines.append(f"## Filter ID: {f.get('id')}")
        lines.append(f"- **Attribute**: {f.get('attr', 'N/A')}")
        lines.append(f"- **Type**: {f.get('type', 'N/A')}")
        lines.append(f"- **Value**: {f.get('value', 'N/A')}")
        lines.append(f"- **Action**: {f.get('action', 'N/A')}")
        lines.append(f"- **Status**: {f.get('status', 'N/A')}")

        lines.append("")

    return "\n".join(lines)


def format_metrika_grants_markdown(grants: List[Dict], counter_id: int) -> str:
    """Format Metrika access grants as markdown."""
    if not grants:
        return "No access grants found for this counter."

    lines = [f"# Access Grants for Counter {counter_id}\n"]
    for grant in grants:
        lines.append(f"## {grant.get('user_login', 'Unknown')}")
        lines.append(f"- **Permission**: {grant.get('perm', 'N/A')}")
        lines.append(f"- **Created**: {grant.get('created_at', 'N/A')}")

        if grant.get("comment"):
            lines.append(f"- **Comment**: {grant.get('comment')}")

        lines.append("")

    return "\n".join(lines)


def format_metrika_comparison_markdown(data: Dict) -> str:
    """Format Metrika comparison report as markdown."""
    lines = ["# Comparison Report\n"]

    query = data.get("query", {})
    lines.append("## Segment A")
    lines.append(f"- **Period**: {query.get('date1_a', 'N/A')} - {query.get('date2_a', 'N/A')}")
    if query.get("filters_a"):
        lines.append(f"- **Filter**: {query.get('filters_a')}")

    lines.append("\n## Segment B")
    lines.append(f"- **Period**: {query.get('date1_b', 'N/A')} - {query.get('date2_b', 'N/A')}")
    if query.get("filters_b"):
        lines.append(f"- **Filter**: {query.get('filters_b')}")

    lines.append("")

    # Totals comparison
    totals_a = data.get("totals_a", [])
    totals_b = data.get("totals_b", [])
    if totals_a or totals_b:
        lines.append("## Totals Comparison")
        metrics = query.get("metrics", [])
        for i in range(max(len(totals_a), len(totals_b))):
            metric_name = metrics[i] if i < len(metrics) else f"Metric {i+1}"
            val_a = totals_a[i] if i < len(totals_a) else 0
            val_b = totals_b[i] if i < len(totals_b) else 0
            diff = val_b - val_a
            pct = (diff / val_a * 100) if val_a != 0 else 0
            lines.append(f"- **{metric_name}**: A={val_a:,.2f}, B={val_b:,.2f}, Diff={diff:+,.2f} ({pct:+.1f}%)")
        lines.append("")

    return "\n".join(lines)


def format_metrika_drilldown_markdown(data: Dict) -> str:
    """Format Metrika drilldown report as markdown."""
    lines = ["# Drilldown Report\n"]

    query = data.get("query", {})
    lines.append(f"- **Period**: {query.get('date1', 'N/A')} - {query.get('date2', 'N/A')}")
    if query.get("dimensions"):
        lines.append(f"- **Dimensions**: {', '.join(query['dimensions'])}")
    lines.append("")

    rows = data.get("data", [])
    if rows:
        lines.append(f"## Data ({len(rows)} rows)")
        for row in rows[:50]:
            dims = row.get("dimensions", [])
            metrics_vals = row.get("metrics", [])
            expand = row.get("expand", False)

            dim_str = " > ".join(
                str(d.get("name", d.get("id", "N/A"))) if isinstance(d, dict) else str(d)
                for d in dims
            )

            metrics_str = ", ".join(f"{v:,.2f}" for v in metrics_vals)
            expand_marker = " [+]" if expand else ""
            lines.append(f"- **{dim_str}**{expand_marker}: {metrics_str}")

        if len(rows) > 50:
            lines.append(f"\n*...and {len(rows) - 50} more rows*")

    return "\n".join(lines)
