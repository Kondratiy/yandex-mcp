"""Utility functions for Yandex MCP Server."""

import httpx


def handle_api_error(e: Exception) -> str:
    """Format API errors into actionable messages."""
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        url = str(e.request.url) if e.request else ""

        # Wordstat-specific 403 — different OAuth scope required than Direct.
        # Direct tokens (direct:api) do NOT automatically grant Wordstat access;
        # the token must additionally carry the wordstat:api scope.
        if status == 403 and "wordstat.yandex" in url:
            return (
                "API Error (403): Wordstat access denied. Wordstat API access "
                "is a TWO-STEP process at Yandex — having scope on the OAuth "
                "app is NOT enough by itself.\n\n"
                "Step 1: OAuth app at https://oauth.yandex.ru/ must have "
                "BOTH 'direct:api' AND 'wordstat:api' permissions.\n\n"
                "Step 2: contact Yandex Direct support and request Wordstat "
                "API enrolment for your username + ClientId. Until support "
                "confirms enrolment, ALL tokens of that app return 403 — "
                "re-issuing the token does NOT help. Per Yandex docs: "
                "\"To connect to the API, contact the Yandex Direct support, "
                "providing your username and ClientId\" "
                "(https://yandex.ru/support2/wordstat/en/content/api-wordstat).\n\n"
                "Step 3: after support confirms, (re-)issue the token and "
                "put it into YANDEX_ACCOUNTS for this account. Note that "
                "existing tokens issued BEFORE both scopes were on the app "
                "won't have wordstat:api — must be re-issued."
            )

        try:
            error_body = e.response.json()
            # Yandex Direct format: {"error": {"error_string": ..., "error_detail": ...}}
            error_obj = error_body.get("error", {})
            if isinstance(error_obj, dict) and error_obj.get("error_string"):
                error_msg = error_obj["error_string"]
                error_detail = error_obj.get("error_detail", "")
                return f"API Error ({status}): {error_msg}. {error_detail}".strip()
            # AppMetrica format: {"errors": [{"error_type": ..., "message": ...}], "message": ...}
            errors_list = error_body.get("errors")
            if isinstance(errors_list, list) and errors_list:
                messages = [err.get("message", "") for err in errors_list if isinstance(err, dict)]
                joined = "; ".join(m for m in messages if m)
                if joined:
                    return f"API Error ({status}): {joined}"
            # Fallback: top-level message
            if isinstance(error_body, dict) and error_body.get("message"):
                return f"API Error ({status}): {error_body['message']}"
        except Exception:
            pass

        error_messages = {
            400: "Bad request. Check your parameters.",
            401: "Authentication failed. Check your API token.",
            403: "Access denied. Check permissions for this operation.",
            404: "Resource not found. Check the ID.",
            429: "Rate limit exceeded. Wait before making more requests.",
            500: "Server error. Try again later.",
            503: "Service unavailable. Try again later."
        }
        return f"API Error: {error_messages.get(status, f'Request failed with status {status}')}"

    if isinstance(e, httpx.TimeoutException):
        return "Request timed out. The operation may still complete on the server."

    if isinstance(e, ValueError):
        return f"Configuration Error: {str(e)}"

    return f"Unexpected error: {type(e).__name__}: {str(e)}"
