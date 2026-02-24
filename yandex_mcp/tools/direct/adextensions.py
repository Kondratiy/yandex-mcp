"""Yandex Direct ad extensions (callouts) tools."""

import json
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

from ...client import api_client
from ...models.common import ResponseFormat
from ...utils import handle_api_error


class GetAdExtensionsInput(BaseModel):
    """Input for getting ad extensions."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    extension_ids: Optional[List[int]] = Field(default=None, description="Filter by extension IDs")
    types: Optional[List[str]] = Field(default=None, description="Filter by types: CALLOUT")
    statuses: Optional[List[str]] = Field(default=None, description="Filter by statuses: ACCEPTED, MODERATION, REJECTED, DRAFT")
    limit: int = Field(default=100, ge=1, le=10000)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class AddCalloutInput(BaseModel):
    """Input for adding callout extensions."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    callout_texts: List[str] = Field(..., min_length=1, max_length=50, description="List of callout texts (max 25 chars each)")


class LinkCalloutsToAdInput(BaseModel):
    """Input for linking callouts to an ad."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    ad_id: int = Field(..., description="Ad ID to link callouts to")
    callout_ids: List[int] = Field(..., min_length=1, description="Callout extension IDs to link")


def register(mcp: FastMCP) -> None:
    """Register ad extension tools."""

    @mcp.tool(
        name="direct_get_adextensions",
        annotations={
            "title": "Get Ad Extensions (Callouts)",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_adextensions(params: GetAdExtensionsInput) -> str:
        """Get ad extensions (callouts/уточнения) from Yandex Direct."""
        try:
            selection_criteria = {}
            if params.extension_ids:
                selection_criteria["Ids"] = params.extension_ids
            if params.types:
                selection_criteria["Types"] = params.types
            if params.statuses:
                selection_criteria["Statuses"] = params.statuses

            request_params = {
                "SelectionCriteria": selection_criteria,
                "FieldNames": ["Id", "Type", "Status"],
                "CalloutFieldNames": ["CalloutText"],
                "Page": {"Limit": params.limit}
            }

            result = await api_client.direct_request("adextensions", "get", request_params)
            extensions = result.get("result", {}).get("AdExtensions", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"extensions": extensions, "total": len(extensions)}, indent=2, ensure_ascii=False)

            if not extensions:
                return "No ad extensions found."

            lines = ["# Ad Extensions (Callouts)\n"]
            lines.append("| ID | Type | Status | Text |")
            lines.append("|----|------|--------|------|")
            for ext in extensions:
                callout_text = ext.get("Callout", {}).get("CalloutText", "N/A")
                lines.append(f"| {ext.get('Id')} | {ext.get('Type')} | {ext.get('Status')} | {callout_text} |")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_add_callouts",
        annotations={
            "title": "Add Callout Extensions",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_add_callouts(params: AddCalloutInput) -> str:
        """Create new callout extensions (уточнения).

        Each callout text max 25 characters. Up to 50 callouts per ad.
        """
        try:
            extensions = [{"Callout": {"CalloutText": text}} for text in params.callout_texts]

            request_params = {"AdExtensions": extensions}

            result = await api_client.direct_request("adextensions", "add", request_params)
            add_results = result.get("result", {}).get("AddResults", [])

            ids = []
            errors = []
            for r in add_results:
                if r.get("Id"):
                    ids.append(r["Id"])
                elif r.get("Errors"):
                    errors.extend([f"{e.get('Code')}: {e.get('Message')}" for e in r["Errors"]])

            msg = ""
            if ids:
                msg += f"Created {len(ids)} callout(s). IDs: {', '.join(str(i) for i in ids)}\n"
            if errors:
                msg += f"Errors:\n" + "\n".join(f"- {e}" for e in errors)

            return msg or f"Unexpected response: {result}"

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_link_callouts_to_ad",
        annotations={
            "title": "Link Callouts to Ad",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_link_callouts_to_ad(params: LinkCalloutsToAdInput) -> str:
        """Link callout extensions to a text ad.

        Links existing callouts to an ad. The ad will need re-moderation.
        """
        try:
            ad_extensions = [
                {"AdExtensionId": cid, "Operation": "SET"}
                for cid in params.callout_ids
            ]

            request_params = {
                "Ads": [{
                    "Id": params.ad_id,
                    "TextAd": {
                        "CalloutSetting": {
                            "AdExtensions": ad_extensions
                        }
                    }
                }]
            }

            result = await api_client.direct_request("ads", "update", request_params, use_v501=True)
            update_results = result.get("result", {}).get("UpdateResults", [])

            if update_results and (update_results[0].get("Id") or update_results[0].get("Ids")):
                return f"Callouts linked to ad {params.ad_id} successfully. Ad sent for re-moderation."

            errors = []
            for r in update_results:
                if r.get("Errors"):
                    errors.extend([f"{e.get('Code')}: {e.get('Message')} | {e.get('Details', '')}" for e in r["Errors"]])
                if r.get("Warnings"):
                    errors.extend([f"Warning: {w.get('Message')}" for w in r["Warnings"]])

            if errors:
                return f"Failed to link callouts:\n" + "\n".join(f"- {e}" for e in errors)

            return f"Unexpected response: {result}"

        except Exception as e:
            return handle_api_error(e)
