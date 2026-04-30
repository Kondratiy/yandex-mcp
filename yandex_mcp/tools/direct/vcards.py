"""Yandex Direct vCards tools."""

import json
from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...models.common import ResponseFormat
from ...models.direct_extended import (
    GetVCardsInput,
    AddVCardInput,
    DeleteVCardsInput,
)
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register vCard tools."""

    @mcp.tool(
        name="direct_get_vcards",
        annotations={
            "title": "Get Yandex Direct VCards",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_vcards(params: GetVCardsInput) -> str:
        """Get vCards from Yandex Direct.

        VCards contain business contact information displayed in ads.
        """
        try:
            selection_criteria = {}

            if params.vcard_ids:
                selection_criteria["Ids"] = params.vcard_ids

            request_params = {
                "SelectionCriteria": selection_criteria,
                "FieldNames": [
                    "Id", "CampaignId", "Country", "City", "Street", "House",
                    "CompanyName", "Phone", "WorkTime", "ExtraMessage"
                ],
                "Page": {
                    "Limit": params.limit,
                    "Offset": params.offset
                }
            }

            result = await api_client.direct_request("vcards", "get", request_params, account=params.account)
            vcards = result.get("result", {}).get("VCards", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"vcards": vcards, "total": len(vcards)}, indent=2, ensure_ascii=False)

            # Format as markdown
            if not vcards:
                return "No vCards found."

            lines = ["# VCards\n"]
            for vc in vcards:
                lines.append(f"## {vc.get('CompanyName', 'Unnamed')} (ID: {vc.get('Id')})")
                lines.append(f"- **Campaign ID**: {vc.get('CampaignId')}")
                lines.append(f"- **Phone**: {vc.get('Phone', 'N/A')}")
                address_parts = [vc.get('Country', ''), vc.get('City', ''), vc.get('Street', ''), vc.get('House', '')]
                address = ', '.join(p for p in address_parts if p)
                lines.append(f"- **Address**: {address or 'N/A'}")
                if vc.get('WorkTime'):
                    lines.append(f"- **Work Time**: {vc.get('WorkTime')}")
                if vc.get('ExtraMessage'):
                    lines.append(f"- **Extra**: {vc.get('ExtraMessage')}")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_add_vcard",
        annotations={
            "title": "Add Yandex Direct VCard",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_add_vcard(params: AddVCardInput) -> str:
        """Create a new vCard.

        VCards display business contact info in ads.
        Phone format: +7-495-123-45-67
        """
        try:
            phone_obj = {
                "CountryCode": params.country_code,
                "CityCode": params.city_code,
                "PhoneNumber": params.phone_number
            }
            if params.phone_extension:
                phone_obj["Extension"] = params.phone_extension

            vcard = {
                "CampaignId": params.campaign_id,
                "CompanyName": params.company,
                "Phone": phone_obj,
                "Country": params.country,
                "City": params.city
            }

            if params.street:
                vcard["Street"] = params.street
            if params.house:
                vcard["House"] = params.house
            if params.work_time:
                vcard["WorkTime"] = params.work_time
            if params.extra_message:
                vcard["ExtraMessage"] = params.extra_message

            request_params = {
                "VCards": [vcard]
            }

            result = await api_client.direct_request("vcards", "add", request_params, account=params.account)
            add_results = result.get("result", {}).get("AddResults", [])

            if add_results and add_results[0].get("Id"):
                return f"VCard created successfully. ID: {add_results[0]['Id']}"

            errors = []
            for r in add_results:
                if r.get("Errors"):
                    errors.extend([f"{e.get('Code', '?')}: {e.get('Message', 'Unknown error')} (Details: {e.get('Details', 'N/A')})" for e in r["Errors"]])

            if errors:
                return f"Failed to create vCard:\n" + "\n".join(f"- {e}" for e in errors)

            return f"Failed to create vCard. Full response: {result}"

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_delete_vcards",
        annotations={
            "title": "Delete Yandex Direct VCards",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_delete_vcards(params: DeleteVCardsInput) -> str:
        """Delete vCards."""
        try:
            request_params = {
                "SelectionCriteria": {"Ids": params.vcard_ids}
            }

            result = await api_client.direct_request("vcards", "delete", request_params, account=params.account)
            delete_results = result.get("result", {}).get("DeleteResults", [])

            success = [r["Id"] for r in delete_results if r.get("Id") and not r.get("Errors")]
            errors = []
            for r in delete_results:
                if r.get("Errors"):
                    errors.extend([f"ID {r.get('Id', '?')}: {e.get('Message', 'Unknown error')}" for e in r["Errors"]])

            response = f"Successfully deleted {len(success)} vCard(s)."
            if errors:
                response += f"\n\nErrors:\n" + "\n".join(f"- {e}" for e in errors)

            return response

        except Exception as e:
            return handle_api_error(e)
