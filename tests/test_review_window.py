"""Unit tests for the bot's review-window mirror.

The bot only repeats the API's window rule for an early refusal; the single
source of truth lives in secret-house-api (see CONTRACTS.md section 1).
"""
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.review_window import review_eligibility


class _Booking:
    def __init__(self, start_date, is_canceled=False, is_prepaymented=True,
                 feedback_submitted=False):
        self.start_date = start_date
        self.is_canceled = is_canceled
        self.is_prepaymented = is_prepaymented
        self.feedback_submitted = feedback_submitted


START = datetime(2026, 3, 1, 14, 0)


def test_checkin_day_is_eligible():
    can, deadline = review_eligibility(_Booking(START), today=date(2026, 3, 1))
    assert can is True
    assert deadline == date(2026, 3, 15)


def test_14th_day_is_eligible():
    can, deadline = review_eligibility(_Booking(START), today=date(2026, 3, 15))
    assert can is True
    assert deadline == date(2026, 3, 15)


def test_15th_day_is_closed():
    can, _ = review_eligibility(_Booking(START), today=date(2026, 3, 16))
    assert can is False


def test_cancelled_booking_is_not_eligible():
    can, deadline = review_eligibility(
        _Booking(START, is_canceled=True), today=date(2026, 3, 1)
    )
    assert can is False
    assert deadline is None


def test_unprepaid_booking_is_not_eligible():
    can, deadline = review_eligibility(
        _Booking(START, is_prepaymented=False), today=date(2026, 3, 1)
    )
    assert can is False
    assert deadline is None


def test_already_reviewed_booking_is_not_eligible():
    can, deadline = review_eligibility(
        _Booking(START, feedback_submitted=True), today=date(2026, 3, 1)
    )
    assert can is False
    assert deadline is None


def test_missing_booking_is_not_eligible():
    can, deadline = review_eligibility(None, today=date(2026, 3, 1))
    assert can is False
    assert deadline is None
