"""Tools registration for Yandex MCP Server."""

from mcp.server.fastmcp import FastMCP


def register_all_tools(mcp: FastMCP) -> None:
    """Register all Direct and Metrika tools."""
    from .direct import register_direct_tools
    from .metrika import register_metrika_tools

    register_direct_tools(mcp)
    register_metrika_tools(mcp)
