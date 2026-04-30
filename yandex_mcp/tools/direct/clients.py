"""Yandex Direct clients and changes tools."""

import json
from typing import Optional

from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...models.common import ResponseFormat
from ...models.direct_extended import (
    GetClientInfoInput,
    CheckCampaignChangesInput,
    CheckAllChangesInput,
)
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register client and changes tools."""

    # =========================================================================
    # Clients
    # =========================================================================

    @mcp.tool(
        name="direct_get_client_info",
        annotations={
            "title": "Get Yandex Direct Client Info",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_client_info(params: GetClientInfoInput) -> str:
        """Get information about the current client/account.

        Returns account settings, limits, and permissions.
        """
        try:
            request_params = {
                "FieldNames": [
                    "AccountQuality", "Archived", "ClientId", "ClientInfo",
                    "CountryId", "CreatedAt", "Currency", "Grants",
                    "Login", "Notification", "OverdraftSumAvailable",
                    "Phone", "Representatives", "Restrictions",
                    "Settings", "Type", "VatRate"
                ]
            }

            result = await api_client.direct_request("clients", "get", request_params, account=params.account)
            clients = result.get("result", {}).get("Clients", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"clients": clients}, indent=2, ensure_ascii=False)

            if not clients:
                return "No client information found."

            client = clients[0]
            lines = ["# Client Information\n"]

            lines.append(f"## {client.get('Login', 'Unknown')}")
            lines.append(f"- **Client ID**: {client.get('ClientId', 'N/A')}")
            lines.append(f"- **Type**: {client.get('Type', 'N/A')}")
            lines.append(f"- **Currency**: {client.get('Currency', 'N/A')}")
            lines.append(f"- **Country ID**: {client.get('CountryId', 'N/A')}")
            lines.append(f"- **Created At**: {client.get('CreatedAt', 'N/A')}")
            lines.append(f"- **Phone**: {client.get('Phone', 'N/A')}")
            lines.append(f"- **VAT Rate**: {client.get('VatRate', 'N/A')}%")
            lines.append(f"- **Account Quality**: {client.get('AccountQuality', 'N/A')}")
            lines.append(f"- **Archived**: {client.get('Archived', 'N/A')}")

            if client.get('OverdraftSumAvailable'):
                lines.append(f"- **Overdraft Available**: {client['OverdraftSumAvailable'] / 1_000_000:.2f}")

            if client.get('ClientInfo'):
                lines.append(f"- **Client Info**: {client['ClientInfo']}")

            # Settings
            settings = client.get('Settings', [])
            if settings:
                lines.append("\n### Settings")
                for s in settings:
                    lines.append(f"- **{s.get('Option')}**: {s.get('Value')}")

            # Restrictions
            restrictions = client.get('Restrictions', [])
            if restrictions:
                lines.append("\n### Restrictions")
                for r in restrictions:
                    lines.append(f"- **{r.get('Element')}**: {r.get('Value')}")

            # Grants
            grants = client.get('Grants', [])
            if grants:
                lines.append("\n### Grants (Permissions)")
                for g in grants:
                    lines.append(f"- **{g.get('Privilege')}**: {g.get('Value')}")

            # Representatives
            reps = client.get('Representatives', [])
            if reps:
                lines.append("\n### Representatives")
                for rep in reps:
                    lines.append(f"- {rep.get('Login')} ({rep.get('Role')}): {rep.get('Email')}")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    # =========================================================================
    # Changes
    # =========================================================================

    @mcp.tool(
        name="direct_check_campaign_changes",
        annotations={
            "title": "Check Yandex Direct Campaign Changes",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_check_campaign_changes(params: CheckCampaignChangesInput) -> str:
        """Check if campaigns have changed since a given timestamp.

        Useful for incremental sync - only fetch campaigns that changed.
        Returns campaign IDs that were modified.
        """
        try:
            request_params = {
                "CampaignIds": params.campaign_ids,
                "Timestamp": params.timestamp
            }

            result = await api_client.direct_request("changes", "checkCampaigns", request_params, account=params.account)
            data = result.get("result", {})

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(data, indent=2, ensure_ascii=False)

            modified = data.get("ModifiedCampaignIds", [])
            not_found = data.get("NotFoundCampaignIds", [])

            lines = ["# Campaign Changes Check\n"]
            lines.append(f"**Timestamp**: {params.timestamp}")
            lines.append(f"**Server Timestamp**: {data.get('Timestamp', 'N/A')}")
            lines.append("")

            if modified:
                lines.append(f"## Modified Campaigns ({len(modified)})")
                for cid in modified:
                    lines.append(f"- Campaign {cid}")
                lines.append("")

            if not_found:
                lines.append(f"## Not Found ({len(not_found)})")
                for cid in not_found:
                    lines.append(f"- Campaign {cid}")
                lines.append("")

            unchanged = set(params.campaign_ids) - set(modified) - set(not_found)
            if unchanged:
                lines.append(f"## Unchanged ({len(unchanged)})")
                for cid in unchanged:
                    lines.append(f"- Campaign {cid}")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_check_all_changes",
        annotations={
            "title": "Check All Yandex Direct Changes",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_check_all_changes(params: CheckAllChangesInput) -> str:
        """Check all changes in the account since a timestamp.

        Returns IDs of modified campaigns, ad groups, and ads.
        Useful for full account sync.
        """
        try:
            request_params = {
                "Timestamp": params.timestamp,
                "FieldNames": [
                    "CampaignIds", "AdGroupIds", "AdIds",
                    "KeywordIds", "DynamicTextAdTargetIds"
                ]
            }

            result = await api_client.direct_request("changes", "check", request_params, account=params.account)
            data = result.get("result", {})

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(data, indent=2, ensure_ascii=False)

            lines = ["# Account Changes Check\n"]
            lines.append(f"**From Timestamp**: {params.timestamp}")
            lines.append(f"**Server Timestamp**: {data.get('Timestamp', 'N/A')}")
            lines.append("")

            modified = data.get("Modified", {})

            campaigns = modified.get("CampaignIds", [])
            if campaigns:
                lines.append(f"## Modified Campaigns ({len(campaigns)})")
                for cid in campaigns[:20]:
                    lines.append(f"- {cid}")
                if len(campaigns) > 20:
                    lines.append(f"... and {len(campaigns) - 20} more")
                lines.append("")

            adgroups = modified.get("AdGroupIds", [])
            if adgroups:
                lines.append(f"## Modified Ad Groups ({len(adgroups)})")
                for gid in adgroups[:20]:
                    lines.append(f"- {gid}")
                if len(adgroups) > 20:
                    lines.append(f"... and {len(adgroups) - 20} more")
                lines.append("")

            ads = modified.get("AdIds", [])
            if ads:
                lines.append(f"## Modified Ads ({len(ads)})")
                for aid in ads[:20]:
                    lines.append(f"- {aid}")
                if len(ads) > 20:
                    lines.append(f"... and {len(ads) - 20} more")
                lines.append("")

            keywords = modified.get("KeywordIds", [])
            if keywords:
                lines.append(f"## Modified Keywords ({len(keywords)})")
                for kid in keywords[:20]:
                    lines.append(f"- {kid}")
                if len(keywords) > 20:
                    lines.append(f"... and {len(keywords) - 20} more")
                lines.append("")

            if not any([campaigns, adgroups, ads, keywords]):
                lines.append("No changes detected since the given timestamp.")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_get_recent_changes_timestamp",
        annotations={
            "title": "Get Yandex Direct Current Timestamp",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_recent_changes_timestamp(account: Optional[str] = None) -> str:
        """Get the current Yandex Direct server timestamp for change tracking.

        Returns the server timestamp from `changes.checkDictionaries` — the
        only method in the `changes` namespace that returns a Timestamp
        without requiring CampaignIds/AdGroupIds/AdIds inputs. Store this
        value and pass it as the starting point to direct_check_all_changes
        or direct_check_campaign_changes for incremental sync.
        """
        try:
            # changes.check / checkCampaigns require CampaignIds (or sibling
            # arrays) and refuse with error 4003 if absent — they cannot be
            # used as a "give me current timestamp" endpoint. checkDictionaries
            # has no required parameters and returns a server-side Timestamp
            # in the same ISO8601 format that check/checkCampaigns expect.
            result = await api_client.direct_request(
                "changes", "checkDictionaries", {}, account=account
            )

            if "error" in result:
                err = result["error"]
                return f"API Error: {err.get('error_code')}: {err.get('error_string')} | {err.get('error_detail', '')}"

            timestamp = result.get("result", {}).get("Timestamp", "")
            if not timestamp:
                return "API returned no timestamp."

            return (
                f"Current server timestamp: {timestamp}\n\n"
                "Store this timestamp and pass it to direct_check_all_changes "
                "or direct_check_campaign_changes to track what changed since."
            )

        except Exception as e:
            return handle_api_error(e)
