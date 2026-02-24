"""Yandex Direct ad videos tools."""

import base64
import json
import os
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

from ...client import api_client
from ...utils import handle_api_error


class UploadVideoInput(BaseModel):
    """Input for uploading a video."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    file_path: str = Field(..., description="Local file path to the video (MP4, WebM, MOV, AVI)")
    name: Optional[str] = Field(default=None, description="Video name (optional)")


class UploadVideoByUrlInput(BaseModel):
    """Input for uploading a video by URL."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    urls: List[str] = Field(..., min_length=1, max_length=10, description="Video URLs to upload (max 10)")


class GetAdVideosInput(BaseModel):
    """Input for getting ad videos."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    video_ids: Optional[List[str]] = Field(default=None, description="Filter by video IDs")
    limit: int = Field(default=100, ge=1, le=10000)


def register(mcp: FastMCP) -> None:
    """Register ad video tools."""

    @mcp.tool(
        name="direct_upload_video",
        annotations={
            "title": "Upload Video for Ad Extensions",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_upload_video(params: UploadVideoInput) -> str:
        """Upload a video file for use as video extension in ads.

        Supported formats: MP4, WebM, MOV, QT, FLV, AVI.
        Max size: 100 MB. Duration: 5-60 seconds.
        Returns a VideoId to use with creatives.
        """
        try:
            file_path = params.file_path
            if not os.path.exists(file_path):
                return f"Error: File not found: {file_path}"

            file_size = os.path.getsize(file_path)
            if file_size > 100 * 1024 * 1024:
                return f"Error: File too large ({file_size / 1024 / 1024:.1f} MB). Max 100 MB."

            with open(file_path, "rb") as f:
                video_data = base64.b64encode(f.read()).decode("utf-8")

            ad_video = {"VideoData": video_data}
            if params.name:
                ad_video["Name"] = params.name
            else:
                ad_video["Name"] = os.path.basename(file_path)

            request_params = {"AdVideos": [ad_video]}

            result = await api_client.direct_request("advideos", "add", request_params, timeout=300.0)

            if "error" in result:
                err = result["error"]
                return f"API Error: {err.get('error_code')}: {err.get('error_string')} | {err.get('error_detail', '')}"

            add_results = result.get("result", {}).get("AddResults", [])

            if add_results and add_results[0].get("Id"):
                video_id = add_results[0]["Id"]
                return f"Video uploaded successfully!\nVideoId: {video_id}\nFile: {os.path.basename(file_path)} ({file_size / 1024 / 1024:.1f} MB)\n\nNext: Check status with direct_get_advideos, then create creative with direct_create_video_creative."

            errors = []
            for r in add_results:
                if r.get("Errors"):
                    errors.extend([f"{e.get('Code')}: {e.get('Message')} | {e.get('Details', '')}" for e in r["Errors"]])

            return f"Failed to upload video:\n" + "\n".join(f"- {e}" for e in errors)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_get_advideos",
        annotations={
            "title": "Get Ad Videos Status",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_advideos(params: GetAdVideosInput) -> str:
        """Get uploaded ad videos and their processing status.

        Statuses: NEW, CONVERTING, READY, ERROR.
        Video must be READY before creating a creative from it.
        """
        try:
            selection_criteria = {}
            if params.video_ids:
                selection_criteria["Ids"] = params.video_ids

            request_params = {
                "SelectionCriteria": selection_criteria,
                "FieldNames": ["Id", "Status"],
                "Page": {"Limit": params.limit}
            }

            result = await api_client.direct_request("advideos", "get", request_params)

            if "error" in result:
                err = result["error"]
                return f"API Error: {err.get('error_code')}: {err.get('error_string')} | {err.get('error_detail', '')}"

            videos = result.get("result", {}).get("AdVideos", [])

            if not videos:
                return "No ad videos found."

            lines = ["# Ad Videos\n"]
            lines.append("| ID | Status |")
            lines.append("|----|--------|")
            for v in videos:
                lines.append(f"| {v.get('Id')} | {v.get('Status')} |")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)
