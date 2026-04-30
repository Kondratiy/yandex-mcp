"""Yandex Metrika report tools."""

import json
from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...models.common import ResponseFormat
from ...models.metrika import (
    MetrikaReportInput,
    MetrikaByTimeInput,
    MetrikaComparisonInput,
    MetrikaDrilldownInput,
)
from ...formatters.metrika import (
    format_metrika_report_markdown,
    format_metrika_comparison_markdown,
    format_metrika_drilldown_markdown,
)
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register report tools."""

    @mcp.tool(
        name="metrika_get_report",
        annotations={
            "title": "Get Yandex Metrika Statistics Report",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_get_report(params: MetrikaReportInput) -> str:
        """Get statistics report from Yandex Metrika.

        Retrieves traffic statistics with customizable metrics and dimensions.

        Common metrics:
        - ym:s:visits - Number of sessions
        - ym:s:users - Number of users
        - ym:s:pageviews - Page views
        - ym:s:bounceRate - Bounce rate
        - ym:s:avgVisitDurationSeconds - Average session duration
        - ym:s:goal<ID>reaches - Goal completions

        Common dimensions:
        - ym:s:date - Date
        - ym:s:trafficSource - Traffic source
        - ym:s:searchEngine - Search engine
        - ym:s:regionCountry - Country
        - ym:s:deviceCategory - Device type
        - ym:s:UTMSource, ym:s:UTMCampaign - UTM parameters
        - ym:s:lastDirectClickOrder - Yandex Direct campaign
        """
        try:
            query_params = {
                "id": params.counter_id,
                "metrics": ",".join(params.metrics),
                "limit": params.limit
            }

            if params.dimensions:
                query_params["dimensions"] = ",".join(params.dimensions)
            if params.date1:
                query_params["date1"] = params.date1
            if params.date2:
                query_params["date2"] = params.date2
            if params.filters:
                query_params["filters"] = params.filters
            if params.sort:
                query_params["sort"] = params.sort

            result = await api_client.metrika_request(
                "/stat/v1/data",
                params=query_params)

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(result, indent=2, ensure_ascii=False)

            return format_metrika_report_markdown(result)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_get_report_by_time",
        annotations={
            "title": "Get Yandex Metrika Time-Based Report",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_get_report_by_time(params: MetrikaByTimeInput) -> str:
        """Get time-based statistics report from Yandex Metrika.

        Retrieves statistics grouped by time periods (day, week, month, etc.).
        Useful for tracking trends and building charts.
        """
        try:
            query_params = {
                "id": params.counter_id,
                "metrics": ",".join(params.metrics),
                "group": params.group.value
            }

            if params.dimensions:
                query_params["dimensions"] = ",".join(params.dimensions)
            if params.date1:
                query_params["date1"] = params.date1
            if params.date2:
                query_params["date2"] = params.date2

            result = await api_client.metrika_request(
                "/stat/v1/data/bytime",
                params=query_params)

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(result, indent=2, ensure_ascii=False)

            # Format time-based report
            lines = ["# Time-Based Report\n"]

            query = result.get("query", {})
            lines.append(f"**Period**: {query.get('date1', 'N/A')} - {query.get('date2', 'N/A')}")
            lines.append(f"**Grouping**: {params.group.value}\n")

            time_intervals = result.get("time_intervals", [])
            data = result.get("data", [])

            if data:
                for row in data:
                    dims = row.get("dimensions", [])
                    metrics = row.get("metrics", [[]])

                    dim_str = " / ".join(
                        str(d.get("name", d.get("id", "N/A"))) if isinstance(d, dict) else str(d)
                        for d in dims
                    ) if dims else "Total"

                    lines.append(f"## {dim_str}")

                    # Show time series
                    if time_intervals and metrics:
                        for i, interval in enumerate(time_intervals):
                            interval_str = " - ".join(str(t) for t in interval) if isinstance(interval, list) else str(interval)
                            values = [m[i] if i < len(m) else 0 for m in metrics]
                            values_str = ", ".join(f"{v:,.2f}" for v in values)
                            lines.append(f"- {interval_str}: {values_str}")

                    lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_get_comparison_report",
        annotations={
            "title": "Get Yandex Metrika Comparison Report",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_get_comparison_report(params: MetrikaComparisonInput) -> str:
        """Get comparison report between two segments/periods.

        Compares metrics between two different time periods or segments.
        Useful for analyzing changes over time or A/B testing.
        """
        try:
            query_params = {
                "id": params.counter_id,
                "metrics": ",".join(params.metrics),
                "date1_a": params.date1_a,
                "date2_a": params.date2_a,
                "date1_b": params.date1_b,
                "date2_b": params.date2_b,
                "limit": params.limit
            }

            if params.dimensions:
                query_params["dimensions"] = ",".join(params.dimensions)
            if params.filters_a:
                query_params["filters_a"] = params.filters_a
            if params.filters_b:
                query_params["filters_b"] = params.filters_b

            result = await api_client.metrika_request(
                "/stat/v1/data/comparison",
                params=query_params)

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(result, indent=2, ensure_ascii=False)

            return format_metrika_comparison_markdown(result)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_get_drilldown_report",
        annotations={
            "title": "Get Yandex Metrika Drilldown Report",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_get_drilldown_report(params: MetrikaDrilldownInput) -> str:
        """Get drilldown (hierarchical) report from Yandex Metrika.

        Creates tree-view reports where you can drill down into specific branches.
        For example: Country > Region > City.
        """
        try:
            query_params = {
                "id": params.counter_id,
                "metrics": ",".join(params.metrics),
                "dimensions": ",".join(params.dimensions),
                "limit": params.limit
            }

            if params.date1:
                query_params["date1"] = params.date1
            if params.date2:
                query_params["date2"] = params.date2
            if params.filters:
                query_params["filters"] = params.filters
            if params.parent_id:
                query_params["parent_id"] = json.dumps(params.parent_id)

            result = await api_client.metrika_request(
                "/stat/v1/data/drilldown",
                params=query_params)

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(result, indent=2, ensure_ascii=False)

            return format_metrika_drilldown_markdown(result)

        except Exception as e:
            return handle_api_error(e)
