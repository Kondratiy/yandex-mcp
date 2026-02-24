"""Yandex Metrika tools registration."""

from mcp.server.fastmcp import FastMCP


def register_metrika_tools(mcp: FastMCP) -> None:
    """Register all Yandex Metrika tools."""
    from . import (
        counters,
        goals,
        reports,
        segments,
        filters,
        grants,
        offline,
        labels,
    )

    # Core tools
    counters.register(mcp)
    goals.register(mcp)
    reports.register(mcp)
    segments.register(mcp)
    filters.register(mcp)
    grants.register(mcp)

    # Extended tools
    offline.register(mcp)
    labels.register(mcp)
