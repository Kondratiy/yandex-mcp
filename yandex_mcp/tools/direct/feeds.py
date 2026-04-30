"""Yandex Direct feeds tools."""

import json
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal

from ...client import api_client
from ...models.common import AccountInput
from ...utils import handle_api_error


class AddFeedInput(AccountInput):
    """Input for adding a feed."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(..., max_length=255, description="Feed name")
    business_type: Literal[
        "RETAIL", "HOTELS", "REALTY", "AUTOMOBILES", "FLIGHTS", "OTHER"
    ] = Field(..., description="Business type: RETAIL, HOTELS, REALTY, AUTOMOBILES, FLIGHTS, OTHER")
    url: str = Field(..., max_length=1024, description="Feed URL (must include protocol)")
    login: Optional[str] = Field(default=None, max_length=255, description="HTTP Basic Auth login")
    password: Optional[str] = Field(default=None, max_length=255, description="HTTP Basic Auth password")
    remove_utm_tags: bool = Field(default=False, description="Remove UTM tags from URLs in feed")


class GetFeedsInput(AccountInput):
    """Input for getting feeds."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    feed_ids: Optional[List[int]] = Field(default=None, description="Filter by feed IDs (max 10000)")
    limit: int = Field(default=100, ge=1, le=10000)


class UpdateFeedInput(AccountInput):
    """Input for updating a feed."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    feed_id: int = Field(..., description="Feed ID to update")
    name: Optional[str] = Field(default=None, max_length=255, description="New feed name")
    url: Optional[str] = Field(default=None, max_length=1024, description="New feed URL")
    login: Optional[str] = Field(default=None, max_length=255, description="New HTTP Basic Auth login")
    password: Optional[str] = Field(default=None, max_length=255, description="New HTTP Basic Auth password")
    remove_utm_tags: Optional[bool] = Field(default=None, description="Remove UTM tags from URLs")


class DeleteFeedsInput(AccountInput):
    """Input for deleting feeds."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    feed_ids: List[int] = Field(..., min_length=1, description="Feed IDs to delete")


def register(mcp: FastMCP) -> None:
    """Register feed tools."""

    @mcp.tool(
        name="direct_add_feed",
        annotations={
            "title": "Add Feed to Yandex Direct",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_add_feed(params: AddFeedInput) -> str:
        """Add a feed (YML/CSV) to Yandex Direct.

        Supports password-protected feeds via HTTP Basic Auth.
        Business types: RETAIL, HOTELS, REALTY, AUTOMOBILES, FLIGHTS, OTHER.
        Max 50 feeds per advertiser.
        """
        try:
            url_feed = {"Url": params.url}
            if params.login:
                url_feed["Login"] = params.login
            if params.password:
                url_feed["Password"] = params.password
            if params.remove_utm_tags:
                url_feed["RemoveUtmTags"] = "YES"

            feed = {
                "Name": params.name,
                "BusinessType": params.business_type,
                "SourceType": "URL",
                "UrlFeed": url_feed
            }

            request_params = {"Feeds": [feed]}

            result = await api_client.direct_request("feeds", "add", request_params, account=params.account)

            if "error" in result:
                err = result["error"]
                return f"API Error: {err.get('error_code')}: {err.get('error_string')} | {err.get('error_detail', '')}"

            add_results = result.get("result", {}).get("AddResults", [])

            if add_results and add_results[0].get("Id"):
                feed_id = add_results[0]["Id"]
                return f"Feed added successfully!\nFeed ID: {feed_id}\nName: {params.name}\nURL: {params.url}\nType: {params.business_type}\n\nFeed will be processed. Check status with direct_get_feeds."

            errors = []
            for r in add_results:
                if r.get("Errors"):
                    errors.extend([f"{e.get('Code')}: {e.get('Message')} | {e.get('Details', '')}" for e in r["Errors"]])

            return f"Failed to add feed:\n" + "\n".join(f"- {e}" for e in errors)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_get_feeds",
        annotations={
            "title": "Get Feeds from Yandex Direct",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_feeds(params: GetFeedsInput) -> str:
        """Get feeds and their processing status.

        Statuses: NEW, UPDATING, DONE, ERROR.
        Shows feed name, type, URL, number of items, and linked campaigns.
        """
        try:
            # Yandex API: SelectionCriteria itself is optional. To get ALL feeds,
            # omit SelectionCriteria entirely. If we send an empty {} the API
            # treats it as "SelectionCriteria is present but Ids is missing"
            # and rejects with "Отсутствует обязательный параметр Ids".
            request_params = {
                "FieldNames": ["Id", "Name", "BusinessType", "SourceType", "Status", "NumberOfItems", "UpdatedAt", "CampaignIds"],
                "UrlFeedFieldNames": ["Url", "Login", "RemoveUtmTags"],
                "Page": {"Limit": params.limit}
            }
            if params.feed_ids:
                request_params["SelectionCriteria"] = {"Ids": params.feed_ids}

            result = await api_client.direct_request("feeds", "get", request_params, account=params.account)

            if "error" in result:
                err = result["error"]
                return f"API Error: {err.get('error_code')}: {err.get('error_string')} | {err.get('error_detail', '')}"

            feeds = result.get("result", {}).get("Feeds", [])

            if not feeds:
                return "No feeds found."

            lines = ["# Feeds\n"]
            for f in feeds:
                lines.append(f"## {f.get('Name', 'N/A')} (ID: {f.get('Id')})")
                lines.append(f"- **Status**: {f.get('Status')}")
                lines.append(f"- **Type**: {f.get('BusinessType')}")
                url_feed = f.get("UrlFeed", {})
                if url_feed:
                    lines.append(f"- **URL**: {url_feed.get('Url', 'N/A')}")
                    if url_feed.get("Login"):
                        lines.append(f"- **Auth**: {url_feed['Login']}")
                items = f.get("NumberOfItems")
                if items is not None:
                    lines.append(f"- **Items**: {items}")
                campaigns = f.get("CampaignIds")
                if campaigns:
                    lines.append(f"- **Campaigns**: {campaigns}")
                updated = f.get("UpdatedAt")
                if updated:
                    lines.append(f"- **Updated**: {updated}")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_update_feed",
        annotations={
            "title": "Update Feed in Yandex Direct",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_update_feed(params: UpdateFeedInput) -> str:
        """Update an existing feed (name, URL, credentials)."""
        try:
            feed_update = {"Id": params.feed_id}

            if params.name:
                feed_update["Name"] = params.name

            url_feed_update = {}
            if params.url:
                url_feed_update["Url"] = params.url
            if params.login:
                url_feed_update["Login"] = params.login
            if params.password:
                url_feed_update["Password"] = params.password
            if params.remove_utm_tags is not None:
                url_feed_update["RemoveUtmTags"] = "YES" if params.remove_utm_tags else "NO"

            if url_feed_update:
                feed_update["UrlFeed"] = url_feed_update

            if len(feed_update) <= 1:
                return "No fields specified for update."

            request_params = {"Feeds": [feed_update]}

            result = await api_client.direct_request("feeds", "update", request_params, account=params.account)

            if "error" in result:
                err = result["error"]
                return f"API Error: {err.get('error_code')}: {err.get('error_string')} | {err.get('error_detail', '')}"

            update_results = result.get("result", {}).get("UpdateResults", [])

            errors = []
            for r in update_results:
                if r.get("Errors"):
                    errors.extend([f"{e.get('Code')}: {e.get('Message')} | {e.get('Details', '')}" for e in r["Errors"]])

            if errors:
                return f"Update failed:\n" + "\n".join(f"- {e}" for e in errors)

            return f"Feed {params.feed_id} updated successfully."

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_delete_feeds",
        annotations={
            "title": "Delete Feeds from Yandex Direct",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_delete_feeds(params: DeleteFeedsInput) -> str:
        """Delete feeds permanently. WARNING: Irreversible."""
        try:
            request_params = {
                "SelectionCriteria": {"Ids": params.feed_ids}
            }

            result = await api_client.direct_request("feeds", "delete", request_params, account=params.account)

            if "error" in result:
                err = result["error"]
                return f"API Error: {err.get('error_code')}: {err.get('error_string')} | {err.get('error_detail', '')}"

            delete_results = result.get("result", {}).get("DeleteResults", [])

            success = [r["Id"] for r in delete_results if r.get("Id") and not r.get("Errors")]
            errors = []
            for r in delete_results:
                if r.get("Errors"):
                    errors.extend([f"ID {r.get('Id', '?')}: {e.get('Message')}" for e in r["Errors"]])

            response = f"Successfully deleted {len(success)} feed(s)."
            if errors:
                response += f"\n\nErrors:\n" + "\n".join(f"- {e}" for e in errors)

            return response

        except Exception as e:
            return handle_api_error(e)
