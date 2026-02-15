"""
Session service for managing bot user session data.
Exact API replacement for RedisSessionService.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from singleton_decorator import singleton
from telegram import Update

from src.models.booking_draft import BookingDraft
from src.models.feedback import Feedback
from src.models.cancel_booking_draft import CancelBookingDraft
from src.models.change_booking_draft import ChangeBookingDraft
from src.models.gift_certificate_draft import GiftCertificateDraft
from src.models.user_booking_draft import UserBookingDraft
from src.models.enum.tariff import Tariff
from src.services.navigation_service import NavigationService
from src.services.session.session_store import SessionStore
from src.services.logger_service import LoggerService
from src.constants import (
    SESSION_STORAGE_FILE,
    SESSION_TTL_DAYS,
    CLEANUP_INTERVAL_DAYS
)


@singleton
class SessionService:
    """
    Manages session data for Telegram bot users.
    Drop-in replacement for RedisSessionService.
    """

    def __init__(self, ttl_days: int = SESSION_TTL_DAYS):
        """
        Initialize session service.

        Args:
            ttl_days: Time-to-live for stored data in days (default: 5)
        """
        self._store = SessionStore(
            storage_file=SESSION_STORAGE_FILE,
            cleanup_interval_days=CLEANUP_INTERVAL_DAYS
        )
        self._ttl_seconds = int(timedelta(days=ttl_days).total_seconds())
        self._navigation_service = NavigationService()
        LoggerService.info(__name__, f"SessionService initialized with TTL={ttl_days} days")

    async def initialize(self) -> None:
        """Initialize the underlying storage. Call from main.py."""
        await self._store.start()

    async def shutdown(self) -> None:
        """Shutdown the storage. Call from main.py cleanup."""
        await self._store.stop()

    # ============ Booking Operations ============

    async def init_booking(self, update: Update) -> None:
        """Initialize a new booking session for the user."""
        await self.clear_booking(update)
        await self.set_booking(update, BookingDraft())

    async def set_booking(self, update: Update, booking: BookingDraft) -> None:
        """Store booking object."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"booking:{chat_id}"
            await self._store.set(key, booking.to_json(), self._ttl_seconds)
        except Exception as e:
            LoggerService.error(__name__, "Failed to save booking", exception=e)

    async def get_booking(self, update: Update) -> Optional[BookingDraft]:
        """Retrieve booking object."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"booking:{chat_id}"
            data = await self._store.get(key)
            if data:
                return BookingDraft.from_json(data)
            return None
        except Exception as e:
            LoggerService.error(__name__, "Failed to get booking", exception=e)
            return None

    async def update_booking_field(self, update: Update, field: str, value) -> None:
        """Update a single field in booking object."""
        try:
            booking = await self.get_booking(update)
            if not booking:
                booking = BookingDraft()

            value = self._cast_field(field, value)
            setattr(booking, field, value)
            await self.set_booking(update, booking)
        except Exception as e:
            LoggerService.error(__name__, f"Failed to update booking field: {field}", exception=e)

    async def update_booking_fields(self, update: Update, fields: dict) -> None:
        """Update multiple fields in booking object."""
        try:
            booking = await self.get_booking(update)
            if not booking:
                booking = BookingDraft()

            for field, value in fields.items():
                setattr(booking, field, self._cast_field(field, value))

            await self.set_booking(update, booking)
        except Exception as e:
            LoggerService.error(__name__, "Failed to update booking fields", exception=e)

    async def clear_booking(self, update: Update) -> None:
        """Clear booking data."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"booking:{chat_id}"
            await self._store.delete(key)
        except Exception as e:
            LoggerService.error(__name__, "Failed to clear booking", exception=e)

    # ============ Feedback Operations ============

    async def init_feedback(self, update: Update) -> None:
        """Initialize feedback storage in Redis."""
        await self.clear_feedback(update)
        await self.set_feedback(update, Feedback())

    async def set_feedback(self, update: Update, feedback: Feedback) -> None:
        """Store feedback object in Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"feedback:{chat_id}"
            await self._store.set(key, feedback.to_json(), self._ttl_seconds)
        except Exception as e:
            LoggerService.error(__name__, "Failed to save feedback", exception=e)

    async def get_feedback(self, update: Update) -> Optional[Feedback]:
        """Retrieve feedback object from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"feedback:{chat_id}"
            data = await self._store.get(key)
            if data:
                return Feedback.from_json(data)
            return None
        except Exception as e:
            LoggerService.error(__name__, "Failed to get feedback", exception=e)
            return None

    async def update_feedback_field(self, update: Update, field: str, value) -> None:
        """Update a single field in feedback object."""
        try:
            feedback = await self.get_feedback(update)
            if not feedback:
                feedback = Feedback()
            setattr(feedback, field, value)
            await self.set_feedback(update, feedback)
        except Exception as e:
            LoggerService.error(__name__, f"Failed to update feedback field: {field}", exception=e)

    async def clear_feedback(self, update: Update) -> None:
        """Clear feedback data from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"feedback:{chat_id}"
            await self._store.delete(key)
        except Exception as e:
            LoggerService.error(__name__, "Failed to clear feedback", exception=e)

    # ============ Cancel Booking Operations ============

    async def init_cancel_booking(self, update: Update) -> None:
        """Initialize a new cancel booking session for the user."""
        await self.clear_cancel_booking(update)
        await self.set_cancel_booking(update, CancelBookingDraft())

    async def set_cancel_booking(self, update: Update, draft: CancelBookingDraft) -> None:
        """Store cancel booking draft in Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"cancel_booking:{chat_id}"
            await self._store.set(key, draft.to_json(), self._ttl_seconds)
        except Exception as e:
            LoggerService.error(__name__, "Failed to save cancel booking draft", exception=e)

    async def get_cancel_booking(self, update: Update) -> Optional[CancelBookingDraft]:
        """Retrieve cancel booking draft from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"cancel_booking:{chat_id}"
            data = await self._store.get(key)
            if data:
                return CancelBookingDraft.from_json(data)
            return None
        except Exception as e:
            LoggerService.error(__name__, "Failed to get cancel booking draft", exception=e)
            return None

    async def update_cancel_booking_field(self, update: Update, field: str, value) -> None:
        """Update a single field in cancel booking draft."""
        try:
            draft = await self.get_cancel_booking(update)
            if not draft:
                draft = CancelBookingDraft()
            setattr(draft, field, value)
            await self.set_cancel_booking(update, draft)
        except Exception as e:
            LoggerService.error(__name__, f"Failed to update cancel booking field: {field}", exception=e)

    async def clear_cancel_booking(self, update: Update) -> None:
        """Clear cancel booking draft from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"cancel_booking:{chat_id}"
            await self._store.delete(key)
        except Exception as e:
            LoggerService.error(__name__, "Failed to clear cancel booking draft", exception=e)

    # ============ Change Booking Date Operations ============

    async def init_change_booking(self, update: Update) -> None:
        """Initialize a new change booking session for the user."""
        await self.clear_change_booking(update)
        await self.set_change_booking(update, ChangeBookingDraft())

    async def set_change_booking(self, update: Update, draft: ChangeBookingDraft) -> None:
        """Store change booking draft in Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"change_booking:{chat_id}"
            await self._store.set(key, draft.to_json(), self._ttl_seconds)
        except Exception as e:
            LoggerService.error(__name__, "Failed to save change booking draft", exception=e)

    async def get_change_booking(self, update: Update) -> Optional[ChangeBookingDraft]:
        """Retrieve change booking draft from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"change_booking:{chat_id}"
            data = await self._store.get(key)
            if data:
                return ChangeBookingDraft.from_json(data)
            return None
        except Exception as e:
            LoggerService.error(__name__, "Failed to get change booking draft", exception=e)
            return None

    async def update_change_booking_field(self, update: Update, field: str, value) -> None:
        """Update a single field in change booking draft."""
        try:
            draft = await self.get_change_booking(update)
            if not draft:
                draft = ChangeBookingDraft()
            setattr(draft, field, value)
            await self.set_change_booking(update, draft)
        except Exception as e:
            LoggerService.error(__name__, f"Failed to update change booking field: {field}", exception=e)

    async def clear_change_booking(self, update: Update) -> None:
        """Clear change booking draft from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"change_booking:{chat_id}"
            await self._store.delete(key)
        except Exception as e:
            LoggerService.error(__name__, "Failed to clear change booking draft", exception=e)

    # ============ Gift Certificate Operations ============

    async def init_gift_certificate(self, update: Update) -> None:
        """Initialize a new gift certificate session for the user."""
        await self.clear_gift_certificate(update)
        await self.set_gift_certificate(update, GiftCertificateDraft())

    async def set_gift_certificate(self, update: Update, draft: GiftCertificateDraft) -> None:
        """Store gift certificate draft in Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"gift_certificate:{chat_id}"
            await self._store.set(key, draft.to_json(), self._ttl_seconds)
        except Exception as e:
            LoggerService.error(__name__, "Failed to save gift certificate draft", exception=e)

    async def get_gift_certificate(self, update: Update) -> Optional[GiftCertificateDraft]:
        """Retrieve gift certificate draft from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"gift_certificate:{chat_id}"
            data = await self._store.get(key)
            if data:
                return GiftCertificateDraft.from_json(data)
            return None
        except Exception as e:
            LoggerService.error(__name__, "Failed to get gift certificate draft", exception=e)
            return None

    async def update_gift_certificate_field(self, update: Update, field: str, value) -> None:
        """Update a single field in gift certificate draft."""
        try:
            draft = await self.get_gift_certificate(update)
            if not draft:
                draft = GiftCertificateDraft()
            setattr(draft, field, value)
            await self.set_gift_certificate(update, draft)
        except Exception as e:
            LoggerService.error(__name__, f"Failed to update gift certificate field: {field}", exception=e)

    async def clear_gift_certificate(self, update: Update) -> None:
        """Clear gift certificate draft from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"gift_certificate:{chat_id}"
            await self._store.delete(key)
        except Exception as e:
            LoggerService.error(__name__, "Failed to clear gift certificate draft", exception=e)

    # ============ User Booking Operations ============

    async def init_user_booking(self, update: Update) -> None:
        """Initialize a new user booking session for the user."""
        await self.clear_user_booking(update)
        await self.set_user_booking(update, UserBookingDraft())

    async def set_user_booking(self, update: Update, draft: UserBookingDraft) -> None:
        """Store user booking draft in Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"user_booking:{chat_id}"
            await self._store.set(key, draft.to_json(), self._ttl_seconds)
        except Exception as e:
            LoggerService.error(__name__, "Failed to save user booking draft", exception=e)

    async def get_user_booking(self, update: Update) -> Optional[UserBookingDraft]:
        """Retrieve user booking draft from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"user_booking:{chat_id}"
            data = await self._store.get(key)
            if data:
                return UserBookingDraft.from_json(data)
            return None
        except Exception as e:
            LoggerService.error(__name__, "Failed to get user booking draft", exception=e)
            return None

    async def update_user_booking_field(self, update: Update, field: str, value) -> None:
        """Update a single field in user booking draft."""
        try:
            draft = await self.get_user_booking(update)
            if not draft:
                draft = UserBookingDraft()
            setattr(draft, field, value)
            await self.set_user_booking(update, draft)
        except Exception as e:
            LoggerService.error(__name__, f"Failed to update user booking field: {field}", exception=e)

    async def clear_user_booking(self, update: Update) -> None:
        """Clear user booking draft from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"user_booking:{chat_id}"
            await self._store.delete(key)
        except Exception as e:
            LoggerService.error(__name__, "Failed to clear user booking draft", exception=e)

    # ============ Private Helper Methods ============

    def _get_chat_id(self, update: Update) -> int:
        """Extract chat_id from Update object."""
        return self._navigation_service.get_chat_id(update)

    def _cast_field(self, field: str, value):
        """Cast field values to appropriate types."""
        if field in ["start_date", "end_date", "start_booking_date", "finish_booking_date", "old_booking_date"]:
            return datetime.fromisoformat(value) if isinstance(value, str) else value
        elif field == "tariff":
            return Tariff[value] if isinstance(value, str) else value
        else:
            return value
