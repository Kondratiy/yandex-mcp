"""Pydantic models for Yandex AppMetrica API."""

import re
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import ResponseFormat

# Event names go straight into AppMetrica filter expressions like
# `ym:ce:eventLabel=='X'`. To prevent breakouts via embedded quotes
# we restrict to a safe charset (matches the same set AppMetrica SDK
# itself enforces for custom event names).
_EVENT_NAME_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")


def _validate_event_names(values: list[str]) -> list[str]:
    for name in values:
        if not _EVENT_NAME_RE.match(name):
            raise ValueError(
                f"Event name {name!r} contains unsafe characters; "
                f"only [A-Za-z0-9_.-] are allowed."
            )
    return values


# =============================================================================
# Enums
# =============================================================================

class AppMetricaGroupType(str, Enum):
    """Time grouping for AppMetrica reports."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    HOUR = "hour"
    MINUTE = "minute"


class LogsExportType(str, Enum):
    """Available Logs API export types."""
    CLICKS = "clicks"
    INSTALLATIONS = "installations"
    POSTBACKS = "postbacks"
    EVENTS = "events"
    SESSIONS_STARTS = "sessions_starts"
    CRASHES = "crashes"
    ERRORS = "errors"
    PUSH_TOKENS = "push_tokens"
    DEEPLINKS = "deeplinks"
    PROFILES = "profiles_v2"
    REVENUE_EVENTS = "revenue_events"
    ECOMMERCE_EVENTS = "ecommerce_events"
    AD_REVENUE_EVENTS = "ad_revenue_events"


# =============================================================================
# Management Models
# =============================================================================

class GetApplicationsInput(BaseModel):
    """Input for listing AppMetrica applications."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class GetApplicationInput(BaseModel):
    """Input for getting a single AppMetrica application."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_id: int = Field(..., description="Application ID in AppMetrica")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


# =============================================================================
# Reporting Models
# =============================================================================

class AppMetricaReportInput(BaseModel):
    """Input for AppMetrica table report."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_id: int = Field(..., description="Application ID in AppMetrica")
    metrics: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "Metric identifiers. All must share the same prefix. "
            "ym:ge: — users, sessions. "
            "ym:ce: — users. "
            "ym:i: — users, devices, installDevices. "
            "ym:cr: — users, crashes, crashDevices. "
            "ym:s: — users. ym:u: — users, devices. ym:p: — users, devices. "
            "Example: ['ym:ge:users', 'ym:ge:sessions']"
        ),
    )
    dimensions: list[str] | None = Field(
        default=None,
        description=(
            "Dimension identifiers for grouping (same prefix as metrics). "
            "ym:ge: — date, regionCountry, regionCity, operatingSystemInfo, "
            "mobileDeviceBranding, mobileDeviceModel, appVersion, gender, "
            "ageInterval, screenResolution. "
            "ym:ce: — eventLabel, eventType. "
            "ym:i: — date, regionCountry, operatingSystemInfo, "
            "mobileDeviceBranding, appVersion, publisher. "
            "ym:cr: — date, operatingSystemInfo, appVersion, "
            "crashGroupName, mobileDeviceBranding. "
            "ym:s: — date, regionCountry, operatingSystemInfo."
        ),
    )
    date1: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Start date in YYYY-MM-DD format",
    )
    date2: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="End date in YYYY-MM-DD format",
    )
    filters: str | None = Field(
        default=None,
        description="Filter expression for data segmentation",
    )
    sort: str | None = Field(
        default=None,
        description="Sort field. Prefix with '-' for descending",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=100000,
        description="Maximum number of rows to return",
    )
    offset: int = Field(
        default=1,
        ge=1,
        description="Offset for pagination (1-based)",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class AppMetricaByTimeInput(BaseModel):
    """Input for AppMetrica time-based report."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_id: int = Field(..., description="Application ID in AppMetrica")
    metrics: list[str] = Field(
        ...,
        min_length=1,
        description="Metric identifiers (e.g. ['ym:ge:users'])",
    )
    dimensions: list[str] | None = Field(
        default=None,
        description="Dimension identifiers for grouping",
    )
    date1: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Start date in YYYY-MM-DD format",
    )
    date2: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="End date in YYYY-MM-DD format",
    )
    group: AppMetricaGroupType = Field(
        default=AppMetricaGroupType.DAY,
        description="Time grouping: day, week, month, hour, minute",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class AppMetricaDrilldownInput(BaseModel):
    """Input for AppMetrica drilldown report."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_id: int = Field(..., description="Application ID in AppMetrica")
    metrics: list[str] = Field(
        ...,
        min_length=1,
        description="Metric identifiers",
    )
    dimensions: list[str] = Field(
        ...,
        min_length=1,
        description="Dimension identifiers for hierarchical grouping",
    )
    date1: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Start date in YYYY-MM-DD format",
    )
    date2: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="End date in YYYY-MM-DD format",
    )
    filters: str | None = Field(
        default=None,
        description="Filter expression",
    )
    parent_id: list[str] | None = Field(
        default=None,
        description="Parent ID for drilling down into a branch",
    )
    limit: int = Field(default=100, ge=1, le=100000)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


# =============================================================================
# Logs API Models
# =============================================================================

class AppMetricaLogsExportInput(BaseModel):
    """Input for AppMetrica Logs API export."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_id: int = Field(..., description="Application ID in AppMetrica")
    export_type: LogsExportType = Field(
        ...,
        description=(
            "Data type to export: clicks, installations, postbacks, events, "
            "sessions_starts, crashes, errors, push_tokens, deeplinks, "
            "profiles_v2, revenue_events, ecommerce_events, ad_revenue_events"
        ),
    )
    date_since: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}",
        description="Start date/datetime (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)",
    )
    date_until: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}",
        description="End date/datetime (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)",
    )
    fields: list[str] | None = Field(
        default=None,
        description="Specific fields to include in export. If empty, all fields returned.",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


# =============================================================================
# Events & Analytics Models
# =============================================================================

class AppMetricaEventsInput(BaseModel):
    """Input for getting event statistics."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_id: int = Field(..., description="Application ID in AppMetrica")
    date1: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Start date in YYYY-MM-DD format",
    )
    date2: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="End date in YYYY-MM-DD format",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=100000,
        description="Maximum number of events to return",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class AppMetricaProfilesInput(BaseModel):
    """Input for exporting user profiles."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_id: int = Field(..., description="Application ID in AppMetrica")
    date_since: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}",
        description="Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)",
    )
    date_until: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}",
        description="End date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)",
    )
    fields: list[str] | None = Field(
        default=None,
        description=(
            "Specific profile fields. Defaults to: appmetrica_device_id, "
            "profile_id, os_name, device_manufacturer, device_model, city, country_iso_code"
        ),
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class AppMetricaCrashesInput(BaseModel):
    """Input for getting crash statistics."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_id: int = Field(..., description="Application ID in AppMetrica")
    date1: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Start date in YYYY-MM-DD format",
    )
    date2: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="End date in YYYY-MM-DD format",
    )
    group_by: list[str] | None = Field(
        default=None,
        description=(
            "Dimensions to group crashes by. "
            "Examples: ym:cr:operatingSystemInfo, ym:cr:appVersion, "
            "ym:cr:crashGroupName, ym:cr:mobileDeviceBranding"
        ),
    )
    limit: int = Field(default=100, ge=1, le=100000)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class AppMetricaFunnelInput(BaseModel):
    """Input for building a conversion funnel from events."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_id: int = Field(..., description="Application ID in AppMetrica")
    steps: list[str] = Field(
        ...,
        min_length=2,
        max_length=10,
        description=(
            "Ordered list of event names representing funnel steps. "
            "Example: ['app_open', 'view_catalog', 'add_to_cart', 'purchase']"
        ),
    )

    @field_validator("steps")
    @classmethod
    def _check_steps(cls, v: list[str]) -> list[str]:
        return _validate_event_names(v)

    date_since: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}",
        description="Start date (YYYY-MM-DD)",
    )
    date_until: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}",
        description="End date (YYYY-MM-DD)",
    )
    publisher_filter: str | None = Field(
        default=None,
        description=(
            "Restrict the funnel to users whose attributed install came "
            "from this AppMetrica publisher (exact match against "
            "publisher_name from installations log). "
            "Example: 'Yandex.Direct', 'Organic'. "
            "When set, install log is also fetched and devices are "
            "intersected by appmetrica_device_id."
        ),
    )
    tracker_filter: str | None = Field(
        default=None,
        description=(
            "Restrict the funnel to users whose attributed install tracker "
            "name contains this substring (case-sensitive). "
            "Combine with publisher_filter for tighter scoping."
        ),
    )
    max_wait_seconds: int = Field(
        default=600,
        ge=60,
        le=1800,
        description=(
            "Logs API is asynchronous; how long to wait for the report "
            "to be prepared. Default 10 min, max 30 min."
        ),
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class AttributionAggregateBy(str, Enum):
    """Grouping axis for attribution_join report."""
    PUBLISHER = "publisher"
    TRACKER_NAME = "tracker_name"
    PUBLISHER_AND_TRACKER = "publisher_and_tracker"


class InstallAttributionAxis(str, Enum):
    """Grouping axis for live install_attribution Reporting API report."""
    PUBLISHER = "publisher"
    PUBLISHER_AND_CAMPAIGN = "publisher_and_campaign"


class AppMetricaInstallAttributionInput(BaseModel):
    """Input for live install attribution via Reporting API.

    Faster cousin of appmetrica_attribution_join: builds N+1 Reporting
    API queries (1 baseline + 1 per conversion event) and aggregates
    them into a single table — no Logs API polling, results in seconds.

    Mechanism: AppMetrica Reporting API allows mixing the install
    namespace (ym:i:devices grouped by ym:i:publisher,ym:i:campaign)
    with cross-prefix event filters in `filters=` (but NOT in
    dimensions=). So for each conversion event we send the same
    grouping with an extra filter `ym:ce:eventLabel=='X'` and divide
    the resulting devices count by the baseline.

    Doesn't return revenue (need ym:rev: which is unrelated to ym:i:)
    or click_url_parameters (only logs have them). For those, use
    appmetrica_attribution_join.
    """
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_id: int = Field(..., description="Application ID in AppMetrica")
    date1: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Start date (YYYY-MM-DD)",
    )
    date2: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="End date (YYYY-MM-DD)",
    )
    conversion_events: list[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description=(
            "List of event names to compute conversion rates for. "
            "Each becomes one extra parallel API call. "
            "Example: ['registration_send', 'subscribe_success']"
        ),
    )

    @field_validator("conversion_events")
    @classmethod
    def _check_conversion_events(cls, v: list[str]) -> list[str]:
        return _validate_event_names(v)

    aggregate_by: InstallAttributionAxis = Field(
        default=InstallAttributionAxis.PUBLISHER_AND_CAMPAIGN,
        description=(
            "Group by ym:i:publisher only, or by "
            "(ym:i:publisher, ym:i:campaign) — campaign is the "
            "AppMetrica tracker name."
        ),
    )
    publisher_filter: str | None = Field(
        default=None,
        description=(
            "Filter rows post-hoc by exact publisher name match. "
            "Cannot be sent to API filters= (combining ym:i:publisher "
            "with ym:ce:eventLabel triggers error 4009), so the tool "
            "fetches all publishers and filters in code. "
            "Example: 'Yandex.Direct'."
        ),
    )
    top_n: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Show top N groups by install count.",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class AppMetricaAttributionInput(BaseModel):
    """Input for joining installs × events × revenue by appmetrica_device_id.

    Pulls 2-3 Logs API exports in parallel (installations + events,
    optionally + revenue_events), joins them locally on
    appmetrica_device_id and returns a per-publisher / per-tracker
    breakdown of installs, conversion events and revenue.

    Use case: "which Yandex.Direct campaign drove not just installs
    but registrations and purchases?" — pick aggregate_by=tracker_name
    and look at the conversion column for your conversion events.
    """
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_id: int = Field(..., description="Application ID in AppMetrica")
    date_since: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}",
        description="Start date (YYYY-MM-DD)",
    )
    date_until: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}",
        description="End date (YYYY-MM-DD)",
    )
    conversion_events: list[str] | None = Field(
        default=None,
        description=(
            "List of event names to count per publisher/tracker. "
            "If omitted, all events are included (heavier output). "
            "Example: ['registration_send', 'subscribe_success']"
        ),
    )

    @field_validator("conversion_events")
    @classmethod
    def _check_conversion_events(
        cls, v: list[str] | None
    ) -> list[str] | None:
        if v is None:
            return None
        return _validate_event_names(v)

    aggregate_by: AttributionAggregateBy = Field(
        default=AttributionAggregateBy.TRACKER_NAME,
        description=(
            "Group by AppMetrica publisher_name, tracker_name, or "
            "the (publisher, tracker) pair."
        ),
    )
    include_revenue: bool = Field(
        default=False,
        description=(
            "Also pull revenue_events log and sum revenue per group. "
            "Adds ~30s-2min to runtime."
        ),
    )
    publisher_filter: str | None = Field(
        default=None,
        description=(
            "Pre-filter installs by publisher_name (exact match). "
            "Example: 'Yandex.Direct'."
        ),
    )
    tracker_filter: str | None = Field(
        default=None,
        description=(
            "Pre-filter installs by tracker_name substring. "
            "Combine with publisher_filter for tighter scoping."
        ),
    )
    top_n: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Show top N groups by install count.",
    )
    max_wait_seconds: int = Field(
        default=900,
        ge=60,
        le=1800,
        description=(
            "Per-export timeout for Logs API polling. "
            "Default 15 min, max 30 min."
        ),
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


# =============================================================================
# Push API Models
# =============================================================================

class CreatePushGroupInput(BaseModel):
    """Input for creating a push notification group."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_id: int = Field(..., description="Application ID in AppMetrica")
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique group name for organizing push sendings",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class GetPushStatusInput(BaseModel):
    """Input for checking push sending status."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    transfer_id: int = Field(..., description="Transfer ID returned from send-batch")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )
