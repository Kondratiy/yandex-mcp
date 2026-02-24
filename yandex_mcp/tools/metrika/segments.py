"""Yandex Metrika segment tools (NEW)."""

import json
from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...models.common import ResponseFormat
from ...models.metrika import (
    GetSegmentsInput,
    CreateSegmentInput,
    UpdateSegmentInput,
    DeleteSegmentInput,
)
from ...formatters.metrika import format_metrika_segments_markdown
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register segment tools."""

    @mcp.tool(
        name="metrika_get_segments",
        annotations={
            "title": "Get Yandex Metrika Segments",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_get_segments(params: GetSegmentsInput) -> str:
        """Get segments for a Metrika counter.

        Segments allow you to analyze subsets of your audience.
        """
        try:
            result = await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}/apisegment/segments"
            )

            segments = result.get("segments", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"segments": segments, "total": len(segments)}, indent=2, ensure_ascii=False)

            return format_metrika_segments_markdown(segments, params.counter_id)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_create_segment",
        annotations={
            "title": "Create Yandex Metrika Segment",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def metrika_create_segment(params: CreateSegmentInput) -> str:
        """Create a new segment for a Metrika counter.

        Segments allow you to analyze specific audience subsets.

        Example expressions:
        - ym:s:trafficSource=='organic' - Organic traffic
        - ym:s:deviceCategory=='mobile' - Mobile users
        - ym:s:regionCountry=='ru' - Russian visitors
        - ym:s:goal<ID>IsReached=='Yes' - Users who completed a goal
        """
        try:
            data = {
                "segment": {
                    "name": params.name,
                    "expression": params.expression
                }
            }

            result = await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}/apisegment/segments",
                method="POST",
                data=data
            )

            segment = result.get("segment", {})

            return f"""Segment created successfully!

**ID**: {segment.get('segment_id')}
**Name**: {segment.get('name')}
**Expression**: {segment.get('expression')}

Use this segment in reports with the filters parameter."""

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_update_segment",
        annotations={
            "title": "Update Yandex Metrika Segment",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_update_segment(params: UpdateSegmentInput) -> str:
        """Update an existing segment."""
        try:
            segment_update = {}

            if params.name:
                segment_update["name"] = params.name
            if params.expression:
                segment_update["expression"] = params.expression

            if not segment_update:
                return "No fields specified for update."

            data = {"segment": segment_update}

            await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}/apisegment/segment/{params.segment_id}",
                method="PUT",
                data=data
            )

            return f"Segment {params.segment_id} updated successfully."

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_delete_segment",
        annotations={
            "title": "Delete Yandex Metrika Segment",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_delete_segment(params: DeleteSegmentInput) -> str:
        """Delete a segment from a Metrika counter."""
        try:
            await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}/apisegment/segment/{params.segment_id}",
                method="DELETE"
            )

            return f"Segment {params.segment_id} deleted successfully."

        except Exception as e:
            return handle_api_error(e)
