"""Tests for multi-account configuration in YandexAPIClient.

These tests construct fresh YandexAPIClient instances rather than using
the module-level api_client singleton (which captures env at import time).
"""

import json
import pytest


def _clear_yandex_env(monkeypatch):
    """Remove all Yandex-related env vars so tests start from a clean slate."""
    for var in (
        "YANDEX_ACCOUNTS",
        "YANDEX_TOKEN",
        "YANDEX_DIRECT_TOKEN",
        "YANDEX_METRIKA_TOKEN",
        "YANDEX_CLIENT_LOGIN",
        "YANDEX_USE_SANDBOX",
    ):
        monkeypatch.delenv(var, raising=False)


def test_parse_accounts_from_json(monkeypatch):
    """YANDEX_ACCOUNTS JSON parses into multiple AccountConfig entries."""
    _clear_yandex_env(monkeypatch)
    from yandex_mcp.client import YandexAPIClient
    monkeypatch.setenv(
        "YANDEX_ACCOUNTS",
        json.dumps(
            {
                "first": {"direct_token": "t1", "client_login": "login-1"},
                "second": {"direct_token": "t2", "client_login": "login-2"},
            }
        ),
    )
    client = YandexAPIClient()
    assert list(client.accounts) == ["first", "second"]
    assert client.default_account == "first"
    assert client.accounts["first"].direct_token == "t1"
    assert client.accounts["first"].client_login == "login-1"
    assert client.accounts["second"].direct_token == "t2"


def test_legacy_fallback_token_only(monkeypatch):
    """Without YANDEX_ACCOUNTS, YANDEX_DIRECT_TOKEN creates a single 'default' account."""
    _clear_yandex_env(monkeypatch)
    from yandex_mcp.client import YandexAPIClient
    monkeypatch.setenv("YANDEX_DIRECT_TOKEN", "legacy-token")
    client = YandexAPIClient()
    assert list(client.accounts) == ["default"]
    assert client.default_account == "default"
    assert client.accounts["default"].direct_token == "legacy-token"
    assert client.accounts["default"].client_login is None


def test_legacy_fallback_with_client_login(monkeypatch):
    """Legacy env path fills client_login from YANDEX_CLIENT_LOGIN."""
    _clear_yandex_env(monkeypatch)
    from yandex_mcp.client import YandexAPIClient
    monkeypatch.setenv("YANDEX_DIRECT_TOKEN", "t")
    monkeypatch.setenv("YANDEX_CLIENT_LOGIN", "some-login")
    client = YandexAPIClient()
    cfg = client.accounts["default"]
    assert cfg.client_login == "some-login"


def test_resolve_default_returns_first(monkeypatch):
    """_resolve_account(None) returns the first account in dict insertion order."""
    _clear_yandex_env(monkeypatch)
    from yandex_mcp.client import YandexAPIClient
    monkeypatch.setenv(
        "YANDEX_ACCOUNTS",
        json.dumps(
            {
                "second": {"direct_token": "s"},
                "third": {"direct_token": "t"},
            }
        ),
    )
    client = YandexAPIClient()
    assert client._resolve_account(None).direct_token == "s"
    assert client._resolve_account("third").direct_token == "t"


def test_resolve_unknown_raises(monkeypatch):
    """_resolve_account('nope') raises ValueError with available accounts in message."""
    _clear_yandex_env(monkeypatch)
    from yandex_mcp.client import YandexAPIClient
    monkeypatch.setenv(
        "YANDEX_ACCOUNTS",
        json.dumps({"a": {"direct_token": "1"}, "b": {"direct_token": "2"}}),
    )
    client = YandexAPIClient()
    with pytest.raises(ValueError) as exc_info:
        client._resolve_account("nope")
    msg = str(exc_info.value)
    assert "Unknown account 'nope'" in msg
    assert "['a', 'b']" in msg


def test_invalid_json_fails_fast(monkeypatch):
    """Malformed YANDEX_ACCOUNTS JSON raises ValueError at construction time."""
    _clear_yandex_env(monkeypatch)
    from yandex_mcp.client import YandexAPIClient
    monkeypatch.setenv("YANDEX_ACCOUNTS", "{not valid json")
    with pytest.raises(ValueError) as exc_info:
        YandexAPIClient()
    assert "not valid JSON" in str(exc_info.value)


def test_no_credentials_raises(monkeypatch):
    """No env at all → ValueError with clear hint."""
    _clear_yandex_env(monkeypatch)
    from yandex_mcp.client import YandexAPIClient
    with pytest.raises(ValueError) as exc_info:
        YandexAPIClient()
    assert "No Yandex accounts configured" in str(exc_info.value)


def test_account_config_requires_direct_token(monkeypatch):
    """AccountConfig validation: direct_token is mandatory."""
    _clear_yandex_env(monkeypatch)
    from yandex_mcp.client import YandexAPIClient
    monkeypatch.setenv(
        "YANDEX_ACCOUNTS",
        json.dumps({"broken": {"client_login": "x"}}),  # missing direct_token
    )
    with pytest.raises(ValueError) as exc_info:
        YandexAPIClient()
    assert "Invalid account config" in str(exc_info.value) or "direct_token" in str(
        exc_info.value
    )
