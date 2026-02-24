"""Yandex Metrika goal tools."""

import json
from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...models.common import ResponseFormat
from ...models.metrika import (
    GetGoalsInput,
    CreateGoalInput,
    UpdateGoalInput,
    DeleteGoalInput,
)
from ...formatters.metrika import format_metrika_goals_markdown
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register goal tools."""

    @mcp.tool(
        name="metrika_get_goals",
        annotations={
            "title": "Get Yandex Metrika Goals",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_get_goals(params: GetGoalsInput) -> str:
        """Get goals for a Metrika counter.

        Retrieves all configured goals for tracking conversions.
        """
        try:
            result = await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}/goals"
            )

            goals = result.get("goals", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"goals": goals, "total": len(goals)}, indent=2, ensure_ascii=False)

            return format_metrika_goals_markdown(goals, params.counter_id)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_create_goal",
        annotations={
            "title": "Create Yandex Metrika Goal",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def metrika_create_goal(params: CreateGoalInput) -> str:
        """Create a new goal for a Metrika counter.

        Goals track conversions like page visits, form submissions, clicks, etc.

        Goal types:
        - url: Track page visits by URL
        - action: Track JavaScript events (reachGoal)
        - phone: Track phone number clicks
        - email: Track email clicks
        - messenger: Track messenger button clicks
        - form: Track form submissions
        - button: Track button clicks
        """
        try:
            data = {
                "goal": {
                    "name": params.name,
                    "type": params.goal_type,
                    "conditions": params.conditions
                }
            }

            result = await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}/goals",
                method="POST",
                data=data
            )

            goal = result.get("goal", {})

            return f"""Goal created successfully!

**ID**: {goal.get('id')}
**Name**: {goal.get('name')}
**Type**: {goal.get('type')}

Use goal ID {goal.get('id')} for tracking conversions in Yandex Direct."""

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_update_goal",
        annotations={
            "title": "Update Yandex Metrika Goal",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_update_goal(params: UpdateGoalInput) -> str:
        """Update an existing goal.

        Allows updating goal name and conditions.
        """
        try:
            goal_update = {}

            if params.name:
                goal_update["name"] = params.name
            if params.conditions:
                goal_update["conditions"] = params.conditions

            if not goal_update:
                return "No fields specified for update."

            data = {"goal": goal_update}

            await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}/goal/{params.goal_id}",
                method="PUT",
                data=data
            )

            return f"Goal {params.goal_id} updated successfully."

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_delete_goal",
        annotations={
            "title": "Delete Yandex Metrika Goal",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_delete_goal(params: DeleteGoalInput) -> str:
        """Delete a goal from a Metrika counter.

        WARNING: Historical conversion data for this goal will be lost.
        """
        try:
            await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}/goal/{params.goal_id}",
                method="DELETE"
            )

            return f"Goal {params.goal_id} deleted successfully."

        except Exception as e:
            return handle_api_error(e)
