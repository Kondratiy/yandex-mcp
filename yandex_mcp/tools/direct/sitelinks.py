"""Yandex Direct sitelinks tools."""

import json
from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...models.common import ResponseFormat
from ...models.direct_extended import (
    GetSitelinksInput,
    AddSitelinksInput,
    DeleteSitelinksInput,
)
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register sitelinks tools."""

    @mcp.tool(
        name="direct_get_sitelinks",
        annotations={
            "title": "Get Yandex Direct Sitelinks",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_sitelinks(params: GetSitelinksInput) -> str:
        """Get sitelink sets from Yandex Direct.

        Sitelinks are additional links shown under the main ad.
        Each set can contain up to 8 sitelinks.
        """
        try:
            selection_criteria = {}

            if params.sitelink_set_ids:
                selection_criteria["Ids"] = params.sitelink_set_ids

            request_params = {
                "SelectionCriteria": selection_criteria,
                "FieldNames": ["Id"],
                "SitelinkFieldNames": ["Title", "Href", "Description", "TurboPageId"],
                "Page": {
                    "Limit": params.limit,
                    "Offset": params.offset
                }
            }

            result = await api_client.direct_request("sitelinks", "get", request_params, account=params.account)
            sitelink_sets = result.get("result", {}).get("SitelinksSets", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"sitelink_sets": sitelink_sets, "total": len(sitelink_sets)}, indent=2, ensure_ascii=False)

            # Format as markdown
            if not sitelink_sets:
                return "No sitelink sets found."

            lines = ["# Sitelink Sets\n"]
            for ss in sitelink_sets:
                lines.append(f"## Set ID: {ss.get('Id')}")
                sitelinks = ss.get("Sitelinks", [])
                for i, sl in enumerate(sitelinks, 1):
                    lines.append(f"  {i}. **{sl.get('Title', 'N/A')}** → {sl.get('Href', 'N/A')}")
                    if sl.get('Description'):
                        lines.append(f"     _{sl['Description']}_")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_add_sitelinks",
        annotations={
            "title": "Add Yandex Direct Sitelinks",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_add_sitelinks(params: AddSitelinksInput) -> str:
        """Create a new sitelink set.

        Creates a set of sitelinks that can be attached to ads.
        Each set can contain 1-8 sitelinks.
        Max total length for sitelinks 1-4 is 66 chars.
        Max total length for sitelinks 5-8 is 66 chars.
        """
        try:
            sitelinks_data = []
            for sl in params.sitelinks:
                item = {"Title": sl.title, "Href": sl.href}
                if sl.description:
                    item["Description"] = sl.description
                sitelinks_data.append(item)

            request_params = {
                "SitelinksSets": [{
                    "Sitelinks": sitelinks_data
                }]
            }

            result = await api_client.direct_request("sitelinks", "add", request_params, account=params.account)
            add_results = result.get("result", {}).get("AddResults", [])

            if add_results and add_results[0].get("Id"):
                return f"Sitelink set created successfully. ID: {add_results[0]['Id']}"

            errors = []
            for r in add_results:
                if r.get("Errors"):
                    errors.extend([e.get("Message", "Unknown error") for e in r["Errors"]])

            return f"Failed to create sitelink set:\n" + "\n".join(f"- {e}" for e in errors)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_delete_sitelinks",
        annotations={
            "title": "Delete Yandex Direct Sitelinks",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_delete_sitelinks(params: DeleteSitelinksInput) -> str:
        """Delete sitelink sets.

        WARNING: Deleted sitelink sets will be removed from all ads using them.
        """
        try:
            request_params = {
                "SelectionCriteria": {"Ids": params.sitelink_set_ids}
            }

            result = await api_client.direct_request("sitelinks", "delete", request_params, account=params.account)
            delete_results = result.get("result", {}).get("DeleteResults", [])

            success = [r["Id"] for r in delete_results if r.get("Id") and not r.get("Errors")]
            errors = []
            for r in delete_results:
                if r.get("Errors"):
                    errors.extend([f"ID {r.get('Id', '?')}: {e.get('Message', 'Unknown error')}" for e in r["Errors"]])

            response = f"Successfully deleted {len(success)} sitelink set(s)."
            if errors:
                response += f"\n\nErrors:\n" + "\n".join(f"- {e}" for e in errors)

            return response

        except Exception as e:
            return handle_api_error(e)
