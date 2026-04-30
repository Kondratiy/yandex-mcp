"""Unified API client for Yandex Direct and Metrika APIs.

Supports multiple Yandex accounts via YANDEX_ACCOUNTS env (JSON).
Falls back to legacy single-account env (YANDEX_DIRECT_TOKEN, YANDEX_TOKEN,
YANDEX_METRIKA_TOKEN, YANDEX_CLIENT_LOGIN, YANDEX_USE_SANDBOX) for
backward compatibility.
"""

import asyncio
import json
import logging
import os
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from .config import (
    DEFAULT_TIMEOUT,
    YANDEX_APPMETRICA_API_URL,
    YANDEX_APPMETRICA_PUSH_API_URL,
    YANDEX_DIRECT_API_URL,
    YANDEX_DIRECT_API_URL_V501,
    YANDEX_DIRECT_SANDBOX_URL,
    YANDEX_METRIKA_API_URL,
)

logger = logging.getLogger(__name__)


class AccountConfig(BaseModel):
    """Per-account credentials for Yandex Direct (and Wordstat).

    Note: Metrika is intentionally NOT per-account — it uses a single global
    YANDEX_METRIKA_TOKEN / YANDEX_TOKEN regardless of which Direct account
    a request targets.
    """
    direct_token: str = Field(..., description="OAuth token for Yandex Direct API")
    client_login: str | None = Field(
        default=None,
        description="Client-Login header value for agency scenarios",
    )
    use_sandbox: bool = Field(
        default=False,
        description="If true, all Direct API calls use sandbox endpoint",
    )


class YandexAPIClient:
    """Unified client for Yandex Direct, Metrika and Wordstat APIs.

    Reads accounts from env on instantiation:
      - YANDEX_ACCOUNTS (JSON object {name: {...}}) — primary multi-account format
      - Otherwise legacy single-account env collapsed into one "default" account

    Each request method accepts optional account=<name>; if omitted, the first
    account from the parsed dict is used.
    """

    def __init__(self):
        self.accounts: dict[str, AccountConfig] = self._parse_accounts_env()
        if not self.accounts:
            raise ValueError(
                "No Yandex accounts configured. "
                "Set YANDEX_ACCOUNTS (JSON object) or "
                "YANDEX_DIRECT_TOKEN / YANDEX_TOKEN (legacy single-account)."
            )
        self.default_account: str = next(iter(self.accounts))
        # Metrika has its own single global token (NOT per-account):
        # priority — YANDEX_METRIKA_TOKEN → YANDEX_TOKEN → first account's direct_token (legacy fallback).
        self.metrika_token: str = (
            os.environ.get("YANDEX_METRIKA_TOKEN", "").strip()
            or os.environ.get("YANDEX_TOKEN", "").strip()
            or self.accounts[self.default_account].direct_token
        )
        # AppMetrica is also single-token (NOT per-account), like Metrika.
        # In practice a single Yandex.Metrica-family OAuth token usually works
        # for BOTH services (verified empirically: a Metrika token with
        # `metrika:read_stats` scope returns 200 from AppMetrica's
        # /management/v1/applications). So we add YANDEX_METRIKA_TOKEN to the
        # fallback chain for convenience — users who already configured Metrika
        # don't need to register a separate AppMetrica token.
        # priority — YANDEX_APPMETRICA_TOKEN → YANDEX_METRIKA_TOKEN → YANDEX_TOKEN → "" (raises at use site).
        self.appmetrica_token: str = (
            os.environ.get("YANDEX_APPMETRICA_TOKEN", "").strip()
            or os.environ.get("YANDEX_METRIKA_TOKEN", "").strip()
            or os.environ.get("YANDEX_TOKEN", "").strip()
        )

    @staticmethod
    def _parse_accounts_env() -> dict[str, AccountConfig]:
        """Parse account configuration from environment.

        Priority:
          1. YANDEX_ACCOUNTS — JSON object {"name": {direct_token, ...}, ...}
          2. Legacy: YANDEX_DIRECT_TOKEN / YANDEX_TOKEN → virtual "default" account
        """
        raw = os.environ.get("YANDEX_ACCOUNTS", "").strip()
        if raw:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as e:
                raise ValueError(f"YANDEX_ACCOUNTS is not valid JSON: {e}")
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"YANDEX_ACCOUNTS must be a JSON object, got {type(parsed).__name__}"
                )
            try:
                return {
                    name: AccountConfig.model_validate(cfg)
                    for name, cfg in parsed.items()
                }
            except ValidationError as e:
                raise ValueError(f"Invalid account config in YANDEX_ACCOUNTS: {e}")

        # Legacy fallback — single virtual "default" account (Direct/Wordstat only;
        # Metrika token handled separately via YANDEX_METRIKA_TOKEN/YANDEX_TOKEN).
        unified = os.environ.get("YANDEX_TOKEN", "").strip()
        direct = os.environ.get("YANDEX_DIRECT_TOKEN", "").strip() or unified
        if not direct:
            return {}
        client_login = os.environ.get("YANDEX_CLIENT_LOGIN", "").strip() or None
        use_sandbox = os.environ.get("YANDEX_USE_SANDBOX", "false").lower() == "true"
        return {
            "default": AccountConfig(
                direct_token=direct,
                client_login=client_login,
                use_sandbox=use_sandbox,
            )
        }

    def _resolve_account(self, name: str | None) -> AccountConfig:
        """Look up account config by name (or default if name is None)."""
        key = name or self.default_account
        if key not in self.accounts:
            raise ValueError(
                f"Unknown account '{key}'. Available: {list(self.accounts)}"
            )
        return self.accounts[key]

    def _get_direct_url(self, use_sandbox: bool, use_v501: bool = False) -> str:
        """Get Direct API URL based on account sandbox flag and v501 flag."""
        if use_sandbox:
            return YANDEX_DIRECT_SANDBOX_URL
        return YANDEX_DIRECT_API_URL_V501 if use_v501 else YANDEX_DIRECT_API_URL

    async def direct_request(
        self,
        service: str,
        method: str,
        params: dict[str, Any],
        use_v501: bool = False,
        timeout: float | None = None,
        account: str | None = None,
    ) -> dict[str, Any]:
        """Make a request to Yandex Direct API for the given account."""
        cfg = self._resolve_account(account)
        token = cfg.direct_token

        url = f"{self._get_direct_url(cfg.use_sandbox, use_v501)}/{service}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept-Language": "ru",
            "Content-Type": "application/json",
        }

        if cfg.client_login:
            headers["Client-Login"] = cfg.client_login

        payload = {
            "method": method,
            "params": params,
        }

        req_timeout = timeout or DEFAULT_TIMEOUT
        async with httpx.AsyncClient(timeout=req_timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def metrika_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a request to Yandex Metrika API.

        Note: Metrika is NOT per-account — uses a single global token
        (YANDEX_METRIKA_TOKEN / YANDEX_TOKEN). Multi-account routing
        applies only to Direct (and Wordstat).
        """
        token = self.metrika_token
        if not token:
            raise ValueError(
                "Yandex Metrika API token not configured. "
                "Set YANDEX_METRIKA_TOKEN or YANDEX_TOKEN environment variable."
            )

        url = f"{YANDEX_METRIKA_API_URL}{endpoint}"
        headers = {
            "Authorization": f"OAuth {token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            if method == "GET":
                response = await client.get(url, params=params, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=data, params=params, headers=headers)
            elif method == "PUT":
                response = await client.put(url, json=data, params=params, headers=headers)
            elif method == "DELETE":
                response = await client.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            if response.status_code == 204:
                return {"success": True}

            return response.json()

    async def wordstat_request(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        account: str | None = None,
    ) -> dict[str, Any]:
        """Make a request to Yandex Wordstat API for the given account."""
        cfg = self._resolve_account(account)
        token = cfg.direct_token  # Wordstat uses Direct OAuth token

        from .config import YANDEX_WORDSTAT_API_URL
        url = f"{YANDEX_WORDSTAT_API_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json;charset=utf-8",
        }

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(url, json=data or {}, headers=headers)
            response.raise_for_status()
            return response.json()

    async def appmetrica_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        timeout: float | None = None,
        use_push_api: bool = False,
    ) -> dict[str, Any]:
        """Make a request to Yandex AppMetrica API.

        Note: AppMetrica is NOT per-account — uses a single global token
        (YANDEX_APPMETRICA_TOKEN / YANDEX_TOKEN). Multi-account routing
        applies only to Direct (and Wordstat).
        """
        token = self.appmetrica_token
        if not token:
            raise ValueError(
                "Yandex AppMetrica API token not configured. "
                "Set YANDEX_APPMETRICA_TOKEN, YANDEX_METRIKA_TOKEN, or "
                "YANDEX_TOKEN environment variable."
            )

        base_url = YANDEX_APPMETRICA_PUSH_API_URL if use_push_api else YANDEX_APPMETRICA_API_URL
        url = f"{base_url}{endpoint}"
        headers = {
            "Authorization": f"OAuth {token}",
            "Content-Type": "application/json",
        }

        req_timeout = timeout or DEFAULT_TIMEOUT
        async with httpx.AsyncClient(timeout=req_timeout) as client:
            if method == "GET":
                response = await client.get(url, params=params, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=data, params=params, headers=headers)
            elif method == "PUT":
                response = await client.put(url, json=data, params=params, headers=headers)
            elif method == "DELETE":
                response = await client.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            if response.status_code == 204:
                return {"success": True}

            return response.json()

    async def appmetrica_logs_export(
        self,
        export_type: str,
        application_id: int,
        date_since: str,
        date_until: str,
        fields: list[str] | None = None,
        max_wait_seconds: int = 600,
        poll_interval: float = 10.0,
    ) -> list[dict[str, Any]]:
        """Export from AppMetrica Logs API with async polling.

        Logs API is asynchronous: the first GET schedules a report and
        returns HTTP 202; subsequent identical GETs poll until HTTP 200
        with the prepared body. This helper hides that loop and returns
        the list of rows directly.

        Args:
            export_type: clicks / installations / postbacks / events /
                sessions_starts / crashes / errors / push_tokens /
                deeplinks / profiles_v2 / revenue_events /
                ecommerce_events / ad_revenue_events
            application_id: AppMetrica application ID
            date_since / date_until: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS
            fields: subset of available columns; None = all
            max_wait_seconds: total polling timeout (default 10 min)
            poll_interval: seconds between 202 polls (default 10s)

        Raises:
            ValueError: token not configured
            TimeoutError: report not ready before max_wait_seconds
            httpx.HTTPStatusError: 4xx/5xx other than 202
        """
        if not self.appmetrica_token:
            raise ValueError(
                "Yandex AppMetrica API token not configured. "
                "Set YANDEX_APPMETRICA_TOKEN, YANDEX_METRIKA_TOKEN, or "
                "YANDEX_TOKEN environment variable."
            )

        url = f"{YANDEX_APPMETRICA_API_URL}/logs/v1/export/{export_type}.json"
        headers = {"Authorization": f"OAuth {self.appmetrica_token}"}
        params: dict[str, Any] = {
            "application_id": application_id,
            "date_since": date_since,
            "date_until": date_until,
        }
        if fields:
            params["fields"] = ",".join(fields)

        loop = asyncio.get_running_loop()
        deadline = loop.time() + max_wait_seconds

        # Read timeout scales with max_wait_seconds (download of large logs
        # can take a while); connect timeout is bounded.
        read_timeout = max(120.0, float(max_wait_seconds))
        timeout_cfg = httpx.Timeout(read_timeout, connect=30.0)

        async with httpx.AsyncClient(timeout=timeout_cfg) as client:
            while True:
                response = await client.get(url, params=params, headers=headers)

                if response.status_code == 200:
                    payload = response.json()
                    if isinstance(payload, list):
                        return payload
                    if isinstance(payload, dict) and "data" in payload:
                        return payload["data"]
                    # Unknown shape — warn and degrade to empty so the
                    # caller still gets a valid list (vs. crashing).
                    shape = (
                        f"dict[keys={list(payload)[:8]}]"
                        if isinstance(payload, dict)
                        else type(payload).__name__
                    )
                    logger.warning(
                        "AppMetrica Logs API returned unexpected payload "
                        "shape for export_type=%s, date_since=%s, "
                        "date_until=%s: %s",
                        export_type, date_since, date_until, shape,
                    )
                    return []

                if response.status_code == 202:
                    if loop.time() > deadline:
                        raise TimeoutError(
                            f"AppMetrica Logs API report for '{export_type}' "
                            f"({date_since} to {date_until}) did not finish "
                            f"within {max_wait_seconds}s. Try a smaller date "
                            f"range or fewer fields."
                        )
                    await asyncio.sleep(poll_interval)
                    continue

                response.raise_for_status()


# Global API client instance — created at import time using current env
api_client = YandexAPIClient()
