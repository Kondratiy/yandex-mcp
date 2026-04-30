"""Yandex Direct statistics tools."""

import asyncio
import json
import httpx
from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...config import REPORT_TIMEOUT
from ...models.common import ResponseFormat
from ...models.direct import DirectReportInput
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register statistics tools."""

    @mcp.tool(
        name="direct_get_statistics",
        annotations={
            "title": "Get Yandex Direct Statistics",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def direct_get_statistics(params: DirectReportInput) -> str:
        """Get campaign statistics report from Yandex Direct.

        Retrieves performance statistics for campaigns, ads, or keywords.

        Report types:
        - ACCOUNT_PERFORMANCE_REPORT - Account level stats
        - CAMPAIGN_PERFORMANCE_REPORT - Campaign level stats (default)
        - AD_PERFORMANCE_REPORT - Ad level stats
        - ADGROUP_PERFORMANCE_REPORT - Ad group level stats
        - CRITERIA_PERFORMANCE_REPORT - Keyword level stats
        - SEARCH_QUERY_PERFORMANCE_REPORT - Search query stats

        Common fields:
        - CampaignName, CampaignId, CampaignType - Campaign info
        - AdId, AdGroupId, AdGroupName, AdFormat - Ad/group info
        - Impressions, Clicks, Cost - Basic metrics
        - Ctr, AvgCpc, ConversionRate - Calculated metrics
        - Conversions, CostPerConversion, Revenue - Conversion metrics
        - Date, Month, Quarter, Year - Time breakdown

        Per-goal conversions:
        To get conversions broken down by Metrika goal, pass goal IDs
        in the 'goals' parameter and include Conversions/CostPerConversion/Revenue
        in field_names. The API will return columns like:
          Conversions_<GoalId>_<Attribution> (e.g. Conversions_155538619_LSC)
          CostPerConversion_<GoalId>_<Attribution>
          Revenue_<GoalId>_<Attribution>

        Example: goals=[155538619, 326960392] with field_names=["CampaignId", "Conversions", "CostPerConversion"]
        → columns: Conversions_155538619_LSC, Conversions_326960392_LSC, CostPerConversion_155538619_LSC, ...

        Attribution suffix: LSC = Last Significant Click, FC = First Click, LC = Last Click.
        """
        try:
            # Build report definition
            report_def = {
                "SelectionCriteria": {
                    "DateFrom": params.date_from,
                    "DateTo": params.date_to
                },
                "FieldNames": params.field_names,
                "ReportName": f"Report_{params.report_type}_{params.date_from}_{params.date_to}_{hash(tuple(params.field_names))}",
                "ReportType": params.report_type,
                "DateRangeType": "CUSTOM_DATE",
                "Format": "TSV",
                "IncludeVAT": "YES" if params.include_vat else "NO",
                "IncludeDiscount": "NO"
            }

            if params.goals:
                report_def["Goals"] = params.goals

            if params.campaign_ids:
                report_def["SelectionCriteria"]["Filter"] = [{
                    "Field": "CampaignId",
                    "Operator": "IN",
                    "Values": [str(cid) for cid in params.campaign_ids]
                }]

            # Resolve account and get its credentials
            cfg = api_client._resolve_account(params.account)
            token = cfg.direct_token

            url = f"{api_client._get_direct_url(cfg.use_sandbox)}/reports"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept-Language": "ru",
                "Content-Type": "application/json",
                "processingMode": "auto",
                "returnMoneyInMicros": "false",
                "skipReportHeader": "true",
                "skipColumnHeader": "false",
                "skipReportSummary": "true"
            }

            if cfg.client_login:
                headers["Client-Login"] = cfg.client_login

            max_attempts = 10
            response = None
            async with httpx.AsyncClient(timeout=REPORT_TIMEOUT) as client:
                for attempt in range(max_attempts):
                    response = await client.post(url, json={"params": report_def}, headers=headers)

                    if response.status_code == 200:
                        break

                    if response.status_code in (201, 202):
                        wait = int(response.headers.get("retryIn", 5))
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(wait)
                            continue
                        return "Report is still being generated. Please try again later."

                    response.raise_for_status()

            if response is None or response.status_code != 200:
                return "Unexpected response from Reports API."

            # Parse TSV response
            lines = response.text.strip().split("\n")
            if len(lines) < 2:
                return "No data found for the specified period."

            header = lines[0].split("\t")
            data_rows = [line.split("\t") for line in lines[1:] if line.strip()]

            if params.response_format == ResponseFormat.JSON:
                result = []
                for row in data_rows:
                    result.append(dict(zip(header, row)))
                return json.dumps({"data": result, "total": len(result)}, indent=2, ensure_ascii=False)

            # Format as markdown
            md_lines = ["# Direct Statistics Report\n"]
            md_lines.append(f"**Period**: {params.date_from} - {params.date_to}")
            md_lines.append(f"**Report type**: {params.report_type}\n")

            md_lines.append("| " + " | ".join(header) + " |")
            md_lines.append("| " + " | ".join(["---"] * len(header)) + " |")

            for row in data_rows[:100]:  # Limit to 100 rows
                md_lines.append("| " + " | ".join(row) + " |")

            if len(data_rows) > 100:
                md_lines.append(f"\n*...and {len(data_rows) - 100} more rows*")

            return "\n".join(md_lines)

        except Exception as e:
            return handle_api_error(e)
