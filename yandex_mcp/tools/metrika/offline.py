"""Yandex Metrika offline data tools - conversions, calls, expenses."""

import json
from mcp.server.fastmcp import FastMCP

from ...client import api_client
from ...models.common import ResponseFormat
from ...models.metrika_extended import (
    UploadOfflineConversionsInput,
    GetOfflineConversionsUploadingsInput,
    UploadCallsInput,
    UploadExpensesInput,
    UploadUserParametersInput,
)
from ...utils import handle_api_error


def register(mcp: FastMCP) -> None:
    """Register offline data tools."""

    # =========================================================================
    # Offline Conversions
    # =========================================================================

    @mcp.tool(
        name="metrika_upload_offline_conversions",
        annotations={
            "title": "Upload Offline Conversions to Yandex Metrika",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def metrika_upload_offline_conversions(params: UploadOfflineConversionsInput) -> str:
        """Upload offline conversions to Yandex Metrika.

        Offline conversions link CRM data to website visits.
        Requires ClientID, UserID, or YCLID to match visitors.

        Identifier types:
        - CLIENT_ID: Yandex Metrika's _ym_uid cookie value
        - USER_ID: Custom UserID set via ym('setUserID')
        - YCLID: Yandex Direct click identifier from URL

        Processing takes 24-48 hours.
        """
        try:
            # Build CSV-like data
            conversions_data = []
            for conv in params.conversions:
                row = {
                    "DateTime": conv.date_time,
                    "Target": conv.target
                }
                if conv.client_id:
                    row["ClientId"] = conv.client_id
                if conv.user_id:
                    row["UserId"] = conv.user_id
                if conv.yclid:
                    row["Yclid"] = conv.yclid
                if conv.price is not None:
                    row["Price"] = conv.price
                if conv.currency:
                    row["Currency"] = conv.currency
                if conv.order_id:
                    row["OrderId"] = conv.order_id
                conversions_data.append(row)

            # Upload via Metrika API
            result = await api_client.metrika_request(
                f"management/v1/counter/{params.counter_id}/offline_conversions/upload",
                method="POST",
                params={"client_id_type": params.client_id_type},
                json_data={"conversions": conversions_data}
            )

            uploading_id = result.get("uploading", {}).get("id")
            if uploading_id:
                return f"Offline conversions uploaded successfully.\nUploading ID: {uploading_id}\n\nProcessing takes 24-48 hours. Check status with metrika_get_offline_conversions_status."

            return f"Upload initiated. Response: {json.dumps(result, ensure_ascii=False)}"

        except Exception as e:
            return handle_api_error(e)

    @mcp.tool(
        name="metrika_get_offline_conversions_status",
        annotations={
            "title": "Get Offline Conversions Upload Status",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    async def metrika_get_offline_conversions_status(params: GetOfflineConversionsUploadingsInput) -> str:
        """Get status of offline conversions uploads.

        Shows processing status and any errors.
        """
        try:
            result = await api_client.metrika_request(
                f"management/v1/counter/{params.counter_id}/offline_conversions/uploadings",
                params={"limit": params.limit}
            )

            uploadings = result.get("uploadings", [])

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"uploadings": uploadings, "total": len(uploadings)}, indent=2, ensure_ascii=False)

            if not uploadings:
                return "No offline conversion uploads found."

            lines = ["# Offline Conversions Uploads\n"]
            for u in uploadings:
                lines.append(f"## Upload ID: {u.get('id')}")
                lines.append(f"- **Status**: {u.get('status', 'N/A')}")
                lines.append(f"- **Created**: {u.get('create_time', 'N/A')}")
                lines.append(f"- **Lines**: {u.get('line_quantity', 0)}")
                lines.append(f"- **Matched**: {u.get('matched_quantity', 0)}")
                lines.append(f"- **Not Matched**: {u.get('not_matched_quantity', 0)}")
                if u.get('errors'):
                    lines.append(f"- **Errors**: {', '.join(u['errors'])}")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)

    # =========================================================================
    # Calls
    # =========================================================================

    @mcp.tool(
        name="metrika_upload_calls",
        annotations={
            "title": "Upload Calls to Yandex Metrika",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def metrika_upload_calls(params: UploadCallsInput) -> str:
        """Upload call data to Yandex Metrika.

        Links phone call data to website visits.
        Useful for call tracking integration.

        Call data is matched to visitors by ClientID, UserID, or YCLID.
        """
        try:
            calls_data = []
            for call in params.calls:
                row = {
                    "DateTime": call.date_time,
                    "CallMissed": "1" if call.call_missed else "0",
                    "FirstTimeCaller": "1" if call.first_time_caller else "0"
                }
                if call.client_id:
                    row["ClientId"] = call.client_id
                if call.user_id:
                    row["UserId"] = call.user_id
                if call.yclid:
                    row["Yclid"] = call.yclid
                if call.phone_number:
                    row["PhoneNumber"] = call.phone_number
                if call.talk_duration is not None:
                    row["TalkDuration"] = call.talk_duration
                if call.tag:
                    row["Tag"] = call.tag
                if call.url:
                    row["URL"] = call.url
                calls_data.append(row)

            request_params = {"client_id_type": params.client_id_type}
            if params.new_goal_name:
                request_params["new_goal_name"] = params.new_goal_name

            result = await api_client.metrika_request(
                f"management/v1/counter/{params.counter_id}/offline_conversions/calls/upload",
                method="POST",
                params=request_params,
                json_data={"calls": calls_data}
            )

            uploading_id = result.get("uploading", {}).get("id")
            if uploading_id:
                return f"Calls uploaded successfully.\nUploading ID: {uploading_id}"

            return f"Upload initiated. Response: {json.dumps(result, ensure_ascii=False)}"

        except Exception as e:
            return handle_api_error(e)

    # =========================================================================
    # Expenses
    # =========================================================================

    @mcp.tool(
        name="metrika_upload_expenses",
        annotations={
            "title": "Upload Expenses to Yandex Metrika",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def metrika_upload_expenses(params: UploadExpensesInput) -> str:
        """Upload advertising expenses to Yandex Metrika.

        Links advertising costs from non-Yandex sources.
        Expenses are matched by UTM parameters.

        Required: date, utm_source, expenses
        Optional: utm_medium, utm_campaign, utm_content, utm_term, clicks, impressions
        """
        try:
            expenses_data = []
            for exp in params.expenses:
                row = {
                    "Date": exp.date,
                    "UTMSource": exp.utm_source,
                    "Expenses": exp.expenses,
                    "Currency": exp.currency
                }
                if exp.utm_medium:
                    row["UTMMedium"] = exp.utm_medium
                if exp.utm_campaign:
                    row["UTMCampaign"] = exp.utm_campaign
                if exp.utm_content:
                    row["UTMContent"] = exp.utm_content
                if exp.utm_term:
                    row["UTMTerm"] = exp.utm_term
                if exp.clicks is not None:
                    row["Clicks"] = exp.clicks
                if exp.impressions is not None:
                    row["Impressions"] = exp.impressions
                expenses_data.append(row)

            result = await api_client.metrika_request(
                f"management/v1/counter/{params.counter_id}/expense/upload",
                method="POST",
                json_data={"expenses": expenses_data}
            )

            uploading_id = result.get("uploading", {}).get("id")
            if uploading_id:
                return f"Expenses uploaded successfully.\nUploading ID: {uploading_id}"

            return f"Upload initiated. Response: {json.dumps(result, ensure_ascii=False)}"

        except Exception as e:
            return handle_api_error(e)

    # =========================================================================
    # User Parameters
    # =========================================================================

    @mcp.tool(
        name="metrika_upload_user_parameters",
        annotations={
            "title": "Upload User Parameters to Yandex Metrika",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    async def metrika_upload_user_parameters(params: UploadUserParametersInput) -> str:
        """Upload user parameters/attributes to Yandex Metrika.

        Enriches visitor data with CRM attributes.
        Parameters can be used for segmentation and reporting.

        Example parameters: customer_type, lifetime_value, subscription_status
        """
        try:
            users_data = []
            for user in params.users:
                row = {"params": user.params}
                if user.client_id:
                    row["ClientId"] = user.client_id
                if user.user_id:
                    row["UserId"] = user.user_id
                users_data.append(row)

            result = await api_client.metrika_request(
                f"management/v1/counter/{params.counter_id}/user_params/uploadings",
                method="POST",
                params={"client_id_type": params.client_id_type},
                json_data={"users": users_data}
            )

            uploading_id = result.get("uploading", {}).get("id")
            if uploading_id:
                return f"User parameters uploaded successfully.\nUploading ID: {uploading_id}"

            return f"Upload initiated. Response: {json.dumps(result, ensure_ascii=False)}"

        except Exception as e:
            return handle_api_error(e)
