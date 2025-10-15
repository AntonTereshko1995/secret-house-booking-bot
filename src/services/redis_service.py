import redis
from datetime import datetime, timedelta
from typing import Optional
from singleton_decorator import singleton
from telegram import Update
from src.models.booking_draft import BookingDraft
from src.models.feedback import Feedback
from src.models.enum.tariff import Tariff
from src.services.navigation_service import NavigatonService
from src.config.config import REDIS_URL, REDIS_PORT, REDIS_SSL


@singleton
class RedisService:
    def __init__(self, ttl_hours=24):
        self.__client = redis.Redis(
            host=REDIS_URL,
            port=REDIS_PORT,
            decode_responses=True,
            ssl=REDIS_SSL,
            ssl_cert_reqs=None,
        )
        self.__ttl = timedelta(hours=ttl_hours)
        self.__navigaton_service = NavigatonService()

    def init_booking(self, update: Update):
        self.clear_booking(update)
        self.set_booking(update, BookingDraft())

    def set_booking(self, update: Update, booking: BookingDraft):
        chat_id = self.__navigaton_service.get_chat_id(update)
        key = f"booking:{chat_id}"
        self.__client.setex(key, self.__ttl, booking.to_json())

    def get_booking(self, update: Update) -> Optional[BookingDraft]:
        chat_id = self.__navigaton_service.get_chat_id(update)
        key = f"booking:{chat_id}"
        data = self.__client.get(key)
        if data:
            return BookingDraft.from_json(data)
        return None

    def update_booking_field(self, update: Update, field: str, value):
        booking = self.get_booking(update)
        if not booking:
            booking = BookingDraft()

        value = self._cast_field(field, value)
        setattr(booking, field, value)
        self.set_booking(update, booking)

    def update_booking_fields(self, update: Update, fields: dict):
        chat_id = self.__navigaton_service.get_chat_id(update)
        booking = self.get_booking(update)
        if not booking:
            booking = BookingDraft()

        for field, value in fields.items():
            setattr(booking, field, self._cast_field(field, value))

        self.set_booking(chat_id, booking)

    def clear_booking(self, update: Update):
        chat_id = self.__navigaton_service.get_chat_id(update)
        key = f"booking:{chat_id}"
        self.__client.delete(key)

    def _cast_field(self, field: str, value):
        if field in ["start_date", "end_date"]:
            return datetime.fromisoformat(value) if isinstance(value, str) else value
        elif field == "tariff":
            return Tariff[value] if isinstance(value, str) else value
        else:
            return value

    # Feedback methods
    def init_feedback(self, update: Update):
        """Initialize feedback storage in Redis"""
        self.clear_feedback(update)
        self.set_feedback(update, Feedback())

    def set_feedback(self, update: Update, feedback: Feedback):
        """Store feedback object in Redis"""
        chat_id = self.__navigaton_service.get_chat_id(update)
        key = f"feedback:{chat_id}"
        self.__client.setex(key, self.__ttl, feedback.to_json())

    def get_feedback(self, update: Update) -> Optional[Feedback]:
        """Retrieve feedback object from Redis"""
        chat_id = self.__navigaton_service.get_chat_id(update)
        key = f"feedback:{chat_id}"
        data = self.__client.get(key)
        if data:
            return Feedback.from_json(data)
        return None

    def update_feedback_field(self, update: Update, field: str, value):
        """Update a single field in feedback object"""
        feedback = self.get_feedback(update)
        if not feedback:
            feedback = Feedback()
        setattr(feedback, field, value)
        self.set_feedback(update, feedback)

    def clear_feedback(self, update: Update):
        """Clear feedback data from Redis"""
        chat_id = self.__navigaton_service.get_chat_id(update)
        key = f"feedback:{chat_id}"
        self.__client.delete(key)
