"""Yandex Wordstat API tools."""

import json
from mcp.server.fastmcp import FastMCP

from ..client import api_client
from ..models.common import ResponseFormat
from ..models.wordstat import (
    WordstatTopRequestsInput,
    WordstatDynamicsInput,
    WordstatRegionsInput,
    WordstatRegionsTreeInput,
    WordstatUserInfoInput,
)
from ..formatters.wordstat import (
    format_wordstat_top_requests_markdown,
    format_wordstat_dynamics_markdown,
    format_wordstat_regions_markdown,
)
from ..utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register Wordstat tools."""

    @mcp.tool(
        name="wordstat_top_requests",
        annotations={
            "title": "Get Wordstat Top Requests",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def wordstat_top_requests(params: WordstatTopRequestsInput) -> str:
        """Get popular search queries from Yandex Wordstat.

        Returns top requests and associated queries for given phrases.
        Provide either 'phrase' (single) or 'phrases' (multiple, max 128).
        """
        try:
            phrases = params.phrases or ([params.phrase] if params.phrase else [])
            if not phrases:
                return "Error: provide either 'phrase' or 'phrases' parameter."

            data = {
                "phrases": phrases,
                "numPhrases": params.num_phrases,
            }
            if params.regions is not None:
                data["regions"] = params.regions
            if params.devices is not None:
                data["devices"] = params.devices

            result = await api_client.wordstat_request("/v1/topRequests", data, account=params.account)

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(result, indent=2, ensure_ascii=False)

            return format_wordstat_top_requests_markdown(result)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="wordstat_dynamics",
        annotations={
            "title": "Get Wordstat Query Dynamics",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def wordstat_dynamics(params: WordstatDynamicsInput) -> str:
        """Get query frequency dynamics over time from Yandex Wordstat.

        Shows how search query popularity changes over a specified time period.
        Only the + operator is allowed in the phrase.
        """
        try:
            data = {
                "phrase": params.phrase,
                "period": params.period,
                "fromDate": params.from_date,
            }
            if params.to_date is not None:
                data["toDate"] = params.to_date
            if params.regions is not None:
                data["regions"] = params.regions
            if params.devices is not None:
                data["devices"] = params.devices

            result = await api_client.wordstat_request("/v1/dynamics", data, account=params.account)

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(result, indent=2, ensure_ascii=False)

            return format_wordstat_dynamics_markdown(result)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="wordstat_regions",
        annotations={
            "title": "Get Wordstat Regional Distribution",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def wordstat_regions(params: WordstatRegionsInput) -> str:
        """Get regional distribution of search queries from Yandex Wordstat.

        Shows how query popularity varies across different regions.
        """
        try:
            data = {
                "phrase": params.phrase,
                "regionType": params.region_type,
            }
            if params.devices is not None:
                data["devices"] = params.devices

            result = await api_client.wordstat_request("/v1/regions", data, account=params.account)

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(result, indent=2, ensure_ascii=False)

            return format_wordstat_regions_markdown(result)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="wordstat_regions_tree",
        annotations={
            "title": "Get Wordstat Regions Tree",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def wordstat_regions_tree(params: WordstatRegionsTreeInput) -> str:
        """Get the full regions tree from Yandex Wordstat.

        Returns hierarchical structure of all available regions with their IDs.
        Useful for finding region IDs to use in other Wordstat tools.
        """
        try:
            result = await api_client.wordstat_request("/v1/getRegionsTree", account=params.account)

            return json.dumps(result, indent=2, ensure_ascii=False)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="wordstat_user_info",
        annotations={
            "title": "Get Wordstat User Info",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def wordstat_user_info(params: WordstatUserInfoInput) -> str:
        """Get Wordstat user quota information.

        Returns current API usage limits and remaining quota.
        """
        try:
            result = await api_client.wordstat_request("/v1/userInfo", account=params.account)

            return json.dumps(result, indent=2, ensure_ascii=False)

        except Exception as e:
            return handle_api_error(e)
