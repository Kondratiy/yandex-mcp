"""Yandex Direct negative keyword shared sets tools."""

import json
from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...models.common import ResponseFormat
from ...models.direct_extended import (
    GetNegativeKeywordSharedSetsInput,
    AddNegativeKeywordSharedSetInput,
    UpdateNegativeKeywordSharedSetInput,
    DeleteNegativeKeywordSharedSetsInput,
)
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register negative keyword shared sets tools."""

    @mcp.tool(
        name="direct_get_negative_keyword_shared_sets",
        annotations={
            "title": "Get Yandex Direct Negative Keyword Shared Sets",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_negative_keyword_shared_sets(params: GetNegativeKeywordSharedSetsInput) -> str:
        """Get negative keyword shared sets from Yandex Direct.

        Shared sets contain negative keywords that can be linked to multiple campaigns.
        This allows managing negative keywords centrally.
        """
        try:
            selection_criteria = {}

            if params.shared_set_ids:
                selection_criteria["Ids"] = params.shared_set_ids

            request_params = {
                "SelectionCriteria": selection_criteria,
                "FieldNames": ["Id", "Name", "NegativeKeywords", "AssociatedCampaignIds"],
                "Page": {"Limit": params.limit}
            }

            result = await api_client.direct_request("negativekeywordsharedsets", "get", request_params)
            shared_sets = result.get("result", {}).get("NegativeKeywordSharedSets", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"shared_sets": shared_sets, "total": len(shared_sets)}, indent=2, ensure_ascii=False)

            if not shared_sets:
                return "No negative keyword shared sets found."

            lines = ["# Negative Keyword Shared Sets\n"]
            for ss in shared_sets:
                lines.append(f"## {ss.get('Name', 'Unnamed')} (ID: {ss.get('Id')})")

                campaigns = ss.get('AssociatedCampaignIds', [])
                if campaigns:
                    lines.append(f"- **Linked Campaigns**: {', '.join(map(str, campaigns))}")
                else:
                    lines.append("- **Linked Campaigns**: None")

                keywords = ss.get('NegativeKeywords', [])
                if keywords:
                    lines.append(f"- **Keywords** ({len(keywords)}):")
                    for kw in keywords[:20]:
                        lines.append(f"  - {kw}")
                    if len(keywords) > 20:
                        lines.append(f"  ... and {len(keywords) - 20} more")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_add_negative_keyword_shared_set",
        annotations={
            "title": "Add Yandex Direct Negative Keyword Shared Set",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_add_negative_keyword_shared_set(params: AddNegativeKeywordSharedSetInput) -> str:
        """Create a new negative keyword shared set.

        After creating, link it to campaigns using direct_link_shared_set_to_campaign.
        Max 20 sets per account. Max 5000 keywords per set.
        """
        try:
            shared_set = {
                "Name": params.name,
                "NegativeKeywords": params.negative_keywords
            }

            request_params = {
                "NegativeKeywordSharedSets": [shared_set]
            }

            result = await api_client.direct_request("negativekeywordsharedsets", "add", request_params)
            add_results = result.get("result", {}).get("AddResults", [])

            if add_results and add_results[0].get("Id"):
                return f"Negative keyword shared set created successfully. ID: {add_results[0]['Id']}"

            errors = []
            for r in add_results:
                if r.get("Errors"):
                    errors.extend([e.get("Message", "Unknown error") for e in r["Errors"]])

            return f"Failed to create shared set:\n" + "\n".join(f"- {e}" for e in errors)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_update_negative_keyword_shared_set",
        annotations={
            "title": "Update Yandex Direct Negative Keyword Shared Set",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_update_negative_keyword_shared_set(params: UpdateNegativeKeywordSharedSetInput) -> str:
        """Update a negative keyword shared set.

        Updates the name and/or keywords in the set.
        Note: Setting negative_keywords replaces all existing keywords.
        """
        try:
            shared_set = {"Id": params.shared_set_id}

            if params.name:
                shared_set["Name"] = params.name
            if params.negative_keywords:
                shared_set["NegativeKeywords"] = params.negative_keywords

            request_params = {
                "NegativeKeywordSharedSets": [shared_set]
            }

            result = await api_client.direct_request("negativekeywordsharedsets", "update", request_params)
            update_results = result.get("result", {}).get("UpdateResults", [])

            errors = []
            for r in update_results:
                if r.get("Errors"):
                    errors.extend([e.get("Message", "Unknown error") for e in r["Errors"]])

            if errors:
                return f"Update completed with issues:\n" + "\n".join(f"- {e}" for e in errors)

            return f"Shared set {params.shared_set_id} updated successfully."

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_delete_negative_keyword_shared_sets",
        annotations={
            "title": "Delete Yandex Direct Negative Keyword Shared Sets",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_delete_negative_keyword_shared_sets(params: DeleteNegativeKeywordSharedSetsInput) -> str:
        """Delete negative keyword shared sets.

        WARNING: Deleting a shared set will unlink it from all associated campaigns.
        """
        try:
            request_params = {
                "SelectionCriteria": {"Ids": params.shared_set_ids}
            }

            result = await api_client.direct_request("negativekeywordsharedsets", "delete", request_params)
            delete_results = result.get("result", {}).get("DeleteResults", [])

            success = [r["Id"] for r in delete_results if r.get("Id") and not r.get("Errors")]

            return f"Successfully deleted {len(success)} shared set(s)."

        except Exception as e:
            return handle_api_error(e)
