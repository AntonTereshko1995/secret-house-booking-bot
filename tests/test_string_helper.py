"""
Tests for string_helper module.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from helpers.string_helper import (
    is_valid_user_contact,
    separate_callback_data,
    get_callback_data,
    convert_hours_to_time_string,
    get_generated_code,
    bool_to_str,
    parse_booking_callback_data,
    parse_gift_callback_data,
    parse_manage_booking_callback,
    format_booking_button_label,
)
from datetime import datetime


class TestIsValidUserContact:
    """Test is_valid_user_contact function."""

    def test_valid_telegram_username(self):
        """Test valid Telegram username."""
        is_valid, cleaned = is_valid_user_contact("@testuser")
        assert is_valid is True
        assert cleaned == "@testuser"

    def test_valid_telegram_username_with_numbers(self):
        """Test valid Telegram username with numbers."""
        is_valid, cleaned = is_valid_user_contact("@test_user_123")
        assert is_valid is True
        assert cleaned == "@test_user_123"

    def test_invalid_telegram_username_too_short(self):
        """Test invalid Telegram username (too short)."""
        is_valid, cleaned = is_valid_user_contact("@test")
        assert is_valid is False

    def test_invalid_telegram_username_special_chars(self):
        """Test invalid Telegram username with special chars."""
        is_valid, cleaned = is_valid_user_contact("@test-user")
        assert is_valid is False

    def test_valid_belarus_phone(self):
        """Test valid Belarus phone number."""
        is_valid, cleaned = is_valid_user_contact("+375291234567")
        assert is_valid is True
        assert cleaned == "+375291234567"

    def test_valid_belarus_phone_with_formatting(self):
        """Test Belarus phone with formatting."""
        is_valid, cleaned = is_valid_user_contact("+375 (29) 123-45-67")
        assert is_valid is True
        assert cleaned == "+375291234567"

    def test_invalid_phone_wrong_prefix(self):
        """Test invalid phone with wrong country code."""
        is_valid, cleaned = is_valid_user_contact("+380291234567")
        assert is_valid is False

    def test_invalid_phone_too_short(self):
        """Test invalid phone (too short)."""
        is_valid, cleaned = is_valid_user_contact("+37529123456")
        assert is_valid is False

    def test_contact_with_newline(self):
        """Test contact with newline returns False."""
        is_valid, _ = is_valid_user_contact("test\nuser")
        assert is_valid is False

    def test_contact_with_spaces(self):
        """Test spaces are removed."""
        is_valid, cleaned = is_valid_user_contact(" @test user ")
        assert cleaned == "@testuser"


class TestCallbackDataParsing:
    """Test callback data parsing functions."""

    def test_separate_callback_data(self):
        """Test separating callback data."""
        result = separate_callback_data("ACTION_VALUE_123")
        assert result == ["ACTION", "VALUE", "123"]

    def test_get_callback_data(self):
        """Test getting last part of callback data."""
        result = get_callback_data("ACTION_VALUE_123")
        assert result == "123"

    def test_get_callback_data_single(self):
        """Test getting callback data with single element."""
        result = get_callback_data("SINGLE")
        assert result == "SINGLE"


class TestConvertHoursToTimeString:
    """Test convert_hours_to_time_string function."""

    def test_midnight(self):
        """Test midnight hour."""
        assert convert_hours_to_time_string(0) == "00:00"

    def test_morning(self):
        """Test morning hour."""
        assert convert_hours_to_time_string(9) == "09:00"

    def test_noon(self):
        """Test noon."""
        assert convert_hours_to_time_string(12) == "12:00"

    def test_evening(self):
        """Test evening hour."""
        assert convert_hours_to_time_string(23) == "23:00"

    def test_invalid_hour_negative(self):
        """Test invalid hour raises ValueError."""
        with pytest.raises(ValueError):
            convert_hours_to_time_string(-1)

    def test_invalid_hour_too_large(self):
        """Test hour > 23 raises ValueError."""
        with pytest.raises(ValueError):
            convert_hours_to_time_string(24)


class TestGetGeneratedCode:
    """Test get_generated_code function."""

    def test_code_length(self):
        """Test generated code has correct length."""
        code = get_generated_code()
        assert len(code) == 15

    def test_code_uppercase(self):
        """Test generated code is uppercase."""
        code = get_generated_code()
        assert code.isupper()

    def test_code_alpha_only(self):
        """Test generated code contains only letters."""
        code = get_generated_code()
        assert code.isalpha()

    def test_code_unique(self):
        """Test generated codes are different."""
        codes = [get_generated_code() for _ in range(10)]
        assert len(set(codes)) == 10  # All unique


class TestBoolToStr:
    """Test bool_to_str function."""

    def test_true(self):
        """Test True converts to 'Да'."""
        assert bool_to_str(True) == "Да"

    def test_false(self):
        """Test False converts to 'Нет'."""
        assert bool_to_str(False) == "Нет"


class TestParseBookingCallbackData:
    """Test parse_booking_callback_data function."""

    def test_valid_callback(self):
        """Test parsing valid booking callback."""
        callback = "booking_1_chatid_123456_bookingid_789_cash_True"
        result = parse_booking_callback_data(callback)
        assert result is not None
        assert result["menu_index"] == "1"
        assert result["user_chat_id"] == "123456"
        assert result["booking_id"] == "789"
        assert result["is_payment_by_cash"] == "True"

    def test_valid_callback_false_cash(self):
        """Test parsing with cash=False."""
        callback = "booking_2_chatid_111222_bookingid_333_cash_False"
        result = parse_booking_callback_data(callback)
        assert result is not None
        assert result["is_payment_by_cash"] == "False"

    def test_invalid_callback(self):
        """Test parsing invalid callback returns None."""
        result = parse_booking_callback_data("invalid_data")
        assert result is None


class TestParseGiftCallbackData:
    """Test parse_gift_callback_data function."""

    def test_valid_callback(self):
        """Test parsing valid gift callback."""
        callback = "gift_1_chatid_123456_giftid_789"
        result = parse_gift_callback_data(callback)
        assert result is not None
        assert result["menu_index"] == "1"
        assert result["user_chat_id"] == "123456"
        assert result["gift_id"] == "789"

    def test_invalid_callback(self):
        """Test parsing invalid callback returns None."""
        result = parse_gift_callback_data("invalid_data")
        assert result is None


class TestParseManageBookingCallback:
    """Test parse_manage_booking_callback function."""

    def test_list_type(self):
        """Test parsing list type."""
        result = parse_manage_booking_callback("MBL")
        assert result == {"type": "list"}

    def test_detail_type(self):
        """Test parsing detail type."""
        result = parse_manage_booking_callback("MBD_123")
        assert result == {"type": "detail", "booking_id": 123}

    def test_action_type(self):
        """Test parsing action type."""
        result = parse_manage_booking_callback("MBA_cancel_123")
        assert result == {"type": "action", "action": "cancel", "booking_id": 123}

    def test_tariff_select_type(self):
        """Test parsing tariff select type."""
        result = parse_manage_booking_callback("MBT_1_123")
        assert result == {"type": "tariff_select", "tariff": 1, "booking_id": 123}

    def test_back_detail_type(self):
        """Test parsing back to detail type."""
        result = parse_manage_booking_callback("MBB_123")
        assert result == {"type": "back_detail", "booking_id": 123}

    def test_invalid_callback(self):
        """Test parsing invalid callback raises ValueError."""
        with pytest.raises(ValueError):
            parse_manage_booking_callback("INVALID_DATA")


class TestFormatBookingButtonLabel:
    """Test format_booking_button_label function."""

    def test_format_booking(self):
        """Test formatting booking for button."""
        from unittest.mock import MagicMock

        booking = MagicMock()
        booking.start_date = datetime(2024, 6, 15, 14, 30)

        result = format_booking_button_label(booking)
        assert result == "15.06.2024 14:30"

    def test_format_booking_midnight(self):
        """Test formatting booking at midnight."""
        from unittest.mock import MagicMock

        booking = MagicMock()
        booking.start_date = datetime(2024, 12, 31, 0, 0)

        result = format_booking_button_label(booking)
        assert result == "31.12.2024 00:00"
