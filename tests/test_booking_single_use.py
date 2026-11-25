"""Unit tests for single-use promocode consumption during booking."""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from src.models.enum.tariff import Tariff
from src.services.database.booking_repository import (
    BookingRepository,
    PromocodeAlreadyUsedError,
)


class _Promo:
    def __init__(self, is_active=True, is_single_use=True):
        self.is_active = is_active
        self.is_single_use = is_single_use


class _User:
    def __init__(self):
        self.id = 1
        self.contact = "+375291234567"


class _UserService:
    def __init__(self):
        self.user = _User()

    def get_or_create_user(self, contact):
        return self.user

    def increment_booking_count(self, user_id):
        pass


class _Session:
    def __init__(self, promo):
        self.promo = promo
        self.added = []
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get(self, model, id):
        return self.promo

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def _add_booking(repo, promocode_id):
    return repo.add_booking(
        user_contact="+375291234567",
        start_date=datetime(2026, 5, 1, 14, 0),
        end_date=datetime(2026, 5, 2, 14, 0),
        tariff=Tariff.DAY,
        has_photoshoot=False,
        has_sauna=False,
        has_white_bedroom=False,
        has_green_bedroom=False,
        has_secret_room=False,
        number_of_guests=2,
        price=500.0,
        comment="",
        promocode_id=promocode_id,
    )


def _repo(session):
    repo = BookingRepository.__wrapped__()
    repo.Session = lambda: session
    repo.user_service = _UserService()
    return repo


def test_single_use_code_is_deactivated_on_booking():
    promo = _Promo(is_active=True, is_single_use=True)
    session = _Session(promo)
    repo = _repo(session)

    booking = _add_booking(repo, promocode_id=1)

    assert booking is not None
    assert promo.is_active is False
    assert session.committed is True


def test_already_used_code_is_refused():
    promo = _Promo(is_active=False, is_single_use=True)
    session = _Session(promo)
    repo = _repo(session)

    with pytest.raises(PromocodeAlreadyUsedError):
        _add_booking(repo, promocode_id=1)

    assert session.rolled_back is True
