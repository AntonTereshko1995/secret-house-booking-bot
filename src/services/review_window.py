"""Review window helper for the Telegram bot.

This is only an early refusal check before starting the feedback questionnaire.
The single source of truth for the review window lives in secret-house-api
(see CONTRACTS.md §1); the bot repeats the same rule so it can skip asking
nine questions when the booking is clearly not eligible.
"""
from datetime import date, datetime, timedelta
from typing import Optional, Tuple

import pytz

MINSK_TZ = pytz.timezone("Europe/Minsk")


def minsk_today() -> date:
    """Return today's date in Europe/Minsk."""
    return datetime.now(MINSK_TZ).date()


def review_eligibility(booking, today: Optional[date] = None) -> Tuple[bool, Optional[date]]:
    """Return (can_review, deadline) for a booking.

    Mirrors the API rule: booking is not canceled, is prepaid, has no feedback
    yet, and today (Minsk) falls within [start_date; start_date + 14 days]
    inclusive. `deadline` is `start_date.date() + 14 days`.
    """
    if booking is None:
        return False, None

    if today is None:
        today = minsk_today()

    if booking.is_canceled or not booking.is_prepaymented or booking.feedback_submitted:
        return False, None

    start = booking.start_date.date() if hasattr(booking.start_date, "date") else booking.start_date
    deadline = start + timedelta(days=14)
    can_review = start <= today <= deadline
    return can_review, deadline
