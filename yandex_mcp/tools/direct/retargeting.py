"""Yandex Direct retargeting tools."""

import json
from mcp.server.fastmcp import FastMCP

from ._helpers import register_manage_tool
from ...client import api_client
from ...models.common import ResponseFormat
from ...models.direct_extended import (
    GetRetargetingListsInput,
    AddRetargetingListInput,
    UpdateRetargetingListInput,
    DeleteRetargetingListsInput,
    GetAudienceTargetsInput,
    AddAudienceTargetInput,
    ManageAudienceTargetsInput,
)
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register retargeting tools."""

    # =========================================================================
    # Retargeting Lists
    # =========================================================================

    @mcp.tool(
        name="direct_get_retargeting_lists",
        annotations={
            "title": "Get Yandex Direct Retargeting Lists",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_retargeting_lists(params: GetRetargetingListsInput) -> str:
        """Get retargeting lists from Yandex Direct.

        Retargeting lists define audiences based on Metrika goals.
        """
        try:
            selection_criteria = {}

            if params.retargeting_list_ids:
                selection_criteria["Ids"] = params.retargeting_list_ids

            request_params = {
                "SelectionCriteria": selection_criteria,
                "FieldNames": ["Id", "Name", "Type", "Description", "IsAvailable"],
                "Page": {"Limit": params.limit}
            }

            result = await api_client.direct_request("retargetinglists", "get", request_params)
            lists = result.get("result", {}).get("RetargetingLists", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"retargeting_lists": lists, "total": len(lists)}, indent=2, ensure_ascii=False)

            if not lists:
                return "No retargeting lists found."

            lines = ["# Retargeting Lists\n"]
            for rl in lists:
                lines.append(f"## {rl.get('Name', 'Unnamed')} (ID: {rl.get('Id')})")
                lines.append(f"- **Type**: {rl.get('Type', 'N/A')}")
                lines.append(f"- **Available**: {rl.get('IsAvailable', 'N/A')}")
                if rl.get('Description'):
                    lines.append(f"- **Description**: {rl['Description']}")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_add_retargeting_list",
        annotations={
            "title": "Add Yandex Direct Retargeting List",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_add_retargeting_list(params: AddRetargetingListInput) -> str:
        """Create a new retargeting list.

        Rules are grouped: OR between groups, AND within each group.
        Each rule references a Metrika goal ID.
        """
        try:
            rules_data = []
            for rule_group in params.rules:
                group_items = []
                for rule in rule_group:
                    group_items.append({
                        "GoalId": rule.goal_id,
                        "MemberOf": rule.member_of,
                        "Days": rule.days
                    })
                rules_data.append({"Items": group_items})

            retargeting_list = {
                "Name": params.name,
                "Rules": rules_data
            }

            if params.description:
                retargeting_list["Description"] = params.description

            request_params = {
                "RetargetingLists": [retargeting_list]
            }

            result = await api_client.direct_request("retargetinglists", "add", request_params)
            add_results = result.get("result", {}).get("AddResults", [])

            if add_results and add_results[0].get("Id"):
                return f"Retargeting list created successfully. ID: {add_results[0]['Id']}"

            errors = []
            for r in add_results:
                if r.get("Errors"):
                    errors.extend([e.get("Message", "Unknown error") for e in r["Errors"]])

            return f"Failed to create retargeting list:\n" + "\n".join(f"- {e}" for e in errors)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_update_retargeting_list",
        annotations={
            "title": "Update Yandex Direct Retargeting List",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_update_retargeting_list(params: UpdateRetargetingListInput) -> str:
        """Update a retargeting list."""
        try:
            retargeting_list = {"Id": params.retargeting_list_id}

            if params.name:
                retargeting_list["Name"] = params.name
            if params.description:
                retargeting_list["Description"] = params.description
            if params.rules:
                rules_data = []
                for rule_group in params.rules:
                    group_items = []
                    for rule in rule_group:
                        group_items.append({
                            "GoalId": rule.goal_id,
                            "MemberOf": rule.member_of,
                            "Days": rule.days
                        })
                    rules_data.append({"Items": group_items})
                retargeting_list["Rules"] = rules_data

            request_params = {
                "RetargetingLists": [retargeting_list]
            }

            result = await api_client.direct_request("retargetinglists", "update", request_params)
            update_results = result.get("result", {}).get("UpdateResults", [])

            errors = []
            for r in update_results:
                if r.get("Errors"):
                    errors.extend([e.get("Message", "Unknown error") for e in r["Errors"]])

            if errors:
                return f"Update completed with issues:\n" + "\n".join(f"- {e}" for e in errors)

            return f"Retargeting list {params.retargeting_list_id} updated successfully."

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_delete_retargeting_lists",
        annotations={
            "title": "Delete Yandex Direct Retargeting Lists",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_delete_retargeting_lists(params: DeleteRetargetingListsInput) -> str:
        """Delete retargeting lists."""
        try:
            request_params = {
                "SelectionCriteria": {"Ids": params.retargeting_list_ids}
            }

            result = await api_client.direct_request("retargetinglists", "delete", request_params)
            delete_results = result.get("result", {}).get("DeleteResults", [])

            success = [r["Id"] for r in delete_results if r.get("Id") and not r.get("Errors")]

            return f"Successfully deleted {len(success)} retargeting list(s)."

        except Exception as e:
            return handle_api_error(e)

    # =========================================================================
    # Audience Targets
    # =========================================================================

    @mcp.tool(
        name="direct_get_audience_targets",
        annotations={
            "title": "Get Yandex Direct Audience Targets",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_audience_targets(params: GetAudienceTargetsInput) -> str:
        """Get audience targets from Yandex Direct.

        Audience targets link retargeting lists to ad groups.
        """
        try:
            selection_criteria = {}

            if params.campaign_ids:
                selection_criteria["CampaignIds"] = params.campaign_ids
            if params.adgroup_ids:
                selection_criteria["AdGroupIds"] = params.adgroup_ids
            if params.audience_target_ids:
                selection_criteria["Ids"] = params.audience_target_ids

            request_params = {
                "SelectionCriteria": selection_criteria,
                "FieldNames": ["Id", "AdGroupId", "CampaignId", "RetargetingListId", "InterestId", "State", "ContextBid"],
                "Page": {"Limit": params.limit}
            }

            result = await api_client.direct_request("audiencetargets", "get", request_params)
            targets = result.get("result", {}).get("AudienceTargets", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"audience_targets": targets, "total": len(targets)}, indent=2, ensure_ascii=False)

            if not targets:
                return "No audience targets found."

            lines = ["# Audience Targets\n"]
            for at in targets:
                lines.append(f"## ID: {at.get('Id')}")
                lines.append(f"- **Ad Group ID**: {at.get('AdGroupId')}")
                lines.append(f"- **Campaign ID**: {at.get('CampaignId')}")
                if at.get('RetargetingListId'):
                    lines.append(f"- **Retargeting List ID**: {at['RetargetingListId']}")
                if at.get('InterestId'):
                    lines.append(f"- **Interest ID**: {at['InterestId']}")
                lines.append(f"- **State**: {at.get('State', 'N/A')}")
                if at.get('ContextBid'):
                    lines.append(f"- **Context Bid**: {at['ContextBid'] / 1_000_000:.2f}")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_add_audience_target",
        annotations={
            "title": "Add Yandex Direct Audience Target",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_add_audience_target(params: AddAudienceTargetInput) -> str:
        """Add an audience target to an ad group."""
        try:
            audience_target = {
                "AdGroupId": params.adgroup_id,
                "RetargetingListId": params.retargeting_list_id
            }

            if params.interest_id:
                audience_target["InterestId"] = params.interest_id
            if params.context_bid:
                audience_target["ContextBid"] = int(params.context_bid * 1_000_000)

            request_params = {
                "AudienceTargets": [audience_target]
            }

            result = await api_client.direct_request("audiencetargets", "add", request_params)
            add_results = result.get("result", {}).get("AddResults", [])

            if add_results and add_results[0].get("Id"):
                return f"Audience target added successfully. ID: {add_results[0]['Id']}"

            errors = []
            for r in add_results:
                if r.get("Errors"):
                    errors.extend([e.get("Message", "Unknown error") for e in r["Errors"]])

            return f"Failed to add audience target:\n" + "\n".join(f"- {e}" for e in errors)

        except Exception as e:
            return handle_api_error(e)

    for action in ("suspend", "resume", "delete"):
        register_manage_tool(
            mcp,
            service="audiencetargets",
            action=action,
            entity="audience target",
            input_model=ManageAudienceTargetsInput,
            ids_field="audience_target_ids",
            tool_name=f"direct_{action}_audience_targets",
        )
