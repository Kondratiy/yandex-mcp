"""Pydantic models for Yandex Metrika API."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import ResponseFormat


# =============================================================================
# Enums
# =============================================================================

class MetrikaGroupType(str, Enum):
    """Time grouping for Metrika reports."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    HOUR = "hour"
    MINUTE = "minute"


class GoalType(str, Enum):
    """Goal type for Metrika."""
    URL = "url"
    ACTION = "action"
    PHONE = "phone"
    EMAIL = "email"
    MESSENGER = "messenger"
    FILE = "file"
    SOCIAL = "social"
    FORM = "form"
    BUTTON = "button"


class FilterType(str, Enum):
    """Filter type for Metrika."""
    ONLY_MIRRORS = "only_mirrors"
    UNIQ_ID = "uniq_id"
    URL_PARAM = "url_param"
    TITLE = "title"
    REFERER = "referer"
    INTERVAL = "interval"
    CLIENT_ID = "client_id"


class FilterAction(str, Enum):
    """Filter action."""
    INCLUDE = "include"
    EXCLUDE = "exclude"


class FilterStatus(str, Enum):
    """Filter status."""
    ACTIVE = "active"
    DISABLED = "disabled"


class GrantPermission(str, Enum):
    """Grant permission level."""
    VIEW = "view"
    EDIT = "edit"


# =============================================================================
# Counter Models
# =============================================================================

class GetCountersInput(BaseModel):
    """Input for getting Metrika counters."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    favorite: Optional[bool] = Field(
        default=None,
        description="Filter by favorite status"
    )
    search_string: Optional[str] = Field(
        default=None,
        description="Search string to filter counters by name or site"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class GetCounterInput(BaseModel):
    """Input for getting single counter details."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class CreateCounterInput(BaseModel):
    """Input for creating a Metrika counter."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Counter name"
    )
    site: str = Field(
        ...,
        description="Website URL"
    )


class UpdateCounterInput(BaseModel):
    """Input for updating a Metrika counter."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="New counter name"
    )
    site: Optional[str] = Field(
        default=None,
        description="New website URL"
    )
    favorite: Optional[bool] = Field(
        default=None,
        description="Mark as favorite"
    )


# =============================================================================
# Goal Models
# =============================================================================

class GetGoalsInput(BaseModel):
    """Input for getting counter goals."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class CreateGoalInput(BaseModel):
    """Input for creating a goal."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Goal name"
    )
    goal_type: str = Field(
        ...,
        description="Goal type: url, action, phone, email, messenger, etc."
    )
    conditions: List[Dict[str, str]] = Field(
        ...,
        description="Goal conditions, e.g., [{'type': 'exact', 'url': '/thank-you'}]"
    )


class UpdateGoalInput(BaseModel):
    """Input for updating a goal."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    goal_id: int = Field(
        ...,
        description="Goal ID to update"
    )
    name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="New goal name"
    )
    conditions: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="New goal conditions"
    )


class DeleteGoalInput(BaseModel):
    """Input for deleting a goal."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    goal_id: int = Field(
        ...,
        description="Goal ID to delete"
    )


# =============================================================================
# Segment Models (NEW)
# =============================================================================

class GetSegmentsInput(BaseModel):
    """Input for getting segments."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class CreateSegmentInput(BaseModel):
    """Input for creating a segment."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Segment name"
    )
    expression: str = Field(
        ...,
        description="Segment filter expression (e.g., ym:s:trafficSource=='organic')"
    )


class UpdateSegmentInput(BaseModel):
    """Input for updating a segment."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    segment_id: int = Field(
        ...,
        description="Segment ID to update"
    )
    name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="New segment name"
    )
    expression: Optional[str] = Field(
        default=None,
        description="New segment filter expression"
    )


class DeleteSegmentInput(BaseModel):
    """Input for deleting a segment."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    segment_id: int = Field(
        ...,
        description="Segment ID to delete"
    )


# =============================================================================
# Filter Models (NEW)
# =============================================================================

class GetFiltersInput(BaseModel):
    """Input for getting filters."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class CreateFilterInput(BaseModel):
    """Input for creating a filter."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    attr: str = Field(
        ...,
        description="Filter attribute: url, referer, uniq_id, client_ip, title"
    )
    type: str = Field(
        ...,
        description="Filter type: only_mirrors, uniq_id, url_param, title, referer, interval"
    )
    value: str = Field(
        ...,
        description="Filter value"
    )
    action: FilterAction = Field(
        default=FilterAction.EXCLUDE,
        description="Filter action: include or exclude"
    )
    status: FilterStatus = Field(
        default=FilterStatus.ACTIVE,
        description="Filter status: active or disabled"
    )


class UpdateFilterInput(BaseModel):
    """Input for updating a filter."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    filter_id: int = Field(
        ...,
        description="Filter ID to update"
    )
    value: Optional[str] = Field(
        default=None,
        description="New filter value"
    )
    action: Optional[FilterAction] = Field(
        default=None,
        description="New filter action"
    )
    status: Optional[FilterStatus] = Field(
        default=None,
        description="New filter status"
    )


class DeleteFilterInput(BaseModel):
    """Input for deleting a filter."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    filter_id: int = Field(
        ...,
        description="Filter ID to delete"
    )


# =============================================================================
# Grant (Access) Models (NEW)
# =============================================================================

class GetGrantsInput(BaseModel):
    """Input for getting counter access grants."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class GrantInput(BaseModel):
    """Input for managing counter access grants."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    user_login: str = Field(
        ...,
        description="User login to grant/revoke access"
    )
    permission: GrantPermission = Field(
        default=GrantPermission.VIEW,
        description="Permission level: view or edit"
    )
    comment: Optional[str] = Field(
        default=None,
        description="Optional comment for this grant"
    )


class DeleteGrantInput(BaseModel):
    """Input for deleting a grant."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    user_login: str = Field(
        ...,
        description="User login to revoke access from"
    )


# =============================================================================
# Report Models
# =============================================================================

class MetrikaReportInput(BaseModel):
    """Input for Metrika statistics report."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    metrics: List[str] = Field(
        default_factory=lambda: ["ym:s:visits", "ym:s:users", "ym:s:bounceRate"],
        description="Metrics to retrieve (e.g., ym:s:visits, ym:s:users, ym:s:pageviews)"
    )
    dimensions: Optional[List[str]] = Field(
        default=None,
        description="Dimensions for grouping (e.g., ym:s:date, ym:s:trafficSource)"
    )
    date1: Optional[str] = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Start date (YYYY-MM-DD), defaults to 7 days ago"
    )
    date2: Optional[str] = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="End date (YYYY-MM-DD), defaults to today"
    )
    filters: Optional[str] = Field(
        default=None,
        description="Filter expression (e.g., ym:s:trafficSource=='organic')"
    )
    sort: Optional[str] = Field(
        default=None,
        description="Sort field with optional '-' prefix for descending"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=100000,
        description="Maximum rows to return"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class MetrikaByTimeInput(BaseModel):
    """Input for time-based Metrika report."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    metrics: List[str] = Field(
        default_factory=lambda: ["ym:s:visits"],
        description="Metrics to retrieve"
    )
    dimensions: Optional[List[str]] = Field(
        default=None,
        description="Dimensions for grouping"
    )
    date1: Optional[str] = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Start date (YYYY-MM-DD)"
    )
    date2: Optional[str] = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="End date (YYYY-MM-DD)"
    )
    group: MetrikaGroupType = Field(
        default=MetrikaGroupType.DAY,
        description="Time grouping: day, week, month, quarter, year, hour, minute"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class MetrikaComparisonInput(BaseModel):
    """Input for segment comparison report (NEW)."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    metrics: List[str] = Field(
        default_factory=lambda: ["ym:s:visits", "ym:s:users"],
        description="Metrics to compare"
    )
    dimensions: Optional[List[str]] = Field(
        default=None,
        description="Dimensions for grouping"
    )
    date1_a: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Segment A start date (YYYY-MM-DD)"
    )
    date2_a: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Segment A end date (YYYY-MM-DD)"
    )
    date1_b: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Segment B start date (YYYY-MM-DD)"
    )
    date2_b: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Segment B end date (YYYY-MM-DD)"
    )
    filters_a: Optional[str] = Field(
        default=None,
        description="Filter for segment A"
    )
    filters_b: Optional[str] = Field(
        default=None,
        description="Filter for segment B"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=100000,
        description="Maximum rows to return"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class MetrikaDrilldownInput(BaseModel):
    """Input for drilldown report (NEW)."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(
        ...,
        description="Metrika counter ID"
    )
    metrics: List[str] = Field(
        default_factory=lambda: ["ym:s:visits", "ym:s:users"],
        description="Metrics to retrieve"
    )
    dimensions: List[str] = Field(
        ...,
        min_length=1,
        description="Dimensions for drilldown (hierarchical)"
    )
    date1: Optional[str] = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Start date (YYYY-MM-DD)"
    )
    date2: Optional[str] = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="End date (YYYY-MM-DD)"
    )
    filters: Optional[str] = Field(
        default=None,
        description="Filter expression"
    )
    parent_id: Optional[List[str]] = Field(
        default=None,
        description="Parent IDs for drilldown into specific branches"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=100000,
        description="Maximum rows to return"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )
