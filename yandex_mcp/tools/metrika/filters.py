"""Yandex Metrika filter tools (NEW)."""

import json
from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...models.common import ResponseFormat
from ...models.metrika import (
    GetFiltersInput,
    CreateFilterInput,
    UpdateFilterInput,
    DeleteFilterInput,
)
from ...formatters.metrika import format_metrika_filters_markdown
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register filter tools."""

    @mcp.tool(
        name="metrika_get_filters",
        annotations={
            "title": "Get Yandex Metrika Filters",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_get_filters(params: GetFiltersInput) -> str:
        """Get filters for a Metrika counter.

        Filters exclude or include specific traffic from statistics.
        """
        try:
            result = await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}/filters")

            filters = result.get("filters", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"filters": filters, "total": len(filters)}, indent=2, ensure_ascii=False)

            return format_metrika_filters_markdown(filters, params.counter_id)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_create_filter",
        annotations={
            "title": "Create Yandex Metrika Filter",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def metrika_create_filter(params: CreateFilterInput) -> str:
        """Create a new filter for a Metrika counter.

        Filters allow you to exclude or include specific traffic.

        Filter attributes (attr):
        - url: Filter by URL
        - referer: Filter by referrer
        - uniq_id: Filter by unique ID
        - client_ip: Filter by IP address
        - title: Filter by page title

        Filter types:
        - only_mirrors: Include only site mirrors
        - uniq_id: Filter by unique ID
        - url_param: Filter by URL parameter
        - title: Filter by page title
        - referer: Filter by referrer
        - interval: Filter by time interval
        """
        try:
            data = {
                "filter": {
                    "attr": params.attr,
                    "type": params.type,
                    "value": params.value,
                    "action": params.action.value,
                    "status": params.status.value
                }
            }

            result = await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}/filters",
                method="POST",
                data=data)

            filter_data = result.get("filter", {})

            return f"""Filter created successfully!

**ID**: {filter_data.get('id')}
**Attribute**: {filter_data.get('attr')}
**Type**: {filter_data.get('type')}
**Value**: {filter_data.get('value')}
**Action**: {filter_data.get('action')}"""

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_update_filter",
        annotations={
            "title": "Update Yandex Metrika Filter",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_update_filter(params: UpdateFilterInput) -> str:
        """Update an existing filter."""
        try:
            filter_update = {}

            if params.value:
                filter_update["value"] = params.value
            if params.action:
                filter_update["action"] = params.action.value
            if params.status:
                filter_update["status"] = params.status.value

            if not filter_update:
                return "No fields specified for update."

            data = {"filter": filter_update}

            await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}/filter/{params.filter_id}",
                method="PUT",
                data=data)

            return f"Filter {params.filter_id} updated successfully."

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_delete_filter",
        annotations={
            "title": "Delete Yandex Metrika Filter",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_delete_filter(params: DeleteFilterInput) -> str:
        """Delete a filter from a Metrika counter."""
        try:
            await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}/filter/{params.filter_id}",
                method="DELETE")

            return f"Filter {params.filter_id} deleted successfully."

        except Exception as e:
            return handle_api_error(e)
