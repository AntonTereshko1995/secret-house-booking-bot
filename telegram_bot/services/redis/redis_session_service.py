"""
Redis session service for managing booking and feedback data.
Provides high-level operations for storing and retrieving session data.
"""
from datetime import datetime, timedelta
from typing import Optional
from singleton_decorator import singleton
from telegram import Update
from telegram_bot.models.booking_draft import BookingDraft
from telegram_bot.models.feedback import Feedback
from telegram_bot.models.cancel_booking_draft import CancelBookingDraft
from telegram_bot.models.change_booking_draft import ChangeBookingDraft
from telegram_bot.models.gift_certificate_draft import GiftCertificateDraft
from telegram_bot.models.user_booking_draft import UserBookingDraft
from telegram_bot.models.enum.tariff import Tariff
from telegram_bot.services.navigation_service import NavigationService
from telegram_bot.services.redis.redis_connection import RedisConnection
from telegram_bot.services.logger_service import LoggerService


@singleton
class RedisSessionService:
    """
    Service for managing booking and feedback session data in Redis.
    Uses RedisConnection singleton for client access.
    """

    def __init__(self, ttl_hours: int = 24):
        """
        Initialize Redis session service.

        Args:
            ttl_hours: Time-to-live for stored data in hours (default: 24)
        """
        self._redis = RedisConnection()
        self._ttl = timedelta(hours=ttl_hours)
        self._navigation_service = NavigationService()
        LoggerService.info(__name__, f"RedisSessionService initialized with TTL={ttl_hours}h")

    # ============ Booking Operations ============

    def init_booking(self, update: Update) -> None:
        """Initialize a new booking session for the user."""
        self.clear_booking(update)
        self.set_booking(update, BookingDraft())

    def set_booking(self, update: Update, booking: BookingDraft) -> None:
        """Store booking object in Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"booking:{chat_id}"
            self._redis.client.setex(key, self._ttl, booking.to_json())
        except Exception as e:
            LoggerService.error(__name__, "Failed to save booking", exception=e)

    def get_booking(self, update: Update) -> Optional[BookingDraft]:
        """Retrieve booking object from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"booking:{chat_id}"
            data = self._redis.client.get(key)
            if data:
                return BookingDraft.from_json(data)
            return None
        except Exception as e:
            LoggerService.error(__name__, "Failed to get booking", exception=e)
            return None

    def update_booking_field(self, update: Update, field: str, value) -> None:
        """Update a single field in booking object."""
        try:
            booking = self.get_booking(update)
            if not booking:
                booking = BookingDraft()

            value = self._cast_field(field, value)
            setattr(booking, field, value)
            self.set_booking(update, booking)
        except Exception as e:
            LoggerService.error(__name__, f"Failed to update booking field: {field}", exception=e)

    def update_booking_fields(self, update: Update, fields: dict) -> None:
        """Update multiple fields in booking object."""
        try:
            booking = self.get_booking(update)
            if not booking:
                booking = BookingDraft()

            for field, value in fields.items():
                setattr(booking, field, self._cast_field(field, value))

            self.set_booking(update, booking)
        except Exception as e:
            LoggerService.error(__name__, "Failed to update booking fields", exception=e)

    def clear_booking(self, update: Update) -> None:
        """Clear booking data from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"booking:{chat_id}"
            self._redis.client.delete(key)
        except Exception as e:
            LoggerService.error(__name__, "Failed to clear booking", exception=e)

    # ============ Feedback Operations ============

    def init_feedback(self, update: Update) -> None:
        """Initialize feedback storage in Redis."""
        self.clear_feedback(update)
        self.set_feedback(update, Feedback())

    def set_feedback(self, update: Update, feedback: Feedback) -> None:
        """Store feedback object in Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"feedback:{chat_id}"
            self._redis.client.setex(key, self._ttl, feedback.to_json())
        except Exception as e:
            LoggerService.error(__name__, "Failed to save feedback", exception=e)

    def get_feedback(self, update: Update) -> Optional[Feedback]:
        """Retrieve feedback object from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"feedback:{chat_id}"
            data = self._redis.client.get(key)
            if data:
                return Feedback.from_json(data)
            return None
        except Exception as e:
            LoggerService.error(__name__, "Failed to get feedback", exception=e)
            return None

    def update_feedback_field(self, update: Update, field: str, value) -> None:
        """Update a single field in feedback object."""
        try:
            feedback = self.get_feedback(update)
            if not feedback:
                feedback = Feedback()
            setattr(feedback, field, value)
            self.set_feedback(update, feedback)
        except Exception as e:
            LoggerService.error(__name__, f"Failed to update feedback field: {field}", exception=e)

    def clear_feedback(self, update: Update) -> None:
        """Clear feedback data from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"feedback:{chat_id}"
            self._redis.client.delete(key)
        except Exception as e:
            LoggerService.error(__name__, "Failed to clear feedback", exception=e)

    # ============ Private Helper Methods ============

    def _get_chat_id(self, update: Update) -> int:
        """Extract chat_id from Update object."""
        return self._navigation_service.get_chat_id(update)

    def _cast_field(self, field: str, value):
        """Cast field values to appropriate types."""
        if field in ["start_date", "end_date"]:
            return datetime.fromisoformat(value) if isinstance(value, str) else value
        elif field == "tariff":
            return Tariff[value] if isinstance(value, str) else value
        else:
            return value

    # ============ Cancel Booking Operations ============

    def init_cancel_booking(self, update: Update) -> None:
        """Initialize a new cancel booking session for the user."""
        self.clear_cancel_booking(update)
        self.set_cancel_booking(update, CancelBookingDraft())

    def set_cancel_booking(self, update: Update, draft: CancelBookingDraft) -> None:
        """Store cancel booking draft in Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"cancel_booking:{chat_id}"
            self._redis.client.setex(key, self._ttl, draft.to_json())
        except Exception as e:
            LoggerService.error(__name__, "Failed to save cancel booking draft", exception=e)

    def get_cancel_booking(self, update: Update) -> Optional[CancelBookingDraft]:
        """Retrieve cancel booking draft from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"cancel_booking:{chat_id}"
            data = self._redis.client.get(key)
            if data:
                return CancelBookingDraft.from_json(data)
            return None
        except Exception as e:
            LoggerService.error(__name__, "Failed to get cancel booking draft", exception=e)
            return None

    def update_cancel_booking_field(self, update: Update, field: str, value) -> None:
        """Update a single field in cancel booking draft."""
        try:
            draft = self.get_cancel_booking(update)
            if not draft:
                draft = CancelBookingDraft()
            setattr(draft, field, value)
            self.set_cancel_booking(update, draft)
        except Exception as e:
            LoggerService.error(__name__, f"Failed to update cancel booking field: {field}", exception=e)

    def clear_cancel_booking(self, update: Update) -> None:
        """Clear cancel booking draft from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"cancel_booking:{chat_id}"
            self._redis.client.delete(key)
        except Exception as e:
            LoggerService.error(__name__, "Failed to clear cancel booking draft", exception=e)

    # ============ Change Booking Date Operations ============

    def init_change_booking(self, update: Update) -> None:
        """Initialize a new change booking session for the user."""
        self.clear_change_booking(update)
        self.set_change_booking(update, ChangeBookingDraft())

    def set_change_booking(self, update: Update, draft: ChangeBookingDraft) -> None:
        """Store change booking draft in Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"change_booking:{chat_id}"
            self._redis.client.setex(key, self._ttl, draft.to_json())
        except Exception as e:
            LoggerService.error(__name__, "Failed to save change booking draft", exception=e)

    def get_change_booking(self, update: Update) -> Optional[ChangeBookingDraft]:
        """Retrieve change booking draft from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"change_booking:{chat_id}"
            data = self._redis.client.get(key)
            if data:
                return ChangeBookingDraft.from_json(data)
            return None
        except Exception as e:
            LoggerService.error(__name__, "Failed to get change booking draft", exception=e)
            return None

    def update_change_booking_field(self, update: Update, field: str, value) -> None:
        """Update a single field in change booking draft."""
        try:
            draft = self.get_change_booking(update)
            if not draft:
                draft = ChangeBookingDraft()
            setattr(draft, field, value)
            self.set_change_booking(update, draft)
        except Exception as e:
            LoggerService.error(__name__, f"Failed to update change booking field: {field}", exception=e)

    def clear_change_booking(self, update: Update) -> None:
        """Clear change booking draft from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"change_booking:{chat_id}"
            self._redis.client.delete(key)
        except Exception as e:
            LoggerService.error(__name__, "Failed to clear change booking draft", exception=e)

    # ============ Gift Certificate Operations ============

    def init_gift_certificate(self, update: Update) -> None:
        """Initialize a new gift certificate session for the user."""
        self.clear_gift_certificate(update)
        self.set_gift_certificate(update, GiftCertificateDraft())

    def set_gift_certificate(self, update: Update, draft: GiftCertificateDraft) -> None:
        """Store gift certificate draft in Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"gift_certificate:{chat_id}"
            self._redis.client.setex(key, self._ttl, draft.to_json())
        except Exception as e:
            LoggerService.error(__name__, "Failed to save gift certificate draft", exception=e)

    def get_gift_certificate(self, update: Update) -> Optional[GiftCertificateDraft]:
        """Retrieve gift certificate draft from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"gift_certificate:{chat_id}"
            data = self._redis.client.get(key)
            if data:
                return GiftCertificateDraft.from_json(data)
            return None
        except Exception as e:
            LoggerService.error(__name__, "Failed to get gift certificate draft", exception=e)
            return None

    def update_gift_certificate_field(self, update: Update, field: str, value) -> None:
        """Update a single field in gift certificate draft."""
        try:
            draft = self.get_gift_certificate(update)
            if not draft:
                draft = GiftCertificateDraft()
            setattr(draft, field, value)
            self.set_gift_certificate(update, draft)
        except Exception as e:
            LoggerService.error(__name__, f"Failed to update gift certificate field: {field}", exception=e)

    def clear_gift_certificate(self, update: Update) -> None:
        """Clear gift certificate draft from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"gift_certificate:{chat_id}"
            self._redis.client.delete(key)
        except Exception as e:
            LoggerService.error(__name__, "Failed to clear gift certificate draft", exception=e)

    # ============ User Booking Operations ============

    def init_user_booking(self, update: Update) -> None:
        """Initialize a new user booking session for the user."""
        self.clear_user_booking(update)
        self.set_user_booking(update, UserBookingDraft())

    def set_user_booking(self, update: Update, draft: UserBookingDraft) -> None:
        """Store user booking draft in Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"user_booking:{chat_id}"
            self._redis.client.setex(key, self._ttl, draft.to_json())
        except Exception as e:
            LoggerService.error(__name__, "Failed to save user booking draft", exception=e)

    def get_user_booking(self, update: Update) -> Optional[UserBookingDraft]:
        """Retrieve user booking draft from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"user_booking:{chat_id}"
            data = self._redis.client.get(key)
            if data:
                return UserBookingDraft.from_json(data)
            return None
        except Exception as e:
            LoggerService.error(__name__, "Failed to get user booking draft", exception=e)
            return None

    def update_user_booking_field(self, update: Update, field: str, value) -> None:
        """Update a single field in user booking draft."""
        try:
            draft = self.get_user_booking(update)
            if not draft:
                draft = UserBookingDraft()
            setattr(draft, field, value)
            self.set_user_booking(update, draft)
        except Exception as e:
            LoggerService.error(__name__, f"Failed to update user booking field: {field}", exception=e)

    def clear_user_booking(self, update: Update) -> None:
        """Clear user booking draft from Redis."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"user_booking:{chat_id}"
            self._redis.client.delete(key)
        except Exception as e:
            LoggerService.error(__name__, "Failed to clear user booking draft", exception=e)
