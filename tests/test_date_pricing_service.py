import pytest
import sys
import os
from datetime import date
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from models.date_pricing_rule import DatePricingRule
from services.date_pricing_service import DatePricingService


class TestDatePricingRule:
    """Test the DatePricingRule model validation and methods."""

    def test_valid_rule_creation(self):
        """Test creating a valid date pricing rule."""
        rule = DatePricingRule(
            rule_id="test_rule",
            name="Test Rule",
            start_date="2024-12-25",
            end_date="2024-12-25",
            price_override=1500
        )
        assert rule.rule_id == "test_rule"
        assert rule.price_override == 1500

    def test_invalid_date_format_raises_error(self):
        """Test that invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date format"):
            DatePricingRule(
                rule_id="invalid_rule",
                name="Invalid Rule",
                start_date="invalid-date",
                end_date="2024-12-25",
                price_override=1000
            )

    def test_start_date_after_end_date_raises_error(self):
        """Test that start date after end date raises ValueError."""
        with pytest.raises(ValueError, match="Start date .* cannot be after end date"):
            DatePricingRule(
                rule_id="invalid_rule",
                name="Invalid Rule",
                start_date="2024-12-31",
                end_date="2024-12-25",
                price_override=1000
            )

    def test_negative_price_raises_error(self):
        """Test that negative price override raises ValueError."""
        with pytest.raises(ValueError, match="Price override cannot be negative"):
            DatePricingRule(
                rule_id="negative_price_rule",
                name="Negative Price Rule",
                start_date="2024-12-25",
                end_date="2024-12-25",
                price_override=-100
            )

    def test_applies_to_date_single_date(self):
        """Test rule applies to correct single date."""
        rule = DatePricingRule(
            rule_id="single_date_rule",
            name="Single Date Rule",
            start_date="2024-12-25",
            end_date="2024-12-25",
            price_override=1500
        )

        assert rule.applies_to_date(date(2024, 12, 25))
        assert not rule.applies_to_date(date(2024, 12, 24))
        assert not rule.applies_to_date(date(2024, 12, 26))

    def test_applies_to_date_range(self):
        """Test rule applies to date range."""
        rule = DatePricingRule(
            rule_id="range_rule",
            name="Range Rule",
            start_date="2024-12-25",
            end_date="2024-12-31",
            price_override=1000
        )

        assert rule.applies_to_date(date(2024, 12, 25))  # Start date
        assert rule.applies_to_date(date(2024, 12, 28))  # Middle date
        assert rule.applies_to_date(date(2024, 12, 31))  # End date
        assert not rule.applies_to_date(date(2024, 12, 24))  # Before range
        assert not rule.applies_to_date(date(2025, 1, 1))   # After range

    def test_inactive_rule_does_not_apply(self):
        """Test inactive rule does not apply to any date."""
        rule = DatePricingRule(
            rule_id="inactive_rule",
            name="Inactive Rule",
            start_date="2024-12-25",
            end_date="2024-12-25",
            price_override=1500,
            is_active=False
        )

        assert not rule.applies_to_date(date(2024, 12, 25))

    def test_get_price_for_duration_single_day(self):
        """Test getting price for single day duration."""
        rule = DatePricingRule(
            rule_id="single_day_rule",
            name="Single Day Rule",
            start_date="2024-12-25",
            end_date="2024-12-25",
            price_override=1500
        )

        assert rule.get_price_for_duration(24) == 1500
        assert rule.get_price_for_duration(12) == 1500

    def test_get_price_for_duration_no_override(self):
        """Test getting price when no override is set."""
        rule = DatePricingRule(
            rule_id="no_override_rule",
            name="No Override Rule",
            start_date="2024-12-25",
            end_date="2024-12-25"
        )

        assert rule.get_price_for_duration(24) is None


class TestDatePricingService:
    """Test the DatePricingService functionality."""

    @pytest.fixture
    def mock_file_service(self):
        """Mock FileService to return test data."""
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
            ),
            DatePricingRule(
                rule_id="disabled_rule",
                name="Disabled Rule",
                start_date="2024-12-01",
                end_date="2024-12-01",
                price_override=800,
                is_active=False
            )
        ]

        with patch('services.date_pricing_service.FileService') as mock_service:
            mock_service.return_value.get_date_pricing_rules.return_value = test_rules
            yield mock_service

    def test_single_date_rule_applies(self, mock_file_service):
        """Test single date rule application."""
        service = DatePricingService()
        service._rules = []  # Force reload

        effective_rule = service.get_effective_rule(date(2024, 12, 25))
        assert effective_rule is not None
        assert effective_rule.rule_id == "christmas_2024"

    def test_date_range_rule_applies(self, mock_file_service):
        """Test date range rule application."""
        service = DatePricingService()
        service._rules = []  # Force reload

        # Test start of range
        effective_rule = service.get_effective_rule(date(2024, 12, 31))
        assert effective_rule is not None
        assert effective_rule.rule_id == "new_year_week_2025"

        # Test middle of range
        effective_rule = service.get_effective_rule(date(2025, 1, 3))
        assert effective_rule is not None
        assert effective_rule.rule_id == "new_year_week_2025"

        # Test end of range
        effective_rule = service.get_effective_rule(date(2025, 1, 7))
        assert effective_rule is not None
        assert effective_rule.rule_id == "new_year_week_2025"

    def test_no_applicable_rules(self, mock_file_service):
        """Test when no rules apply to a date."""
        service = DatePricingService()
        service._rules = []  # Force reload

        effective_rule = service.get_effective_rule(date(2024, 6, 15))
        assert effective_rule is None

    def test_disabled_rules_ignored(self, mock_file_service):
        """Test that disabled rules are ignored."""
        service = DatePricingService()
        service._rules = []  # Force reload

        effective_rule = service.get_effective_rule(date(2024, 12, 1))
        assert effective_rule is None

    def test_price_override_with_duration(self, mock_file_service):
        """Test price override calculation with duration."""
        service = DatePricingService()
        service._rules = []  # Force reload

        price = service.get_price_override(date(2024, 12, 25), 24)
        assert price == 1500

        # Test no override for date without rules
        price = service.get_price_override(date(2024, 6, 15), 24)
        assert price is None

    def test_has_date_override(self, mock_file_service):
        """Test checking if date has price override."""
        service = DatePricingService()
        service._rules = []  # Force reload

        assert service.has_date_override(date(2024, 12, 25))
        assert not service.has_date_override(date(2024, 6, 15))

    def test_get_rule_description(self, mock_file_service):
        """Test getting rule description."""
        service = DatePricingService()
        service._rules = []  # Force reload

        description = service.get_rule_description(date(2024, 12, 25))
        assert description is not None
        assert "Christmas" in description

        description = service.get_rule_description(date(2024, 6, 15))
        assert description is None

    def test_refresh_rules(self, mock_file_service):
        """Test refreshing rules from file."""
        service = DatePricingService()

        # Load rules initially
        rules = service._try_load_rules()
        assert len(rules) == 3

        # Refresh rules
        refreshed_rules = service.refresh_rules()
        assert len(refreshed_rules) == 3