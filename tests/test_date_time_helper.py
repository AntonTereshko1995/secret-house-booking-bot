"""
Tests for date_time_helper module.
"""
import pytest
from datetime import date, datetime, time, timedelta
from freezegun import freeze_time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from helpers.date_time_helper import (
    get_month_name,
    get_future_months,
    parse_date,
    seconds_to_hours,
    month_bounds,
    _get_month_end_date,
)


class TestGetMonthName:
    """Test get_month_name function."""

    def test_all_months(self):
        """Test all month names."""
        expected = {
            1: "Январь",
            2: "Февраль",
            3: "Март",
            4: "Апрель",
            5: "Май",
            6: "Июнь",
            7: "Июль",
            8: "Август",
            9: "Сентябрь",
            10: "Октябрь",
            11: "Ноябрь",
            12: "Декабрь",
        }
        for month, name in expected.items():
            assert get_month_name(month) == name

    def test_invalid_month(self):
        """Test invalid month returns None."""
        assert get_month_name(0) is None
        assert get_month_name(13) is None


class TestGetFutureMonths:
    """Test get_future_months function."""

    @freeze_time("2024-06-15")
    def test_get_next_3_months(self):
        """Test getting next 3 months from June."""
        result = get_future_months(3)
        assert "2024_06" in result  # Current month
        assert result["2024_06"] == "Июнь"
        assert "2024_07" in result
        assert result["2024_07"] == "Июль"
        assert "2024_08" in result
        assert "2024_09" in result
        assert len(result) == 4  # Current + 3 future

    @freeze_time("2024-12-15")
    def test_year_transition(self):
        """Test month list across year boundary."""
        result = get_future_months(2)
        assert "2024_12" in result
        assert "2025_01" in result
        assert result["2025_01"] == "Январь"


class TestParseDate:
    """Test parse_date function."""

    def test_valid_date_default_format(self):
        """Test parsing valid date with default format."""
        result = parse_date("15.06.2024")
        assert result == datetime(2024, 6, 15, 0, 0)

    def test_valid_date_custom_format(self):
        """Test parsing valid date with custom format."""
        result = parse_date("2024-06-15", "%Y-%m-%d")
        assert result == datetime(2024, 6, 15, 0, 0)

    def test_invalid_date(self):
        """Test parsing invalid date returns None."""
        assert parse_date("invalid") is None
        assert parse_date("32.13.2024") is None

    def test_none_input(self):
        """Test None input returns None."""
        assert parse_date(None) is None


class TestSecondsToHours:
    """Test seconds_to_hours function."""

    def test_full_hours(self):
        """Test conversion of full hours."""
        assert seconds_to_hours(3600) == 1.0
        assert seconds_to_hours(7200) == 2.0

    def test_partial_hours(self):
        """Test conversion of partial hours."""
        assert seconds_to_hours(1800) == 0.5
        assert seconds_to_hours(5400) == 1.5

    def test_zero(self):
        """Test zero seconds."""
        assert seconds_to_hours(0) == 0.0


class TestMonthBounds:
    """Test month_bounds function."""

    def test_mid_month(self):
        """Test bounds for middle of month."""
        test_date = date(2024, 6, 15)
        first, last = month_bounds(test_date)
        assert first == date(2024, 6, 1)
        assert last == date(2024, 6, 30)

    def test_first_day(self):
        """Test bounds when input is first day."""
        test_date = date(2024, 6, 1)
        first, last = month_bounds(test_date)
        assert first == date(2024, 6, 1)
        assert last == date(2024, 6, 30)

    def test_last_day(self):
        """Test bounds when input is last day."""
        test_date = date(2024, 6, 30)
        first, last = month_bounds(test_date)
        assert first == date(2024, 6, 1)
        assert last == date(2024, 6, 30)

    def test_february_leap_year(self):
        """Test February in leap year."""
        test_date = date(2024, 2, 15)
        first, last = month_bounds(test_date)
        assert first == date(2024, 2, 1)
        assert last == date(2024, 2, 29)

    def test_february_non_leap_year(self):
        """Test February in non-leap year."""
        test_date = date(2023, 2, 15)
        first, last = month_bounds(test_date)
        assert first == date(2023, 2, 1)
        assert last == date(2023, 2, 28)

    def test_december(self):
        """Test December (year boundary)."""
        test_date = date(2024, 12, 15)
        first, last = month_bounds(test_date)
        assert first == date(2024, 12, 1)
        assert last == date(2024, 12, 31)


class TestGetMonthEndDate:
    """Test _get_month_end_date function."""

    def test_january(self):
        """Test January (31 days)."""
        assert _get_month_end_date(2024, 1) == date(2024, 1, 31)

    def test_february_leap(self):
        """Test February in leap year."""
        assert _get_month_end_date(2024, 2) == date(2024, 2, 29)

    def test_february_non_leap(self):
        """Test February in non-leap year."""
        assert _get_month_end_date(2023, 2) == date(2023, 2, 28)

    def test_april(self):
        """Test April (30 days)."""
        assert _get_month_end_date(2024, 4) == date(2024, 4, 30)

    def test_december(self):
        """Test December (year transition)."""
        assert _get_month_end_date(2024, 12) == date(2024, 12, 31)
