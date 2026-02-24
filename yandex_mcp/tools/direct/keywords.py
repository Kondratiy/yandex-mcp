"""Yandex Direct keyword tools."""

import json
from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...models.common import ResponseFormat
from ...models.direct import (
    GetKeywordsInput,
    AddKeywordsInput,
    SetKeywordBidsInput,
    ManageKeywordInput,
)
from ...formatters.direct import format_keywords_markdown
from ...utils import handle_api_error
from ._helpers import register_manage_tool


def register(mcp: FastMCP) -> None:
    """Register keyword tools."""

    @mcp.tool(
        name="direct_get_keywords",
        annotations={
            "title": "Get Yandex Direct Keywords",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_keywords(params: GetKeywordsInput) -> str:
        """Get list of keywords from Yandex Direct.

        Retrieves keywords with their bids and status.
        """
        try:
            selection_criteria = {}

            if params.campaign_ids:
                selection_criteria["CampaignIds"] = params.campaign_ids
            if params.adgroup_ids:
                selection_criteria["AdGroupIds"] = params.adgroup_ids
            if params.keyword_ids:
                selection_criteria["Ids"] = params.keyword_ids

            request_params = {
                "SelectionCriteria": selection_criteria,
                "FieldNames": ["Id", "Keyword", "AdGroupId", "State", "Status", "Bid"],
                "Page": {
                    "Limit": params.limit,
                    "Offset": params.offset
                }
            }

            result = await api_client.direct_request("keywords", "get", request_params)
            keywords = result.get("result", {}).get("Keywords", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"keywords": keywords, "total": len(keywords)}, indent=2, ensure_ascii=False)

            return format_keywords_markdown(keywords)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_add_keywords",
        annotations={
            "title": "Add Yandex Direct Keywords",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def direct_add_keywords(params: AddKeywordsInput) -> str:
        """Add keywords to an ad group.

        Creates new keywords with optional bid settings.
        """
        try:
            keywords = []
            for kw in params.keywords:
                keyword_item = {
                    "Keyword": kw,
                    "AdGroupId": params.adgroup_id
                }
                if params.bid:
                    keyword_item["Bid"] = int(params.bid * 1_000_000)
                keywords.append(keyword_item)

            request_params = {
                "Keywords": keywords
            }

            result = await api_client.direct_request("keywords", "add", request_params)
            add_results = result.get("result", {}).get("AddResults", [])

            success = [r["Id"] for r in add_results if r.get("Id") and not r.get("Errors")]
            errors = []
            for r in add_results:
                if r.get("Errors"):
                    errors.extend([e.get("Message", "Unknown error") for e in r["Errors"]])

            response = f"Successfully added {len(success)} keyword(s)."
            if success:
                response += f"\nIDs: {', '.join(map(str, success))}"
            if errors:
                response += f"\n\nErrors:\n" + "\n".join(f"- {e}" for e in errors)

            return response

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_set_keyword_bids",
        annotations={
            "title": "Set Keyword Bids",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_set_keyword_bids(params: SetKeywordBidsInput) -> str:
        """Set bids for keywords.

        Updates search and/or network bids for specified keywords.
        """
        try:
            keyword_bids = []
            for kb in params.keyword_bids:
                bid_item = {"KeywordId": kb["keyword_id"]}
                if kb.get("search_bid"):
                    bid_item["SearchBid"] = int(kb["search_bid"] * 1_000_000)
                if kb.get("network_bid"):
                    bid_item["NetworkBid"] = int(kb["network_bid"] * 1_000_000)
                keyword_bids.append(bid_item)

            request_params = {
                "KeywordBids": keyword_bids
            }

            result = await api_client.direct_request("keywordbids", "set", request_params)
            set_results = result.get("result", {}).get("SetResults", [])

            success = [r["KeywordId"] for r in set_results if r.get("KeywordId") and not r.get("Errors")]

            return f"Successfully updated bids for {len(success)} keyword(s)."

        except Exception as e:
            return handle_api_error(e)

    for action in ("suspend", "resume", "delete"):
        register_manage_tool(
            mcp,
            service="keywords",
            action=action,
            entity="keyword",
            input_model=ManageKeywordInput,
            ids_field="keyword_ids",
        )
