"""
Yandex MCP Server - MCP server for Yandex Direct and Yandex Metrika APIs.

This server provides tools for managing advertising campaigns in Yandex Direct
and analyzing website statistics in Yandex Metrika through the Model Context Protocol.
"""

from mcp.server.fastmcp import FastMCP

from .tools import register_all_tools

__version__ = "1.1.0"

# Initialize MCP Server
mcp = FastMCP("yandex_mcp")

# Register all tools
register_all_tools(mcp)


def run():
    """Run the MCP server."""
    mcp.run()


__all__ = ["mcp", "run", "__version__"]
