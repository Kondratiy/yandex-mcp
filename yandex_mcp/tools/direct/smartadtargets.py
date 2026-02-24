"""Yandex Direct smart ad targets (filters) tools."""

import json
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

from ...client import api_client
from ...utils import handle_api_error
from ._helpers import register_manage_tool


class SmartAdTargetCondition(BaseModel):
    """A single filter condition."""
    operand: str = Field(..., description="Feed field name (e.g., 'price', 'manufacturer', 'category_id', 'url', 'title')")
    operator: str = Field(..., description="Operator: EQUALS_ANY, CONTAINS_ANY, NOT_CONTAINS_ALL, GREATER_THAN, LESS_THAN, IN_RANGE, EXISTS")
    arguments: List[str] = Field(..., description="Values to match (max 50). For IN_RANGE use 'min-max' format.")


class AddSmartAdTargetInput(BaseModel):
    """Input for adding a smart ad target (filter)."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    adgroup_id: int = Field(..., description="Smart ad group ID")
    name: str = Field(..., max_length=255, description="Filter name")
    available_items_only: bool = Field(default=True, description="Show only available items (YES) or all (NO)")
    conditions: Optional[List[SmartAdTargetCondition]] = Field(
        default=None,
        description="Filter conditions. If empty, all feed items are used."
    )


class GetSmartAdTargetsInput(BaseModel):
    """Input for getting smart ad targets."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    campaign_ids: Optional[List[int]] = Field(default=None, description="Filter by campaign IDs")
    adgroup_ids: Optional[List[int]] = Field(default=None, description="Filter by ad group IDs")
    target_ids: Optional[List[int]] = Field(default=None, description="Filter by target IDs")
    limit: int = Field(default=100, ge=1, le=10000)


class ManageSmartAdTargetsInput(BaseModel):
    """Input for managing smart ad targets."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    target_ids: List[int] = Field(..., min_length=1, description="Smart ad target IDs")


def register(mcp: FastMCP) -> None:
    """Register smart ad target tools."""

    @mcp.tool(
        name="direct_add_smart_ad_target",
        annotations={
            "title": "Add Smart Ad Target (Filter)",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_add_smart_ad_target(params: AddSmartAdTargetInput) -> str:
        """Add a targeting filter to a smart ad group.

        Defines which product offers from the feed are used to generate smart banners.
        Without conditions, ALL feed items are used.
        With conditions, only matching items are shown (max 10 rules per filter).
        """
        try:
            target = {
                "AdGroupId": params.adgroup_id,
                "Name": params.name,
                "AvailableItemsOnly": "YES" if params.available_items_only else "NO"
            }

            if params.conditions:
                target["Conditions"] = [
                    {
                        "Operand": c.operand,
                        "Operator": c.operator,
                        "Arguments": c.arguments
                    }
                    for c in params.conditions
                ]

            request_params = {"SmartAdTargets": [target]}

            result = await api_client.direct_request("smartadtargets", "add", request_params)

            if "error" in result:
                err = result["error"]
                return f"API Error: {err.get('error_code')}: {err.get('error_string')} | {err.get('error_detail', '')}"

            add_results = result.get("result", {}).get("AddResults", [])

            if add_results and add_results[0].get("Id"):
                target_id = add_results[0]["Id"]
                return f"Smart ad target created successfully!\nTarget ID: {target_id}\nName: {params.name}\nGroup: {params.adgroup_id}"

            errors = []
            for r in add_results:
                if r.get("Errors"):
                    errors.extend([f"{e.get('Code')}: {e.get('Message')} | {e.get('Details', '')}" for e in r["Errors"]])

            return f"Failed to create smart ad target:\n" + "\n".join(f"- {e}" for e in errors)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_get_smart_ad_targets",
        annotations={
            "title": "Get Smart Ad Targets",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_smart_ad_targets(params: GetSmartAdTargetsInput) -> str:
        """Get smart ad targets (filters) and their conditions."""
        try:
            selection_criteria = {}
            if params.campaign_ids:
                selection_criteria["CampaignIds"] = params.campaign_ids
            if params.adgroup_ids:
                selection_criteria["AdGroupIds"] = params.adgroup_ids
            if params.target_ids:
                selection_criteria["Ids"] = params.target_ids

            request_params = {
                "SelectionCriteria": selection_criteria,
                "FieldNames": ["Id", "AdGroupId", "CampaignId", "Name", "State", "Status", "AvailableItemsOnly"],
                "Page": {"Limit": params.limit}
            }

            result = await api_client.direct_request("smartadtargets", "get", request_params)

            if "error" in result:
                err = result["error"]
                return f"API Error: {err.get('error_code')}: {err.get('error_string')} | {err.get('error_detail', '')}"

            targets = result.get("result", {}).get("SmartAdTargets", [])

            if not targets:
                return "No smart ad targets found."

            lines = ["# Smart Ad Targets\n"]
            for t in targets:
                lines.append(f"## {t.get('Name', 'N/A')} (ID: {t.get('Id')})")
                lines.append(f"- **AdGroup**: {t.get('AdGroupId')}")
                lines.append(f"- **Campaign**: {t.get('CampaignId')}")
                lines.append(f"- **State**: {t.get('State')}")
                lines.append(f"- **Status**: {t.get('Status')}")
                lines.append(f"- **Available Only**: {t.get('AvailableItemsOnly')}")
                conditions = t.get("Conditions", [])
                if conditions:
                    lines.append("- **Conditions**:")
                    for c in conditions:
                        lines.append(f"  - {c.get('Operand')} {c.get('Operator')} {c.get('Arguments')}")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    for action in ("suspend", "resume", "delete"):
        register_manage_tool(
            mcp,
            service="smartadtargets",
            action=action,
            entity="smart ad target",
            input_model=ManageSmartAdTargetsInput,
            ids_field="target_ids",
            tool_name=f"direct_{action}_smart_ad_targets",
            tool_title=f"{action.capitalize()} Smart Ad Targets",
        )
