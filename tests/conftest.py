"""Shared fixtures for Yandex MCP tests."""

import os
import pytest

# Set a dummy token on module load — BEFORE pytest collects test files that
# may trigger `import yandex_mcp` (which constructs the api_client singleton
# at module top level using current env). Tests that need a clean env can
# override / delete this via monkeypatch.delenv inside the test body.
os.environ.setdefault("YANDEX_TOKEN", "test-token-for-registration")

# Eagerly import client module so api_client singleton is constructed once
# with the dummy token above, before any test body has a chance to clear env.
# After this, tests that import YandexAPIClient class get the cached module
# from sys.modules (no re-execution), and they construct fresh instances of
# the class manually with whatever env they want.
import yandex_mcp.client  # noqa: E402, F401


@pytest.fixture(autouse=True)
def _set_dummy_token(monkeypatch):
    """Provide a dummy token for any test that doesn't manage env itself."""
    monkeypatch.setenv("YANDEX_TOKEN", "test-token-for-registration")


@pytest.fixture
def mcp_instance():
    """Return a fresh FastMCP instance with all tools registered."""
    from yandex_mcp import mcp
    return mcp
