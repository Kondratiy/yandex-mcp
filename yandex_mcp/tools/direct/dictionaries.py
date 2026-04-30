"""Yandex Direct dictionaries tools."""

import json
from typing import Optional

from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...models.common import ResponseFormat
from ...models.direct_extended import GetDictionariesInput
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register dictionary tools."""

    @mcp.tool(
        name="direct_get_dictionaries",
        annotations={
            "title": "Get Yandex Direct Dictionaries",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_dictionaries(params: GetDictionariesInput) -> str:
        """Get dictionaries from Yandex Direct.

        Available dictionaries:
        - Regions: Geographic regions for targeting
        - TimeZones: Available time zones
        - Constants: API constants and limits
        - AdCategories: Ad categories
        - OperationSystemVersions: OS versions for mobile targeting
        - ProductivityAssertions: Productivity assertions
        - SupplySidePlatforms: SSP platforms for RTB
        - Interests: Interest categories for targeting
        - AudienceCriteriaTypes: Audience criteria types
        """
        try:
            request_params = {
                "DictionaryNames": params.dictionary_names
            }

            result = await api_client.direct_request("dictionaries", "get", request_params, account=params.account)
            data = result.get("result", {})

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(data, indent=2, ensure_ascii=False)

            lines = ["# Yandex Direct Dictionaries\n"]

            # Regions
            if "GeoRegions" in data:
                lines.append("## Geographic Regions\n")
                regions = data["GeoRegions"]
                for region in regions[:50]:  # Limit output
                    lines.append(f"- **{region.get('GeoRegionName')}** (ID: {region.get('GeoRegionId')}, Type: {region.get('GeoRegionType')})")
                if len(regions) > 50:
                    lines.append(f"\n... and {len(regions) - 50} more regions")
                lines.append("")

            # TimeZones
            if "TimeZones" in data:
                lines.append("## Time Zones\n")
                for tz in data["TimeZones"]:
                    lines.append(f"- **{tz.get('TimeZoneName')}** ({tz.get('TimeZone')})")
                lines.append("")

            # Constants
            if "Constants" in data:
                lines.append("## API Constants\n")
                constants = data["Constants"]
                for key, value in constants.items():
                    lines.append(f"- **{key}**: {value}")
                lines.append("")

            # AdCategories
            if "AdCategories" in data:
                lines.append("## Ad Categories\n")
                for cat in data["AdCategories"]:
                    lines.append(f"- **{cat.get('AdCategoryName')}** (ID: {cat.get('AdCategory')})")
                lines.append("")

            # OperationSystemVersions
            if "OperationSystemVersions" in data:
                lines.append("## OS Versions\n")
                for os_ver in data["OperationSystemVersions"]:
                    lines.append(f"- **{os_ver.get('OsType')}** {os_ver.get('OsVersion')} (ID: {os_ver.get('OsVersionId')})")
                lines.append("")

            # SupplySidePlatforms
            if "SupplySidePlatforms" in data:
                lines.append("## Supply Side Platforms (SSP)\n")
                for ssp in data["SupplySidePlatforms"]:
                    lines.append(f"- **{ssp.get('Title')}**")
                lines.append("")

            # Interests
            if "Interests" in data:
                lines.append("## Interest Categories\n")
                for interest in data["Interests"][:30]:
                    parent = f" (Parent: {interest.get('ParentId')})" if interest.get('ParentId') else ""
                    # API returns the field as "Name", not "InterestName".
                    lines.append(f"- **{interest.get('Name')}** (ID: {interest.get('InterestId')}){parent}")
                if len(data["Interests"]) > 30:
                    lines.append(f"\n... and {len(data['Interests']) - 30} more interests")
                lines.append("")

            # AudienceCriteriaTypes
            if "AudienceCriteriaTypes" in data:
                lines.append("## Audience Criteria Types\n")
                for act in data["AudienceCriteriaTypes"]:
                    lines.append(f"- **{act.get('Name')}** (Type: {act.get('Type')})")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_get_regions",
        annotations={
            "title": "Get Yandex Direct Regions",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_regions(
        response_format: ResponseFormat = ResponseFormat.MARKDOWN,
        account: Optional[str] = None,
    ) -> str:
        """Get geographic regions for targeting.

        Returns list of regions with IDs for use in geo-targeting.
        Useful for finding region IDs to use in campaign settings.
        """
        try:
            request_params = {
                "DictionaryNames": ["GeoRegions"]
            }

            result = await api_client.direct_request("dictionaries", "get", request_params, account=account)
            regions = result.get("result", {}).get("GeoRegions", [])

            if response_format == ResponseFormat.JSON:
                return json.dumps({"regions": regions, "total": len(regions)}, indent=2, ensure_ascii=False)

            if not regions:
                return "No regions found."

            # Group by type
            by_type = {}
            for region in regions:
                rtype = region.get("GeoRegionType", "Unknown")
                if rtype not in by_type:
                    by_type[rtype] = []
                by_type[rtype].append(region)

            lines = ["# Geographic Regions\n"]
            for rtype, rlist in sorted(by_type.items()):
                lines.append(f"## {rtype} ({len(rlist)} items)\n")
                for r in rlist[:20]:  # Limit per type
                    parent = f" [Parent: {r.get('ParentId')}]" if r.get('ParentId') else ""
                    lines.append(f"- {r.get('GeoRegionName')} (ID: {r.get('GeoRegionId')}){parent}")
                if len(rlist) > 20:
                    lines.append(f"... and {len(rlist) - 20} more")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="direct_get_interests",
        annotations={
            "title": "Get Yandex Direct Interests",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_interests(
        response_format: ResponseFormat = ResponseFormat.MARKDOWN,
        account: Optional[str] = None,
    ) -> str:
        """Get interest categories for targeting.

        Returns list of interests for use in audience targeting.
        """
        try:
            request_params = {
                "DictionaryNames": ["Interests"]
            }

            result = await api_client.direct_request("dictionaries", "get", request_params, account=account)
            interests = result.get("result", {}).get("Interests", [])

            if response_format == ResponseFormat.JSON:
                return json.dumps({"interests": interests, "total": len(interests)}, indent=2, ensure_ascii=False)

            if not interests:
                return "No interests found."

            # Build tree structure
            root_interests = [i for i in interests if not i.get("ParentId")]
            child_map = {}
            for i in interests:
                parent = i.get("ParentId")
                if parent:
                    if parent not in child_map:
                        child_map[parent] = []
                    child_map[parent].append(i)

            lines = ["# Interest Categories\n"]
            for root in root_interests:
                rid = root.get("InterestId")
                # API field name is "Name", not "InterestName".
                lines.append(f"## {root.get('Name')} (ID: {rid})")
                if rid in child_map:
                    for child in child_map[rid]:
                        lines.append(f"  - {child.get('Name')} (ID: {child.get('InterestId')})")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)
