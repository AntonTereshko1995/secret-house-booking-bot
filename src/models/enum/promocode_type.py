"""
Promocode type enum.
"""
from enum import Enum


class PromocodeType(Enum):
    """Enum for promocode types."""
    PERCENTAGE = "percentage"
    FIXED = "fixed"
    SPECIAL = "special"
