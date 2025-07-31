import redis
import json
from datetime import datetime, timedelta
from typing import Optional, Type, TypeVar
from singleton_decorator import singleton
from telegram import Update
from src.models.booking_draft import BookingDraft
from src.models.enum.tariff import Tariff
from src.models.rental_price import RentalPrice
from src.services.navigation_service import NavigatonService

T = TypeVar('T')  # Generic type for model classes

@singleton
class RedisService:
    def __init__(self, host='data/', port=6379, db=0, ttl_hours=24):
        self.__client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
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