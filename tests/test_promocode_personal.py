"""Unit tests for personal (single-use reward) promocode validation.

The booking contact must match the promocode owner; otherwise the code is
rejected with the same message the API uses.
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models.enum.tariff import Tariff
from src.services.database.promocode_repository import PromocodeRepository

PERSONAL_ERROR = (
    "Этот промокод именной: он действует только для контакта, "
    "с которого оставлен отзыв"
)


class _Promo:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.promocode_type = 1  # BOOKING_DATES
        self.date_from = date(2026, 1, 1)
        self.date_to = date(2026, 12, 31)
        self.applicable_tariffs = None
        self.is_active = True
        self.name = "rev12345678"


class _User:
    def __init__(self, id, contact):
        self.id = id
        self.contact = contact


class _Session:
    def __init__(self, scalar_results):
        self._scalar_results = list(scalar_results)
        self.expunged = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def scalar(self, stmt):
        return self._scalar_results.pop(0)

    def expunge(self, obj):
        self.expunged.append(obj)


def _repo(session):
    repo = PromocodeRepository.__wrapped__()
    repo.Session = lambda: session
    return repo


def test_personal_code_accepts_own_contact():
    promo = _Promo(user_id=1)
    owner = _User(1, "+375291234567")
    session = _Session([promo, owner])
    repo = _repo(session)

    is_valid, _message, result = repo.validate_promocode(
        "REV12345678", date(2026, 5, 1), Tariff.DAY, contact="+375291234567"
    )

    assert is_valid is True
    assert result is promo


def test_personal_code_rejects_foreign_contact():
    promo = _Promo(user_id=1)
    owner = _User(1, "+375291234567")
    session = _Session([promo, owner])
    repo = _repo(session)

    is_valid, message, result = repo.validate_promocode(
        "REV12345678", date(2026, 5, 1), Tariff.DAY, contact="+375298765432"
    )

    assert is_valid is False
    assert message == PERSONAL_ERROR
    assert result is None
