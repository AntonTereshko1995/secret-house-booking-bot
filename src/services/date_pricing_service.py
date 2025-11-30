"""
Date Pricing Service - Stub for compatibility
This is a temporary stub. In the refactored architecture,
pricing calculations should be done via Backend API.
"""
from datetime import date
from typing import Optional


class DatePricingService:
    """Service for managing date-specific pricing."""

    def __init__(self):
        """Initialize the date pricing service."""
        pass

    def has_date_override(self, booking_date: date) -> bool:
        """
        Check if a date has special pricing.

        TODO: Replace with Backend API call
        """
        return False

    def get_rule_description(self, booking_date: date) -> Optional[str]:
        """
        Get description of pricing rule for a date.

        TODO: Replace with Backend API call
        """
        return None
