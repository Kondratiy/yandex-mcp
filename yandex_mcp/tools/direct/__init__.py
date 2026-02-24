"""Yandex Direct tools registration."""

from mcp.server.fastmcp import FastMCP


def register_direct_tools(mcp: FastMCP) -> None:
    """Register all Yandex Direct tools."""
    from . import (
        campaigns,
        adgroups,
        ads,
        keywords,
        stats,
        sitelinks,
        vcards,
        bidmodifiers,
        retargeting,
        dictionaries,
        negative_keywords_shared,
        clients,
        adextensions,
        advideos,
        creatives,
        feeds,
        smartadtargets,
    )

    # Core tools
    campaigns.register(mcp)
    adgroups.register(mcp)
    ads.register(mcp)
    keywords.register(mcp)
    stats.register(mcp)

    # Extended tools
    sitelinks.register(mcp)
    vcards.register(mcp)
    bidmodifiers.register(mcp)
    retargeting.register(mcp)
    dictionaries.register(mcp)
    negative_keywords_shared.register(mcp)
    clients.register(mcp)
    adextensions.register(mcp)
    advideos.register(mcp)
    creatives.register(mcp)
    feeds.register(mcp)
    smartadtargets.register(mcp)
