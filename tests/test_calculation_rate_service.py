"""
Tests for CalculationRateService.
"""
import pytest
from datetime import date
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from services.calculation_rate_service import CalculationRateService


@pytest.mark.unit
class TestCalculationRateService:
    """Test CalculationRateService."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return CalculationRateService()

    def test_basic_price_calculation(self, service):
        """Test basic price calculation without extras."""
        price = service.calculate_price_for_date(
            booking_date=date(2024, 6, 15),
            tariff="DAY",
            duration_hours=24,
            is_sauna=False,
            is_secret_room=False,
            is_second_room=False,
            is_photoshoot=False,
            count_people=2,
        )
        assert price == 1000  # Base price

    def test_price_with_sauna(self, service):
        """Test price calculation with sauna."""
        price = service.calculate_price_for_date(
            booking_date=date(2024, 6, 15),
            tariff="DAY",
            duration_hours=24,
            is_sauna=True,
            count_people=2,
        )
        assert price == 1500  # Base + sauna

    def test_price_with_all_extras(self, service):
        """Test price calculation with all extras."""
        price = service.calculate_price_for_date(
            booking_date=date(2024, 6, 15),
            tariff="DAY",
            duration_hours=24,
            is_sauna=True,
            is_secret_room=True,
            is_second_room=True,
            is_photoshoot=True,
            count_people=4,
        )
        # Base 1000 + sauna 500 + secret 300 + second 400 + photo 600 + 2 extra people 200
        assert price == 3000

    def test_extra_people_pricing(self, service):
        """Test pricing for extra people."""
        price_2_people = service.calculate_price_for_date(
            booking_date=date(2024, 6, 15),
            tariff="DAY",
            duration_hours=24,
            count_people=2,
        )

        price_5_people = service.calculate_price_for_date(
            booking_date=date(2024, 6, 15),
            tariff="DAY",
            duration_hours=24,
            count_people=5,
        )

        # 3 extra people = 300 extra
        assert price_5_people == price_2_people + 300

    def test_get_price_categories_base(self, service):
        """Test price categories with no extras."""
        categories = service.get_price_categories(
            rental_rate=None,
            is_sauna=False,
            is_secret_room=False,
            is_additional_bedroom=False,
            number_of_guests=2,
            extra_hours=0,
        )
        assert categories == "базовая аренда"

    def test_get_price_categories_with_sauna(self, service):
        """Test price categories with sauna."""
        categories = service.get_price_categories(
            rental_rate=None,
            is_sauna=True,
            is_secret_room=False,
            is_additional_bedroom=False,
            number_of_guests=2,
            extra_hours=0,
        )
        assert "сауна" in categories

    def test_get_price_categories_all_options(self, service):
        """Test price categories with all options."""
        categories = service.get_price_categories(
            rental_rate=None,
            is_sauna=True,
            is_secret_room=True,
            is_additional_bedroom=True,
            number_of_guests=4,
            extra_hours=3,
        )
        assert "сауна" in categories
        assert "секретная комната" in categories
        assert "дополнительная спальня" in categories
        assert "4 гостей" in categories
        assert "+3ч" in categories
