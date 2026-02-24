"""Yandex Direct statistics tools."""

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
        - CampaignName, CampaignId - Campaign info
        - Impressions, Clicks, Cost - Basic metrics
        - Ctr, AvgCpc, ConversionRate - Calculated metrics
        - Date - For daily breakdown
        """
        try:
            # Build report definition
            report_def = {
                "SelectionCriteria": {
                    "DateFrom": params.date_from,
                    "DateTo": params.date_to
                },
                "FieldNames": params.field_names,
                "ReportName": f"Report_{params.date_from}_{params.date_to}",
                "ReportType": params.report_type,
                "DateRangeType": "CUSTOM_DATE",
                "Format": "TSV",
                "IncludeVAT": "YES" if params.include_vat else "NO",
                "IncludeDiscount": "NO"
            }

            if params.campaign_ids:
                report_def["SelectionCriteria"]["Filter"] = [{
                    "Field": "CampaignId",
                    "Operator": "IN",
                    "Values": [str(cid) for cid in params.campaign_ids]
                }]

            # Get Direct token
            token = api_client._get_direct_token()
            if not token:
                raise ValueError("Yandex Direct API token not configured.")

            url = f"{api_client._get_direct_url()}/reports"
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

            if api_client.client_login:
                headers["Client-Login"] = api_client.client_login

            async with httpx.AsyncClient(timeout=REPORT_TIMEOUT) as client:
                response = await client.post(url, json={"params": report_def}, headers=headers)

                if response.status_code == 200:
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

                elif response.status_code == 201 or response.status_code == 202:
                    return "Report is being generated. Please try again in a few seconds."

                else:
                    response.raise_for_status()

            return "Unexpected response from API."

        except Exception as e:
            return handle_api_error(e)
