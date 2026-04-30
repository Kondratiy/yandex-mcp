"""Pydantic models for Yandex Wordstat API."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from .common import ResponseFormat, AccountInput


class WordstatTopRequestsInput(AccountInput):
    """Input for getting popular search queries."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    phrase: Optional[str] = Field(default=None, description="Single phrase to search")
    phrases: Optional[List[str]] = Field(default=None, max_length=128, description="Multiple phrases (max 128)")
    num_phrases: int = Field(default=50, ge=1, le=2000, description="Number of results per phrase")
    regions: Optional[List[int]] = Field(default=None, description="Region IDs to filter")
    devices: Optional[List[str]] = Field(default=None, description="Device filter: all, desktop, phone, tablet")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' or 'json'")


class WordstatDynamicsInput(AccountInput):
    """Input for query frequency dynamics over time."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    phrase: str = Field(..., description="Query phrase (only + operator allowed)")
    period: str = Field(default="monthly", description="Period: monthly, weekly, or daily")
    from_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Start date (YYYY-MM-DD)")
    to_date: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="End date (YYYY-MM-DD)")
    regions: Optional[List[int]] = Field(default=None, description="Region IDs to filter")
    devices: Optional[List[str]] = Field(default=None, description="Device filter: all, desktop, phone, tablet")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


class WordstatRegionsInput(AccountInput):
    """Input for regional distribution of queries."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    phrase: str = Field(..., description="Query phrase")
    region_type: str = Field(default="all", description="Region granularity: cities, regions, or all")
    devices: Optional[List[str]] = Field(default=None, description="Device filter")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


class WordstatRegionsTreeInput(AccountInput):
    """Input for getting the regions tree."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class WordstatUserInfoInput(AccountInput):
    """Input for getting user quota info."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
