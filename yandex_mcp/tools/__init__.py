"""Tools registration for Yandex MCP Server."""

from mcp.server.fastmcp import FastMCP


def register_all_tools(mcp: FastMCP) -> None:
    """Register all Direct, Metrika, and AppMetrica tools.

    Note: Yandex Wordstat tools are deprecated and disabled by default.
    The legacy Wordstat REST API (api.wordstat.yandex.net) is being
    superseded by the new Yandex Cloud Search API:
    https://aistudio.yandex.ru/docs/ru/search-api/concepts/wordstat
    which uses IAM-token auth (different from Direct OAuth) and lives
    under a different endpoint. Source code for the old integration is
    preserved (yandex_mcp/tools/wordstat.py + the related models/
    formatters/client helpers) — uncomment the two `wordstat` lines
    below if you still have legacy access. A fresh integration against
    Yandex Cloud Search API would be a separate tool family.
    """
    from .direct import register_direct_tools
    from .metrika import register_metrika_tools
    from .appmetrica import register_appmetrica_tools
    # from . import wordstat  # deprecated — see docstring above

    register_direct_tools(mcp)
    register_metrika_tools(mcp)
    # wordstat.register(mcp)  # deprecated — see docstring above
    register_appmetrica_tools(mcp)
