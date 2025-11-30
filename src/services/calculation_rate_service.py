"""
Calculation Rate Service - Stub for compatibility
This is a temporary stub. In the refactored architecture,
pricing calculations should be done via Backend API.
"""
from typing import Optional
from datetime import date


class CalculationRateService:
    """Service for calculating rental rates and prices."""

    def __init__(self):
        """Initialize the rate calculation service."""
        pass

    def calculate_price_for_date(
        self,
        booking_date: date,
        tariff: str,
        duration_hours: int,
        is_sauna: bool = False,
        is_secret_room: bool = False,
        is_second_room: bool = False,
        is_photoshoot: bool = False,
        count_people: int = 2
    ) -> int:
        """
        Calculate price for a booking.

        TODO: Replace with Backend API call to /api/v1/pricing/calculate
        """
        # Basic stub calculation
        base_price = 1000
        price = base_price

        if is_sauna:
            price += 500
        if is_secret_room:
            price += 300
        if is_second_room:
            price += 400
        if is_photoshoot:
            price += 600
        if count_people > 2:
            price += (count_people - 2) * 100

        return price

    def get_price_categories(
        self,
        rental_rate,
        is_sauna: bool,
        is_secret_room: bool,
        is_additional_bedroom: bool,
        number_of_guests: int,
        extra_hours: int = 0
    ) -> str:
        """Get formatted price categories string."""
        categories = []

        if is_sauna:
            categories.append("сауна")
        if is_secret_room:
            categories.append("секретная комната")
        if is_additional_bedroom:
            categories.append("дополнительная спальня")
        if number_of_guests > 2:
            categories.append(f"{number_of_guests} гостей")
        if extra_hours > 0:
            categories.append(f"+{extra_hours}ч")

        return ", ".join(categories) if categories else "базовая аренда"
