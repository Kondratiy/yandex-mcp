"""Yandex Metrika access grant tools (NEW)."""

import json
from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...models.common import ResponseFormat
from ...models.metrika import (
    GetGrantsInput,
    GrantInput,
    DeleteGrantInput,
)
from ...formatters.metrika import format_metrika_grants_markdown
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register grant (access) tools."""

    @mcp.tool(
        name="metrika_get_grants",
        annotations={
            "title": "Get Yandex Metrika Access Grants",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_get_grants(params: GetGrantsInput) -> str:
        """Get access grants for a Metrika counter.

        Shows all users who have access to this counter.
        """
        try:
            result = await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}/grants"
            )

            grants = result.get("grants", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"grants": grants, "total": len(grants)}, indent=2, ensure_ascii=False)

            return format_metrika_grants_markdown(grants, params.counter_id)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_add_grant",
        annotations={
            "title": "Add Yandex Metrika Access Grant",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_add_grant(params: GrantInput) -> str:
        """Grant access to a Metrika counter for another user.

        Permission levels:
        - view: Read-only access to statistics
        - edit: Can edit counter settings and goals
        """
        try:
            data = {
                "grant": {
                    "user_login": params.user_login,
                    "perm": params.permission.value
                }
            }

            if params.comment:
                data["grant"]["comment"] = params.comment

            result = await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}/grants",
                method="POST",
                data=data
            )

            grant = result.get("grant", {})

            return f"""Access granted successfully!

**User**: {grant.get('user_login')}
**Permission**: {grant.get('perm')}
**Counter**: {params.counter_id}"""

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_update_grant",
        annotations={
            "title": "Update Yandex Metrika Access Grant",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_update_grant(params: GrantInput) -> str:
        """Update access grant for a user.

        Changes permission level or comment.
        """
        try:
            data = {
                "grant": {
                    "perm": params.permission.value
                }
            }

            if params.comment:
                data["grant"]["comment"] = params.comment

            await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}/grant/{params.user_login}",
                method="PUT",
                data=data
            )

            return f"Access grant for {params.user_login} updated successfully."

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_delete_grant",
        annotations={
            "title": "Delete Yandex Metrika Access Grant",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_delete_grant(params: DeleteGrantInput) -> str:
        """Revoke access to a Metrika counter for a user."""
        try:
            await api_client.metrika_request(
                f"/management/v1/counter/{params.counter_id}/grant/{params.user_login}",
                method="DELETE"
            )

            return f"Access for {params.user_login} revoked successfully."

        except Exception as e:
            return handle_api_error(e)
