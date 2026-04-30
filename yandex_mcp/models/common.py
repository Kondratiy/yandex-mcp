"""Common models shared across Direct and Metrika."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class AccountInput(BaseModel):
    """Mixin: lets tool input models select which Yandex account to use.

    All top-level tool input models should inherit from this instead of BaseModel
    to expose an optional `account` parameter. The chosen account name must match
    one of the keys in YANDEX_ACCOUNTS env (or be omitted to use the default
    account = first one in the dict).
    """
    account: Optional[str] = Field(
        default=None,
        description=(
            "Account name (a key from YANDEX_ACCOUNTS env). "
            "If omitted, uses the first/default account. "
            "Example: account=\"main\""
        ),
    )
