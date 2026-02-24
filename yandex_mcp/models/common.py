"""Common models shared across Direct and Metrika."""

from enum import Enum


class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"
