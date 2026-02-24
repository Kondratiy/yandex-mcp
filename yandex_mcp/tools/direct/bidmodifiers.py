"""Yandex Direct bid modifiers tools."""

import json
from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...models.common import ResponseFormat
from ...models.direct_extended import (
    GetBidModifiersInput,
    AddBidModifierInput,
    SetBidModifierInput,
    DeleteBidModifiersInput,
    ToggleBidModifiersInput,
)
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register bid modifier tools."""

    @mcp.tool(
        name="direct_get_bid_modifiers",
        annotations={
            "title": "Get Yandex Direct Bid Modifiers",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_bid_modifiers(params: GetBidModifiersInput) -> str:
        """Get bid modifiers from Yandex Direct.

        Bid modifiers adjust bids based on:
        - Device type (mobile/desktop)
        - Demographics (age, gender)
        - Geography (regions)
        - Retargeting lists
        - Video additions
        """
        try:
            selection_criteria = {}

            if params.campaign_ids:
                selection_criteria["CampaignIds"] = params.campaign_ids
            if params.adgroup_ids:
                selection_criteria["AdGroupIds"] = params.adgroup_ids
            if params.bid_modifier_ids:
                selection_criteria["Ids"] = params.bid_modifier_ids
            if params.types:
                selection_criteria["Types"] = params.types

            # Levels is REQUIRED — without it API returns empty results silently
            levels = []
            if params.campaign_ids:
                levels.append("CAMPAIGN")
            if params.adgroup_ids:
                levels.append("AD_GROUP")
            if not levels:
                levels = ["CAMPAIGN", "AD_GROUP"]
            selection_criteria["Levels"] = levels

            request_params = {
                "SelectionCriteria": selection_criteria,
                "FieldNames": ["Id", "CampaignId", "AdGroupId", "Type", "Level"],
                "MobileAdjustmentFieldNames": ["BidModifier"],
                "DesktopAdjustmentFieldNames": ["BidModifier"],
                "DemographicsAdjustmentFieldNames": ["Gender", "Age", "BidModifier", "Enabled"],
                "RegionalAdjustmentFieldNames": ["RegionId", "BidModifier", "Enabled"],
                "Page": {"Limit": params.limit}
            }

            result = await api_client.direct_request("bidmodifiers", "get", request_params)
            bid_modifiers = result.get("result", {}).get("BidModifiers", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"bid_modifiers": bid_modifiers, "total": len(bid_modifiers)}, indent=2, ensure_ascii=False)

            if not bid_modifiers:
                return "No bid modifiers found."

            lines = ["# Bid Modifiers\n"]
            for bm in bid_modifiers:
                lines.append(f"## ID: {bm.get('Id')} ({bm.get('Type', 'N/A')})")
                lines.append(f"- **Level**: {bm.get('Level', 'N/A')}")
                lines.append(f"- **Campaign ID**: {bm.get('CampaignId', 'N/A')}")
                if bm.get('AdGroupId'):
                    lines.append(f"- **Ad Group ID**: {bm.get('AdGroupId')}")

                if bm.get('MobileAdjustment'):
                    lines.append(f"- **Mobile**: {bm['MobileAdjustment'].get('BidModifier', 0)}%")
                if bm.get('DesktopAdjustment'):
                    lines.append(f"- **Desktop**: {bm['DesktopAdjustment'].get('BidModifier', 0)}%")
                if bm.get('DemographicsAdjustment'):
                    da = bm['DemographicsAdjustment']
                    lines.append(f"- **Demographics**: {da.get('Gender', '')} {da.get('Age', '')} → {da.get('BidModifier', 0)}%")
                if bm.get('RegionalAdjustment'):
                    ra = bm['RegionalAdjustment']
                    lines.append(f"- **Region {ra.get('RegionId')}**: {ra.get('BidModifier', 0)}%")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_add_bid_modifier",
        annotations={
            "title": "Add Yandex Direct Bid Modifier",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_add_bid_modifier(params: AddBidModifierInput) -> str:
        """Add a bid modifier.

        Bid modifier values:
        - 0 = disable (no impressions)
        - 50 = decrease bid by 50%
        - 100 = no change
        - 150 = increase bid by 50%
        - 1300 = maximum (13x increase)
        """
        try:
            bid_modifier = {}

            if params.campaign_id:
                bid_modifier["CampaignId"] = params.campaign_id
            if params.adgroup_id:
                bid_modifier["AdGroupId"] = params.adgroup_id

            if params.mobile_adjustment:
                bid_modifier["MobileAdjustment"] = {
                    "BidModifier": params.mobile_adjustment.bid_modifier
                }
            if params.desktop_adjustment:
                bid_modifier["DesktopAdjustment"] = {
                    "BidModifier": params.desktop_adjustment.bid_modifier
                }
            if params.demographics_adjustments:
                demo_list = []
                for da in params.demographics_adjustments:
                    demo_item = {"BidModifier": da.bid_modifier}
                    if da.gender:
                        demo_item["Gender"] = da.gender
                    if da.age:
                        demo_item["Age"] = da.age
                    demo_list.append(demo_item)
                bid_modifier["DemographicsAdjustments"] = demo_list
            if params.regional_adjustments:
                bid_modifier["RegionalAdjustments"] = [
                    {
                        "RegionId": ra.region_id,
                        "BidModifier": ra.bid_modifier
                    } for ra in params.regional_adjustments
                ]

            request_params = {
                "BidModifiers": [bid_modifier]
            }

            result = await api_client.direct_request("bidmodifiers", "add", request_params)
            add_results = result.get("result", {}).get("AddResults", [])

            if add_results and (add_results[0].get("Id") or add_results[0].get("Ids")):
                ids = add_results[0].get("Ids") or [add_results[0].get("Id")]
                return f"Bid modifier added successfully. IDs: {', '.join(str(i) for i in ids)}"

            errors = []
            for r in add_results:
                if r.get("Errors"):
                    errors.extend([f"{e.get('Code', '?')}: {e.get('Message', 'Unknown')} | {e.get('Details', '')}" for e in r["Errors"]])

            if errors:
                return f"Failed to add bid modifier:\n" + "\n".join(f"- {e}" for e in errors)

            return f"Failed to add bid modifier. Response: {result}"

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_set_bid_modifier",
        annotations={
            "title": "Set Yandex Direct Bid Modifier Value",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_set_bid_modifier(params: SetBidModifierInput) -> str:
        """Set bid modifier value."""
        try:
            request_params = {
                "BidModifiers": [{
                    "Id": params.bid_modifier_id,
                    "BidModifier": params.bid_modifier
                }]
            }

            result = await api_client.direct_request("bidmodifiers", "set", request_params)
            set_results = result.get("result", {}).get("SetResults", [])

            success = [r["Id"] for r in set_results if r.get("Id") and not r.get("Errors")]

            if success:
                return f"Bid modifier {params.bid_modifier_id} set to {params.bid_modifier}%."

            errors = []
            for r in set_results:
                if r.get("Errors"):
                    errors.extend([e.get("Message", "Unknown error") for e in r["Errors"]])

            return f"Failed to set bid modifier:\n" + "\n".join(f"- {e}" for e in errors)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_delete_bid_modifiers",
        annotations={
            "title": "Delete Yandex Direct Bid Modifiers",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_delete_bid_modifiers(params: DeleteBidModifiersInput) -> str:
        """Delete bid modifiers."""
        try:
            request_params = {
                "SelectionCriteria": {"Ids": params.bid_modifier_ids}
            }

            result = await api_client.direct_request("bidmodifiers", "delete", request_params)
            delete_results = result.get("result", {}).get("DeleteResults", [])

            success = [r["Id"] for r in delete_results if r.get("Id") and not r.get("Errors")]

            return f"Successfully deleted {len(success)} bid modifier(s)."

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_toggle_bid_modifiers",
        annotations={
            "title": "Toggle Yandex Direct Bid Modifiers",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_toggle_bid_modifiers(params: ToggleBidModifiersInput) -> str:
        """Enable or disable bid modifiers."""
        try:
            request_params = {
                "BidModifierToggleItems": [
                    {"BidModifierId": bm_id, "Enabled": "YES" if params.enabled else "NO"}
                    for bm_id in params.bid_modifier_ids
                ]
            }

            result = await api_client.direct_request("bidmodifiers", "toggle", request_params)
            toggle_results = result.get("result", {}).get("ToggleResults", [])

            success = len([r for r in toggle_results if not r.get("Errors")])
            action = "enabled" if params.enabled else "disabled"

            return f"Successfully {action} {success} bid modifier(s)."

        except Exception as e:
            return handle_api_error(e)
