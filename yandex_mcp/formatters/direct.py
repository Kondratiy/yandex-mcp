"""Markdown formatters for Yandex Direct responses."""

from typing import Dict, List


def format_campaigns_markdown(campaigns: List[Dict]) -> str:
    """Format campaigns list as markdown."""
    if not campaigns:
        return "No campaigns found."

    lines = ["# Campaigns\n"]
    for camp in campaigns:
        lines.append(f"## {camp.get('Name', 'Unnamed')} (ID: {camp.get('Id')})")
        lines.append(f"- **Type**: {camp.get('Type', 'N/A')}")
        lines.append(f"- **State**: {camp.get('State', 'N/A')}")
        lines.append(f"- **Status**: {camp.get('Status', 'N/A')}")

        if camp.get("DailyBudget"):
            budget = camp["DailyBudget"]
            amount = budget.get("Amount", 0) / 1_000_000
            lines.append(f"- **Daily Budget**: {amount:.2f} ({budget.get('Mode', 'N/A')})")

        if camp.get("Statistics"):
            stats = camp["Statistics"]
            lines.append(f"- **Clicks**: {stats.get('Clicks', 0)}")
            lines.append(f"- **Impressions**: {stats.get('Impressions', 0)}")

        lines.append("")

    return "\n".join(lines)


def format_adgroups_markdown(groups: List[Dict]) -> str:
    """Format ad groups list as markdown."""
    if not groups:
        return "No ad groups found."

    lines = ["# Ad Groups\n"]
    for group in groups:
        lines.append(f"## {group.get('Name', 'Unnamed')} (ID: {group.get('Id')})")
        lines.append(f"- **Campaign ID**: {group.get('CampaignId')}")
        lines.append(f"- **Type**: {group.get('Type', 'N/A')}")
        lines.append(f"- **Status**: {group.get('Status', 'N/A')}")

        region_ids = group.get("RegionIds", [])
        if region_ids:
            lines.append(f"- **Regions**: {', '.join(map(str, region_ids))}")

        lines.append("")

    return "\n".join(lines)


def format_ads_markdown(ads: List[Dict]) -> str:
    """Format ads list as markdown."""
    if not ads:
        return "No ads found."

    lines = ["# Ads\n"]
    for ad in ads:
        ad_id = ad.get("Id")
        lines.append(f"## Ad ID: {ad_id}")
        lines.append(f"- **AdGroup ID**: {ad.get('AdGroupId')}")
        lines.append(f"- **Campaign ID**: {ad.get('CampaignId')}")
        lines.append(f"- **State**: {ad.get('State', 'N/A')}")
        lines.append(f"- **Status**: {ad.get('Status', 'N/A')}")

        if ad.get("TextAd"):
            text_ad = ad["TextAd"]
            lines.append(f"- **Title**: {text_ad.get('Title', 'N/A')}")
            lines.append(f"- **Title2**: {text_ad.get('Title2', 'N/A')}")
            lines.append(f"- **Text**: {text_ad.get('Text', 'N/A')}")
            lines.append(f"- **Href**: {text_ad.get('Href', 'N/A')}")

        lines.append("")

    return "\n".join(lines)


def format_keywords_markdown(keywords: List[Dict]) -> str:
    """Format keywords list as markdown."""
    if not keywords:
        return "No keywords found."

    lines = ["# Keywords\n"]
    for kw in keywords:
        lines.append(f"## {kw.get('Keyword', 'N/A')} (ID: {kw.get('Id')})")
        lines.append(f"- **AdGroup ID**: {kw.get('AdGroupId')}")
        lines.append(f"- **State**: {kw.get('State', 'N/A')}")
        lines.append(f"- **Status**: {kw.get('Status', 'N/A')}")

        bid = kw.get("Bid", 0)
        if bid:
            lines.append(f"- **Bid**: {bid / 1_000_000:.2f}")

        lines.append("")

    return "\n".join(lines)
