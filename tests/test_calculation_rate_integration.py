import pytest
import sys
import os
from datetime import date
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from models.date_pricing_rule import DatePricingRule
from models.enum.tariff import Tariff
from models.rental_price import RentalPrice
from services.calculation_rate_service import CalculationRateService


class TestCalculationRateServiceIntegration:
    """Test integration of date pricing with CalculationRateService."""

    @pytest.fixture
    def mock_services(self):
        """Mock both FileService and DatePricingService."""
        # Mock standard rental price
        standard_rental_price = RentalPrice(
            tariff=1,  # Use enum value, not enum
            name="Standard Day Rate",
            duration_hours=24,
            price=700,
            sauna_price=100,
            secret_room_price=0,
            second_bedroom_price=0,
            extra_hour_price=30,
            extra_people_price=0,
            photoshoot_price=100,
            max_people=6,
            is_check_in_time_limit=False,
            is_photoshoot=True,
            is_transfer=False,
            subscription_type=0,
            multi_day_prices={
                "1": 700,
                "2": 1300,
                "3": 1850
            }
        )

        # Mock date pricing rules
        test_rules = [
            DatePricingRule(
                rule_id="christmas_2024",
                name="Christmas Day Premium",
                start_date="2024-12-25",
                end_date="2024-12-25",
                price_override=1500
            ),
            DatePricingRule(
                rule_id="new_year_week_2025",
                name="New Year Week Special",
                start_date="2024-12-31",
                end_date="2025-01-07",
                price_override=1200
            )
        ]

        with patch('services.calculation_rate_service.FileService') as mock_file_service, \
             patch('services.date_pricing_service.FileService') as mock_date_file_service:

            mock_file_service.return_value.get_tariff_rates.return_value = [standard_rental_price]
            mock_date_file_service.return_value.get_date_pricing_rules.return_value = test_rules

            yield {
                'file_service': mock_file_service,
                'date_file_service': mock_date_file_service,
                'standard_price': standard_rental_price,
                'rules': test_rules
            }

    def test_get_effective_price_for_date_with_override(self, mock_services):
        """Test getting effective price when date has override."""
        service = CalculationRateService()
        service._rates = []  # Force reload

        # Christmas should use override price
        christmas_price = service.get_effective_price_for_date(
            date(2024, 12, 25),
            Tariff.DAY,
            24
        )
        assert christmas_price == 1500

    def test_get_effective_price_for_date_without_override(self, mock_services):
        """Test getting effective price when date has no override."""
        service = CalculationRateService()
        service._rates = []  # Force reload

        # Regular date should use standard price (using April to avoid summer promotion)
        regular_price = service.get_effective_price_for_date(
            date(2024, 4, 15),
            Tariff.DAY,
            24
        )
        assert regular_price == 700

    def test_get_effective_price_multi_day_with_override(self, mock_services):
        """Test multi-day pricing with date overrides."""
        service = CalculationRateService()
        service._rates = []  # Force reload

        # New Year week with 2 days - should use single override price
        two_day_price = service.get_effective_price_for_date(
            date(2025, 1, 1),
            Tariff.DAY,
            48
        )
        assert two_day_price == 1200

        # New Year week with 3 days - should use single override price
        three_day_price = service.get_effective_price_for_date(
            date(2025, 1, 1),
            Tariff.DAY,
            72
        )
        assert three_day_price == 1200

    def test_get_effective_price_multi_day_without_override(self, mock_services):
        """Test multi-day pricing without date overrides uses standard rates."""
        service = CalculationRateService()
        service._rates = []  # Force reload

        # Regular date with 2 days should use standard multi-day pricing
        two_day_price = service.get_effective_price_for_date(
            date(2024, 4, 15),
            Tariff.DAY,
            48
        )
        assert two_day_price == 1300

    def test_calculate_price_for_date_with_addons(self, mock_services):
        """Test calculating total price including add-ons with date override."""
        service = CalculationRateService()
        service._rates = []  # Force reload

        # Christmas with sauna and photoshoot
        total_price = service.calculate_price_for_date(
            booking_date=date(2024, 12, 25),
            tariff=Tariff.DAY,
            duration_hours=24,
            is_sauna=True,
            is_photoshoot=True
        )

        # Base price (override) + sauna + photoshoot
        expected_price = 1500 + 100 + 100  # 1700
        assert total_price == expected_price

    def test_calculate_price_for_date_without_override_addons(self, mock_services):
        """Test calculating total price including add-ons without date override."""
        service = CalculationRateService()
        service._rates = []  # Force reload

        # Regular date with sauna and photoshoot
        total_price = service.calculate_price_for_date(
            booking_date=date(2024, 4, 15),
            tariff=Tariff.DAY,
            duration_hours=24,
            is_sauna=True,
            is_photoshoot=True
        )

        # Standard base price + sauna + photoshoot
        expected_price = 700 + 100 + 100  # 900
        assert total_price == expected_price








    def test_backward_compatibility_existing_methods(self, mock_services):
        """Test that existing methods still work unchanged."""
        service = CalculationRateService()
        service._rates = []  # Force reload

        # Existing get_by_tariff should work unchanged
        rental_price = service.get_by_tariff(Tariff.DAY)
        assert rental_price.price == 700

        # Existing get_price should work unchanged
        price = service.get_price(tariff=Tariff.DAY)
        assert price == 700

        # Existing calculate_price should work unchanged
        total_price = service.calculate_price(
            rental_price=rental_price,
            is_sauna=True,
            is_secret_room=False,
            is_second_room=False,
            is_photoshoot=True,
            count_people=2,
            duration_hours=24
        )
        expected = 700 + 100 + 100  # base + sauna + photoshoot
        assert total_price == expected

    def test_extra_hours_calculation_with_override(self, mock_services):
        """Test extra hours calculation when base price is overridden."""
        service = CalculationRateService()
        service._rates = []  # Force reload

        # Christmas day with extra 6 hours (30 hours total)
        # Note: For date overrides, extra hours calculation is not implemented
        # The override price applies to the whole duration
        price = service.get_effective_price_for_date(
            date(2024, 12, 25),
            Tariff.DAY,
            30
        )

        # Should be just the override price (date rules don't add extra hour charges)
        expected = 1500
        assert price == expected

    def test_edge_case_zero_duration(self, mock_services):
        """Test edge case with zero duration."""
        service = CalculationRateService()
        service._rates = []  # Force reload

        # Should handle zero duration gracefully
        price = service.get_effective_price_for_date(
            date(2024, 12, 25),
            Tariff.DAY,
            0
        )
        assert price == 1500  # Should return base override price