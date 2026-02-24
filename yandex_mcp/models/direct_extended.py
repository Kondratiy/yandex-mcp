"""Extended Pydantic models for Yandex Direct API - Sitelinks, VCards, BidModifiers, etc."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import ResponseFormat


# =============================================================================
# Sitelinks Models
# =============================================================================

class GetSitelinksInput(BaseModel):
    """Input for getting sitelink sets."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    sitelink_set_ids: Optional[List[int]] = Field(
        default=None,
        description="Filter by specific sitelink set IDs"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum number of sitelink sets to return"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Offset for pagination"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class SitelinkItem(BaseModel):
    """Single sitelink item."""
    title: str = Field(..., max_length=30, description="Sitelink title (max 30 chars)")
    href: str = Field(..., description="Sitelink URL")
    description: Optional[str] = Field(default=None, max_length=60, description="Description (max 60 chars)")


class AddSitelinksInput(BaseModel):
    """Input for adding a sitelink set."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    sitelinks: List[SitelinkItem] = Field(
        ...,
        min_length=1,
        max_length=8,
        description="List of sitelinks (1-8 items)"
    )


class DeleteSitelinksInput(BaseModel):
    """Input for deleting sitelink sets."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    sitelink_set_ids: List[int] = Field(
        ...,
        min_length=1,
        description="Sitelink set IDs to delete"
    )


# =============================================================================
# VCards Models
# =============================================================================

class GetVCardsInput(BaseModel):
    """Input for getting vCards."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    vcard_ids: Optional[List[int]] = Field(
        default=None,
        description="Filter by specific vCard IDs"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum number of vCards to return"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Offset for pagination"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class AddVCardInput(BaseModel):
    """Input for adding a vCard."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    campaign_id: int = Field(..., description="Campaign ID for this vCard")
    company: str = Field(..., max_length=255, description="Company name")
    country_code: str = Field(default="+7", description="Phone country code (e.g., +7)")
    city_code: str = Field(..., description="Phone city code (e.g., 423 for Vladivostok)")
    phone_number: str = Field(..., description="Phone number without codes (e.g., 204-50-70)")
    phone_extension: Optional[str] = Field(default=None, description="Phone extension")
    country: str = Field(default="Россия", description="Country name")
    city: str = Field(..., description="City name")
    street: Optional[str] = Field(default=None, description="Street address")
    house: Optional[str] = Field(default=None, description="House number")
    work_time: Optional[str] = Field(default=None, description="Working hours (e.g., '0#3#10#00#18#00')")
    extra_message: Optional[str] = Field(default=None, max_length=200, description="Additional info")


class DeleteVCardsInput(BaseModel):
    """Input for deleting vCards."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    vcard_ids: List[int] = Field(
        ...,
        min_length=1,
        description="vCard IDs to delete"
    )


# =============================================================================
# BidModifiers Models
# =============================================================================

class GetBidModifiersInput(BaseModel):
    """Input for getting bid modifiers."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    campaign_ids: Optional[List[int]] = Field(
        default=None,
        description="Filter by campaign IDs"
    )
    adgroup_ids: Optional[List[int]] = Field(
        default=None,
        description="Filter by ad group IDs"
    )
    bid_modifier_ids: Optional[List[int]] = Field(
        default=None,
        description="Filter by specific bid modifier IDs"
    )
    types: Optional[List[str]] = Field(
        default=None,
        description="Filter by types: MOBILE_ADJUSTMENT, DESKTOP_ADJUSTMENT, DEMOGRAPHICS_ADJUSTMENT, etc."
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum number to return"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class MobileAdjustment(BaseModel):
    """Mobile bid adjustment."""
    bid_modifier: int = Field(..., ge=0, le=1300, description="Bid modifier percent (0-1300, 100=no change)")


class DesktopAdjustment(BaseModel):
    """Desktop bid adjustment."""
    bid_modifier: int = Field(..., ge=0, le=1300, description="Bid modifier percent (0-1300)")


class DemographicsAdjustment(BaseModel):
    """Demographics bid adjustment."""
    gender: Optional[str] = Field(default=None, description="GENDER_MALE or GENDER_FEMALE")
    age: Optional[str] = Field(default=None, description="AGE_0_17, AGE_18_24, AGE_25_34, AGE_35_44, AGE_45_54, AGE_55")
    bid_modifier: int = Field(..., ge=0, le=1300, description="Bid modifier percent")


class RegionalAdjustment(BaseModel):
    """Regional bid adjustment."""
    region_id: int = Field(..., description="Region ID")
    bid_modifier: int = Field(..., ge=10, le=1300, description="Bid modifier percent (10-1300)")


class AddBidModifierInput(BaseModel):
    """Input for adding bid modifiers."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    campaign_id: Optional[int] = Field(default=None, description="Campaign ID (for campaign-level modifier)")
    adgroup_id: Optional[int] = Field(default=None, description="Ad group ID (for group-level modifier)")

    mobile_adjustment: Optional[MobileAdjustment] = Field(default=None, description="Mobile device adjustment")
    desktop_adjustment: Optional[DesktopAdjustment] = Field(default=None, description="Desktop adjustment")
    demographics_adjustments: Optional[List[DemographicsAdjustment]] = Field(default=None, description="Demographics adjustments")
    regional_adjustments: Optional[List[RegionalAdjustment]] = Field(default=None, description="Regional adjustments")


class SetBidModifierInput(BaseModel):
    """Input for setting bid modifier value."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    bid_modifier_id: int = Field(..., description="Bid modifier ID")
    bid_modifier: int = Field(..., ge=0, le=1300, description="New bid modifier percent")


class DeleteBidModifiersInput(BaseModel):
    """Input for deleting bid modifiers."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    bid_modifier_ids: List[int] = Field(
        ...,
        min_length=1,
        description="Bid modifier IDs to delete"
    )


class ToggleBidModifiersInput(BaseModel):
    """Input for enabling/disabling bid modifiers."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    bid_modifier_ids: List[int] = Field(..., description="Bid modifier IDs")
    enabled: bool = Field(..., description="Enable (True) or disable (False)")


# =============================================================================
# RetargetingLists Models
# =============================================================================

class GetRetargetingListsInput(BaseModel):
    """Input for getting retargeting lists."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    retargeting_list_ids: Optional[List[int]] = Field(
        default=None,
        description="Filter by specific retargeting list IDs"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum number to return"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class RetargetingRule(BaseModel):
    """Single retargeting rule."""
    goal_id: int = Field(..., description="Metrika goal ID")
    member_of: str = Field(default="POSITIVE", description="POSITIVE or NEGATIVE")
    days: int = Field(default=30, ge=1, le=540, description="Days to look back (1-540)")


class AddRetargetingListInput(BaseModel):
    """Input for adding a retargeting list."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(..., max_length=255, description="Retargeting list name")
    rules: List[List[RetargetingRule]] = Field(
        ...,
        description="Rules groups (OR between groups, AND within group)"
    )
    description: Optional[str] = Field(default=None, description="Description")


class UpdateRetargetingListInput(BaseModel):
    """Input for updating a retargeting list."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    retargeting_list_id: int = Field(..., description="Retargeting list ID")
    name: Optional[str] = Field(default=None, max_length=255, description="New name")
    rules: Optional[List[List[RetargetingRule]]] = Field(default=None, description="New rules")
    description: Optional[str] = Field(default=None, description="New description")


class DeleteRetargetingListsInput(BaseModel):
    """Input for deleting retargeting lists."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    retargeting_list_ids: List[int] = Field(
        ...,
        min_length=1,
        description="Retargeting list IDs to delete"
    )


# =============================================================================
# AudienceTargets Models
# =============================================================================

class GetAudienceTargetsInput(BaseModel):
    """Input for getting audience targets."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    campaign_ids: Optional[List[int]] = Field(default=None, description="Filter by campaign IDs")
    adgroup_ids: Optional[List[int]] = Field(default=None, description="Filter by ad group IDs")
    audience_target_ids: Optional[List[int]] = Field(default=None, description="Filter by IDs")
    limit: int = Field(default=100, ge=1, le=10000)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class AddAudienceTargetInput(BaseModel):
    """Input for adding an audience target."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    adgroup_id: int = Field(..., description="Ad group ID")
    retargeting_list_id: int = Field(..., description="Retargeting list ID")
    interest_id: Optional[int] = Field(default=None, description="Interest category ID")
    context_bid: Optional[float] = Field(default=None, gt=0, description="Bid for context networks")


class ManageAudienceTargetsInput(BaseModel):
    """Input for managing audience targets (suspend/resume/delete)."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    audience_target_ids: List[int] = Field(..., min_length=1, description="Audience target IDs")


# =============================================================================
# NegativeKeywordSharedSets Models
# =============================================================================

class GetNegativeKeywordSharedSetsInput(BaseModel):
    """Input for getting negative keyword shared sets."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    shared_set_ids: Optional[List[int]] = Field(default=None, description="Filter by IDs")
    limit: int = Field(default=100, ge=1, le=10000)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class AddNegativeKeywordSharedSetInput(BaseModel):
    """Input for adding a negative keyword shared set."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(..., max_length=255, description="Set name")
    negative_keywords: List[str] = Field(..., min_length=1, description="Negative keywords")


class UpdateNegativeKeywordSharedSetInput(BaseModel):
    """Input for updating a negative keyword shared set."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    shared_set_id: int = Field(..., description="Shared set ID")
    name: Optional[str] = Field(default=None, max_length=255, description="New name")
    negative_keywords: Optional[List[str]] = Field(default=None, description="New negative keywords")


class DeleteNegativeKeywordSharedSetsInput(BaseModel):
    """Input for deleting negative keyword shared sets."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    shared_set_ids: List[int] = Field(..., min_length=1, description="Set IDs to delete")


# =============================================================================
# Dictionaries Models
# =============================================================================

class GetDictionariesInput(BaseModel):
    """Input for getting dictionaries."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    dictionary_names: List[str] = Field(
        ...,
        min_length=1,
        description="Dictionary names: GeoRegions, Currencies, TimeZones, Constants, AdCategories, OperationSystemVersions, ProductivityAssertions, SupplySidePlatforms, Interests, AudienceCriteriaTypes"
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


# =============================================================================
# Changes Models
# =============================================================================

class CheckCampaignChangesInput(BaseModel):
    """Input for checking campaign changes."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    campaign_ids: List[int] = Field(..., min_length=1, description="Campaign IDs to check")
    timestamp: str = Field(..., description="Timestamp from previous check (ISO 8601)")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class CheckAllChangesInput(BaseModel):
    """Input for checking all changes."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    timestamp: str = Field(..., description="Timestamp from previous check (ISO 8601)")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


# =============================================================================
# Clients Models
# =============================================================================


class GetClientInfoInput(BaseModel):
    """Input for getting client info."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)
