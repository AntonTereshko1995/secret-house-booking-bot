import base64
from datetime import datetime
import json
import socket
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.secret_manager_service import SecretManagerService
from src.services.logger_service import LoggerService
from src.helpers import string_helper, tariff_helper
from google.auth.exceptions import TransportError
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from db.models.user import UserBase
from db.models.booking import BookingBase
from singleton_decorator import singleton
from src.config.config import CALENDAR_ID
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)
import logging

SERVICE_ACCOUNT_FILE = "src/config/credentials.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
secret_manager_service = SecretManagerService()

_NETWORK_ERRORS = (OSError, TransportError, socket.error)

_retry_on_network = retry(
    retry=retry_if_exception_type(_NETWORK_ERRORS),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
    reraise=True,
)


@singleton
class CalendarService:
    def __init__(self):
        credentials_base64 = os.getenv("GOOGLE_CREDENTIALS")
        credentials_json = base64.b64decode(credentials_base64).decode("utf-8")
        credentials_dict = json.loads(credentials_json)

        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict, scopes=SCOPES
        )

        self.service = build("calendar", "v3", credentials=credentials)

    def add_event(self, booking: BookingBase, user: UserBase) -> str:
        try:
            return self._add_event(booking, user)
        except _NETWORK_ERRORS as e:
            LoggerService.error(__name__, "add_event: network unreachable after retries", e)
        except HttpError as e:
            LoggerService.error(__name__, f"add_event: Google API error {e.status_code}", e)
        except Exception as e:
            LoggerService.error(__name__, "add_event: unexpected error", e)

    @_retry_on_network
    def _add_event(self, booking: BookingBase, user: UserBase) -> str:
        event = {
            "summary": tariff_helper.get_name(booking.tariff),
            "description": string_helper.generate_booking_info_message(booking, user),
            "start": {
                "dateTime": booking.start_date.isoformat(),
                "timeZone": "Europe/Minsk",
            },
            "end": {
                "dateTime": booking.end_date.isoformat(),
                "timeZone": "Europe/Minsk",
            },
        }
        event = (
            self.service.events()
            .insert(calendarId=CALENDAR_ID, body=event)
            .execute()
        )
        print(f"Событие добавлено: {event.get('htmlLink')}")
        LoggerService.info(__name__, "add_event")
        return event["id"]

    def get_event_by_id(self, id: str):
        try:
            return self._get_event_by_id(id)
        except _NETWORK_ERRORS as e:
            LoggerService.error(__name__, f"get_event_by_id: network unreachable after retries, event_id={id}", e)
        except HttpError as e:
            LoggerService.error(__name__, f"get_event_by_id: Google API error {e.status_code}, event_id={id}", e)
        except Exception as e:
            LoggerService.error(__name__, f"get_event_by_id: unexpected error, event_id={id}", e)

    @_retry_on_network
    def _get_event_by_id(self, id: str):
        event = (
            self.service.events().get(calendarId=CALENDAR_ID, eventId=id).execute()
        )
        if not event:
            print("❌ Нет событий в указанное время.")
            return None

        LoggerService.info(__name__, "get_event_by_id")
        return event

    def move_event(
        self, event_id: str, start_datetime: datetime, finish_datetime: datetime,
        booking: BookingBase = None, user: UserBase = None
    ):
        """Move event to new time and optionally update description

        Args:
            event_id: Google Calendar event ID
            start_datetime: New start date and time
            finish_datetime: New end date and time
            booking: Optional booking object to update description
            user: Optional user object to update description
        """
        try:
            self._move_event(event_id, start_datetime, finish_datetime, booking, user)
        except _NETWORK_ERRORS as e:
            LoggerService.error(__name__, f"move_event: network unreachable after retries, event_id={event_id}", e)
        except HttpError as e:
            LoggerService.error(__name__, f"move_event: Google API error {e.status_code}, event_id={event_id}", e)
        except Exception as e:
            LoggerService.error(__name__, f"move_event: unexpected error, event_id={event_id}", e)

    @_retry_on_network
    def _move_event(
        self, event_id: str, start_datetime: datetime, finish_datetime: datetime,
        booking: BookingBase = None, user: UserBase = None
    ):
        event = self.get_event_by_id(event_id)
        if not event:
            LoggerService.warning(__name__, f"move_event: event not found, event_id={event_id}")
            return

        event["start"]["dateTime"] = start_datetime.isoformat()
        event["end"]["dateTime"] = finish_datetime.isoformat()

        if booking and user:
            event["summary"] = tariff_helper.get_name(booking.tariff)
            event["description"] = string_helper.generate_booking_info_message(
                booking, user
            )

        updated_event = (
            self.service.events()
            .update(calendarId=CALENDAR_ID, eventId=event["id"], body=event)
            .execute()
        )

        print(f"✅ Событие перенесено: {updated_event.get('htmlLink')}")
        LoggerService.info(__name__, "move_event")

    def update_event_info(self, event_id: str, booking: BookingBase, user: UserBase):
        """Update event description and summary without changing time

        Args:
            event_id: Google Calendar event ID
            booking: Booking object with updated information
            user: User object
        """
        try:
            self._update_event_info(event_id, booking, user)
        except _NETWORK_ERRORS as e:
            LoggerService.error(__name__, f"update_event_info: network unreachable after retries, event_id={event_id}", e)
        except HttpError as e:
            LoggerService.error(__name__, f"update_event_info: Google API error {e.status_code}, event_id={event_id}", e)
        except Exception as e:
            LoggerService.error(__name__, f"update_event_info: unexpected error, event_id={event_id}", e)

    @_retry_on_network
    def _update_event_info(self, event_id: str, booking: BookingBase, user: UserBase):
        event = self.get_event_by_id(event_id)
        if not event:
            LoggerService.warning(__name__, f"update_event_info: event not found, event_id={event_id}")
            return

        event["summary"] = tariff_helper.get_name(booking.tariff)
        event["description"] = string_helper.generate_booking_info_message(
            booking, user
        )

        updated_event = (
            self.service.events()
            .update(calendarId=CALENDAR_ID, eventId=event["id"], body=event)
            .execute()
        )

        print(f"✅ Информация события обновлена: {updated_event.get('htmlLink')}")
        LoggerService.info(__name__, "update_event_info")

    def cancel_event(self, event_id: str):
        try:
            self._cancel_event(event_id)
        except _NETWORK_ERRORS as e:
            LoggerService.error(__name__, f"cancel_event: network unreachable after retries, event_id={event_id}", e)
        except HttpError as e:
            LoggerService.error(__name__, f"cancel_event: Google API error {e.status_code}, event_id={event_id}", e)
        except Exception as e:
            LoggerService.error(__name__, f"cancel_event: unexpected error, event_id={event_id}", e)

    @_retry_on_network
    def _cancel_event(self, event_id: str):
        event = self.get_event_by_id(event_id)
        if not event:
            LoggerService.warning(__name__, f"cancel_event: event not found, event_id={event_id}")
            return

        event["colorId"] = 8
        event["summary"] = f"Отмена {event['summary']}"
        updated_event = (
            self.service.events()
            .update(calendarId=CALENDAR_ID, eventId=event_id, body=event)
            .execute()
        )
        print(f"✅ Событие {event['id']} успешно удалено.")
        LoggerService.info(__name__, "cancel_event")
