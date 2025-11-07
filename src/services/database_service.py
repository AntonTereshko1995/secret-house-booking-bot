"""
Database Service Facade

This service provides backward compatibility by delegating to specialized repositories:
- UserRepository: User-related operations
- GiftRepository: Gift certificate operations
- BookingRepository: Booking operations

For new code, prefer using the specialized repositories directly from:
src.services.database import UserRepository, GiftRepository, BookingRepository
"""

from datetime import date, datetime
from typing import Sequence
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.database import UserRepository, GiftRepository, BookingRepository
from db.models.user import UserBase
from db.models.gift import GiftBase
from db.models.booking import BookingBase
from src.models.enum.tariff import Tariff
from singleton_decorator import singleton


@singleton
class DatabaseService:
    """
    Facade for database operations. Delegates to specialized repositories.

    This class maintains backward compatibility while organizing code into
    separate repositories by entity type.
    """

    def __init__(self):
        self.user_repository = UserRepository()
        self.gift_repository = GiftRepository()
        self.booking_repository = BookingRepository()

        # For backward compatibility
        self.engine = self.user_repository.engine
        self.Session = self.user_repository.Session

    # ========== User Operations ==========

    def add_user(self, contact: str) -> UserBase:
        """Add a new user to the database."""
        return self.user_repository.add_user(contact)

    def get_or_create_user(self, contact: str) -> UserBase:
        """Get existing user or create new one."""
        return self.user_repository.get_or_create_user(contact)

    def get_user_by_contact(self, contact: str) -> UserBase:
        """Get user by contact (username or phone)."""
        return self.user_repository.get_user_by_contact(contact)

    def get_user_by_id(self, user_id: int) -> UserBase:
        """Get user by ID."""
        return self.user_repository.get_user_by_id(user_id)

    def get_user_by_chat_id(self, chat_id: int) -> UserBase:
        """Get user by chat_id."""
        return self.user_repository.get_user_by_chat_id(chat_id)

    def update_user_contact(self, user_id: int, contact: str) -> UserBase:
        """Update user's contact (phone/email)."""
        return self.user_repository.update_user_contact(user_id, contact)

    def update_user_chat_id(self, contact: str, chat_id: int) -> UserBase:
        """Update or set chat_id for user. Handles duplicates gracefully."""
        return self.user_repository.update_user_chat_id(contact, chat_id)

    def get_all_user_chat_ids(self) -> list[int]:
        """Get all chat IDs from UserBase."""
        return self.user_repository.get_all_user_chat_ids()

    def get_user_chat_ids_with_bookings(self) -> list[int]:
        """Get chat IDs of users who have at least one booking."""
        return self.user_repository.get_user_chat_ids_with_bookings()

    def get_user_chat_ids_without_bookings(self) -> list[int]:
        """Get chat IDs of users who have never made a booking."""
        return self.user_repository.get_user_chat_ids_without_bookings()

    def remove_user_chat_id(self, chat_id: int) -> bool:
        """Remove chat_id from user (set to None). Returns True if found."""
        return self.user_repository.remove_user_chat_id(chat_id)

    def increment_completed_bookings(self, user_id: int) -> None:
        """Increment completed booking counter for user."""
        return self.user_repository.increment_completed_bookings(user_id)

    # ========== Gift Operations ==========

    def add_gift(
        self,
        buyer_contact: str,
        tariff: Tariff,
        has_sauna: bool,
        has_secret_room: bool,
        has_additional_bedroom: bool,
        price: float,
        code: str,
    ) -> GiftBase:
        """Add a new gift certificate to the database."""
        return self.gift_repository.add_gift(
            buyer_contact,
            tariff,
            has_sauna,
            has_secret_room,
            has_additional_bedroom,
            price,
            code,
        )

    def update_gift(
        self,
        gift_id: int,
        user_id: int = None,
        date_expired: datetime = None,
        is_paymented: bool = None,
        is_done: bool = None,
    ) -> GiftBase:
        """Update gift certificate fields."""
        return self.gift_repository.update_gift(
            gift_id, user_id, date_expired, is_paymented, is_done
        )

    def get_gift_by_code(self, code: str) -> GiftBase:
        """Get valid gift certificate by code."""
        return self.gift_repository.get_gift_by_code(code)

    def get_gift_by_id(self, id: int) -> GiftBase:
        """Get gift certificate by ID."""
        return self.gift_repository.get_gift_by_id(id)

    # ========== Booking Operations ==========

    def add_booking(
        self,
        user_contact: str,
        start_date: datetime,
        end_date: datetime,
        tariff: Tariff,
        has_photoshoot: bool,
        has_sauna: bool,
        has_white_bedroom: bool,
        has_green_bedroom: bool,
        has_secret_room: bool,
        number_of_guests: int,
        price: float,
        comment: str,
        gift_id: int = None,
        wine_preference: str = None,
        transfer_address: str = None,
    ) -> BookingBase:
        """Add a new booking to the database."""
        return self.booking_repository.add_booking(
            user_contact,
            start_date,
            end_date,
            tariff,
            has_photoshoot,
            has_sauna,
            has_white_bedroom,
            has_green_bedroom,
            has_secret_room,
            number_of_guests,
            price,
            comment,
            gift_id,
            wine_preference,
            transfer_address,
        )

    def get_booking_by_start_date_user(
        self, user_contact: str, start_date: date
    ) -> BookingBase:
        """Get booking for specific user by start date."""
        return self.booking_repository.get_booking_by_start_date_user(
            user_contact, start_date
        )

    def get_booking_by_start_date(self, start_date: date):
        """Get all bookings starting on a specific date."""
        return self.booking_repository.get_booking_by_start_date(start_date)

    def get_booking_by_finish_date(self, end_date: date):
        """Get all bookings ending on a specific date."""
        return self.booking_repository.get_booking_by_finish_date(end_date)

    def get_booking_by_period(
        self, from_date: date, to_date: date, is_admin: bool = False
    ) -> Sequence[BookingBase]:
        """Get bookings within a date range."""
        return self.booking_repository.get_booking_by_period(
            from_date, to_date, is_admin
        )

    def get_booking_by_day(
        self, target_date: date, except_booking_id: int = None
    ) -> Sequence[BookingBase]:
        """Get all bookings overlapping with a specific day."""
        return self.booking_repository.get_booking_by_day(
            target_date, except_booking_id
        )

    def get_bookings_by_month(
        self, target_month: int, target_year: int
    ) -> Sequence[BookingBase]:
        """Get all bookings overlapping with a specific month."""
        return self.booking_repository.get_bookings_by_month(target_month, target_year)

    def is_booking_between_dates(self, start: datetime, end: datetime) -> bool:
        """Check if there are any bookings between the given dates."""
        return self.booking_repository.is_booking_between_dates(start, end)

    def get_booking_by_id(self, booking_id: int) -> BookingBase:
        """Get booking by ID."""
        return self.booking_repository.get_booking_by_id(booking_id)

    def get_booking_by_user_contact(self, user_contact: str) -> list[BookingBase]:
        """Get all active bookings for a user."""
        return self.booking_repository.get_booking_by_user_contact(user_contact)

    def get_unpaid_bookings(self) -> Sequence[BookingBase]:
        """Get all unpaid, active bookings."""
        return self.booking_repository.get_unpaid_bookings()

    def get_all_chat_ids(self) -> list[int]:
        """Get all unique chat IDs from bookings (legacy method)."""
        return self.booking_repository.get_all_chat_ids()

    def get_done_booking_count(self, user_id: int) -> int:
        """Get count of completed bookings for a user from user.completed_bookings."""
        user = self.user_repository.get_user_by_id(user_id)
        return user.completed_bookings if user else 0

    def update_booking(
        self,
        booking_id: int,
        start_date: datetime = None,
        end_date: datetime = None,
        is_canceled: bool = None,
        is_date_changed: bool = None,
        price: float = None,
        is_prepaymented: bool = None,
        calendar_event_id: str = None,
        is_done: bool = None,
        prepayment: float = None,
    ) -> BookingBase:
        """Update booking fields."""
        return self.booking_repository.update_booking(
            booking_id,
            start_date,
            end_date,
            is_canceled,
            is_date_changed,
            price,
            is_prepaymented,
            calendar_event_id,
            is_done,
            prepayment,
        )

    # Statistics methods
    def get_bookings_count_by_period(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        is_completed: bool = None,
    ) -> int:
        """Get count of bookings in a period with optional completion filter."""
        return self.booking_repository.get_bookings_count_by_period(
            start_date, end_date, is_completed
        )

    def get_revenue_by_period(
        self, start_date: datetime = None, end_date: datetime = None
    ) -> float:
        """Get total revenue from completed bookings in a period."""
        return self.booking_repository.get_revenue_by_period(start_date, end_date)

    def get_canceled_bookings_count(
        self, start_date: datetime = None, end_date: datetime = None
    ) -> int:
        """Get count of canceled bookings in a period."""
        return self.booking_repository.get_canceled_bookings_count(start_date, end_date)

    def get_active_bookings_count(
        self, start_date: datetime = None, end_date: datetime = None
    ) -> int:
        """Get count of active/upcoming bookings in a period."""
        return self.booking_repository.get_active_bookings_count(start_date, end_date)

    def get_total_users_count(self) -> int:
        """Get total count of users in system."""
        return self.user_repository.get_total_users_count()

    def get_users_with_bookings_count(self) -> int:
        """Get count of users with at least one booking."""
        return self.user_repository.get_users_with_bookings_count()

    def get_users_with_completed_count(self) -> int:
        """Get count of users with at least one completed booking."""
        return self.user_repository.get_users_with_completed_count()

    def get_active_users_count(self) -> int:
        """Get count of active users."""
        return self.user_repository.get_active_users_count()

    def get_deactivated_users_count(self) -> int:
        """Get count of deactivated users."""
        return self.user_repository.get_deactivated_users_count()
