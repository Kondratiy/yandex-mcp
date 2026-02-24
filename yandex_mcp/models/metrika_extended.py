"""Extended Pydantic models for Yandex Metrika API - Offline Conversions, Calls, Labels, etc."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import ResponseFormat


# =============================================================================
# Offline Conversions Models
# =============================================================================

class OfflineConversion(BaseModel):
    """Single offline conversion record."""
    client_id: Optional[str] = Field(default=None, description="ClientID from Metrika")
    user_id: Optional[str] = Field(default=None, description="UserID set by site owner")
    yclid: Optional[str] = Field(default=None, description="Click ID from Yandex Direct")
    date_time: int = Field(..., description="Conversion timestamp (Unix Time, UTC+0)")
    target: str = Field(..., description="Goal identifier")
    price: Optional[float] = Field(default=None, description="Conversion value/revenue")
    currency: Optional[str] = Field(default=None, description="Currency code (RUB, USD, EUR)")
    order_id: Optional[str] = Field(default=None, description="Order ID")


class UploadOfflineConversionsInput(BaseModel):
    """Input for uploading offline conversions."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(..., description="Metrika counter ID")
    client_id_type: str = Field(
        default="CLIENT_ID",
        description="ID type: CLIENT_ID, USER_ID, or YCLID"
    )
    conversions: List[OfflineConversion] = Field(
        ...,
        min_length=1,
        description="List of conversions to upload"
    )


class GetOfflineConversionsUploadingsInput(BaseModel):
    """Input for getting offline conversions uploadings status."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(..., description="Metrika counter ID")
    limit: int = Field(default=100, ge=1, le=1000)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


# =============================================================================
# Calls Models
# =============================================================================

class CallRecord(BaseModel):
    """Single call record."""
    client_id: Optional[str] = Field(default=None, description="ClientID from Metrika")
    user_id: Optional[str] = Field(default=None, description="UserID set by site owner")
    yclid: Optional[str] = Field(default=None, description="Click ID from Yandex Direct")
    date_time: int = Field(..., description="Call timestamp (Unix Time, UTC+0)")
    phone_number: Optional[str] = Field(default=None, description="Phone number called")
    talk_duration: Optional[int] = Field(default=None, description="Call duration in seconds")
    call_missed: bool = Field(default=False, description="Whether the call was missed")
    tag: Optional[str] = Field(default=None, description="Call tag/label")
    first_time_caller: bool = Field(default=True, description="First time caller")
    url: Optional[str] = Field(default=None, description="Page URL where call originated")


class UploadCallsInput(BaseModel):
    """Input for uploading call data."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(..., description="Metrika counter ID")
    client_id_type: str = Field(
        default="CLIENT_ID",
        description="ID type: CLIENT_ID, USER_ID, or YCLID"
    )
    calls: List[CallRecord] = Field(
        ...,
        min_length=1,
        description="List of calls to upload"
    )
    new_goal_name: Optional[str] = Field(
        default=None,
        description="Name for auto-created goal for calls"
    )


# =============================================================================
# Expenses Models
# =============================================================================

class ExpenseRecord(BaseModel):
    """Single expense record."""
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date (YYYY-MM-DD)")
    utm_source: str = Field(..., description="UTM source")
    utm_medium: Optional[str] = Field(default=None, description="UTM medium")
    utm_campaign: Optional[str] = Field(default=None, description="UTM campaign")
    utm_content: Optional[str] = Field(default=None, description="UTM content")
    utm_term: Optional[str] = Field(default=None, description="UTM term")
    expenses: float = Field(..., ge=0, description="Expense amount")
    currency: str = Field(default="RUB", description="Currency code")
    clicks: Optional[int] = Field(default=None, ge=0, description="Number of clicks")
    impressions: Optional[int] = Field(default=None, ge=0, description="Number of impressions")


class UploadExpensesInput(BaseModel):
    """Input for uploading expense data."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(..., description="Metrika counter ID")
    expenses: List[ExpenseRecord] = Field(
        ...,
        min_length=1,
        description="List of expense records"
    )


# =============================================================================
# User Parameters Models
# =============================================================================

class UserParameter(BaseModel):
    """Single user parameter record."""
    client_id: Optional[str] = Field(default=None, description="ClientID from Metrika")
    user_id: Optional[str] = Field(default=None, description="UserID set by site owner")
    params: Dict[str, Any] = Field(..., description="User parameters as key-value pairs")


class UploadUserParametersInput(BaseModel):
    """Input for uploading user parameters."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(..., description="Metrika counter ID")
    client_id_type: str = Field(
        default="CLIENT_ID",
        description="ID type: CLIENT_ID or USER_ID"
    )
    users: List[UserParameter] = Field(
        ...,
        min_length=1,
        description="List of user parameter records"
    )


# =============================================================================
# Labels Models
# =============================================================================

class GetLabelsInput(BaseModel):
    """Input for getting labels."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class CreateLabelInput(BaseModel):
    """Input for creating a label."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(..., min_length=1, max_length=255, description="Label name")


class UpdateLabelInput(BaseModel):
    """Input for updating a label."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    label_id: int = Field(..., description="Label ID")
    name: str = Field(..., min_length=1, max_length=255, description="New label name")


class DeleteLabelInput(BaseModel):
    """Input for deleting a label."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    label_id: int = Field(..., description="Label ID to delete")


class LinkCounterToLabelInput(BaseModel):
    """Input for linking counter to label."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(..., description="Counter ID")
    label_id: int = Field(..., description="Label ID")


# =============================================================================
# Chart Annotations Models
# =============================================================================

class GetAnnotationsInput(BaseModel):
    """Input for getting chart annotations."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(..., description="Counter ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class CreateAnnotationInput(BaseModel):
    """Input for creating a chart annotation."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(..., description="Counter ID")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date (YYYY-MM-DD)")
    title: str = Field(..., max_length=255, description="Annotation title")
    message: Optional[str] = Field(default=None, description="Annotation message")
    group: Optional[str] = Field(default=None, description="Annotation group")


class UpdateAnnotationInput(BaseModel):
    """Input for updating a chart annotation."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(..., description="Counter ID")
    annotation_id: int = Field(..., description="Annotation ID")
    title: Optional[str] = Field(default=None, max_length=255, description="New title")
    message: Optional[str] = Field(default=None, description="New message")


class DeleteAnnotationInput(BaseModel):
    """Input for deleting a chart annotation."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    counter_id: int = Field(..., description="Counter ID")
    annotation_id: int = Field(..., description="Annotation ID to delete")


# =============================================================================
# Delegates Models
# =============================================================================

class GetDelegatesInput(BaseModel):
    """Input for getting delegates."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class AddDelegateInput(BaseModel):
    """Input for adding a delegate."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    user_login: str = Field(..., description="User login to add as delegate")
    comment: Optional[str] = Field(default=None, description="Optional comment")


class DeleteDelegateInput(BaseModel):
    """Input for deleting a delegate."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    user_login: str = Field(..., description="User login to remove")
