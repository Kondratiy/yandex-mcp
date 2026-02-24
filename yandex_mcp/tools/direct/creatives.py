"""Yandex Direct creatives tools."""

import json
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

from ...client import api_client
from ...utils import handle_api_error


class CreateVideoCreativeInput(BaseModel):
    """Input for creating a video extension creative."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    video_id: str = Field(..., description="VideoId from uploaded video (from direct_upload_video)")


class GetCreativesInput(BaseModel):
    """Input for getting creatives."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    creative_ids: Optional[List[int]] = Field(default=None, description="Filter by creative IDs")
    types: Optional[List[str]] = Field(
        default=None,
        description="Filter by types: VIDEO_EXTENSION_CREATIVE, CPC_VIDEO_CREATIVE, CPM_VIDEO_CREATIVE"
    )
    limit: int = Field(default=100, ge=1, le=10000)


def register(mcp: FastMCP) -> None:
    """Register creative tools."""

    @mcp.tool(
        name="direct_create_video_creative",
        annotations={
            "title": "Create Video Extension Creative",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_create_video_creative(params: CreateVideoCreativeInput) -> str:
        """Create a VIDEO_EXTENSION_CREATIVE from an uploaded video.

        The video must have status READY (check with direct_get_advideos).
        Returns a CreativeId to attach to ads via direct_update_ad.
        """
        try:
            request_params = {
                "Creatives": [{
                    "VideoExtensionCreative": {
                        "VideoId": params.video_id
                    }
                }]
            }

            result = await api_client.direct_request("creatives", "add", request_params)

            if "error" in result:
                err = result["error"]
                return f"API Error: {err.get('error_code')}: {err.get('error_string')} | {err.get('error_detail', '')}"

            add_results = result.get("result", {}).get("AddResults", [])

            if add_results and add_results[0].get("Id"):
                creative_id = add_results[0]["Id"]
                return f"Video creative created successfully!\nCreativeId: {creative_id}\n\nNext: Attach to ads using direct_update_ad with video_extension_creative_id={creative_id}"

            errors = []
            for r in add_results:
                if r.get("Errors"):
                    errors.extend([f"{e.get('Code')}: {e.get('Message')} | {e.get('Details', '')}" for e in r["Errors"]])

            return f"Failed to create creative:\n" + "\n".join(f"- {e}" for e in errors)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_get_creatives",
        annotations={
            "title": "Get Creatives",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_creatives(params: GetCreativesInput) -> str:
        """Get creatives (video, banners) from Yandex Direct.

        Types: VIDEO_EXTENSION_CREATIVE, CPC_VIDEO_CREATIVE, CPM_VIDEO_CREATIVE
        """
        try:
            selection_criteria = {}
            if params.creative_ids:
                selection_criteria["Ids"] = params.creative_ids
            if params.types:
                selection_criteria["Types"] = params.types

            request_params = {
                "SelectionCriteria": selection_criteria,
                "FieldNames": ["Id", "Type", "Name", "PreviewUrl", "ThumbnailUrl"],
                "VideoExtensionCreativeFieldNames": ["Duration"],
                "Page": {"Limit": params.limit}
            }

            result = await api_client.direct_request("creatives", "get", request_params)

            if "error" in result:
                err = result["error"]
                return f"API Error: {err.get('error_code')}: {err.get('error_string')} | {err.get('error_detail', '')}"

            creatives = result.get("result", {}).get("Creatives", [])

            if not creatives:
                return "No creatives found."

            lines = ["# Creatives\n"]
            lines.append("| ID | Type | Name | Duration |")
            lines.append("|----|------|------|----------|")
            for c in creatives:
                duration = c.get("VideoExtensionCreative", {}).get("Duration", "N/A")
                lines.append(f"| {c.get('Id')} | {c.get('Type')} | {c.get('Name', 'N/A')} | {duration}s |")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)
