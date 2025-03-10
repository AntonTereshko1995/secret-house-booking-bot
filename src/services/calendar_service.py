import base64
from datetime import datetime
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.secret_manager_service import SecretManagerService
from src.services.logger_service import LoggerService
from src.helpers import string_helper, tariff_helper
from google.oauth2 import service_account
from googleapiclient.discovery import build
from db.models.user import UserBase
from db.models.booking import BookingBase
from singleton_decorator import singleton
from src.config.config import CALENDAR_ID, GOOGLE_CREDENTIALS

SERVICE_ACCOUNT_FILE = "src/config/credentials.json"  
SCOPES = ["https://www.googleapis.com/auth/calendar"]
secret_manager_service = SecretManagerService()

@singleton
class CalendarService:
    def __init__(self):

        # Local file
        # credentials = service_account.Credentials.from_service_account_file(
        #     SERVICE_ACCOUNT_FILE, 
        #     scopes=SCOPES)
        
        # Google cloud
        # credentials_json = secret_manager_service.get_secret("GOOGLE_CREDENTIALS")

        # Getenv
        credentials_base64 = os.getenv("GOOGLE_CREDENTIALS")
        credentials_json = base64.b64decode(credentials_base64).decode("utf-8")
        credentials_dict = json.loads(credentials_json)

        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict, 
            scopes=SCOPES)

        self.service = build("calendar", "v3", credentials=credentials)

    def add_event(self, booking: BookingBase, user: UserBase) -> str:
        try:
            event = {
                "summary": tariff_helper.get_name(booking.tariff),
                "description": string_helper.generate_booking_info_message(booking, user),
                "start": {"dateTime": booking.start_date.isoformat(), "timeZone": "Europe/Minsk"},
                "end": {"dateTime": booking.end_date.isoformat(), "timeZone": "Europe/Minsk"},
            }
            event = self.service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
            print(f"Событие добавлено: {event.get('htmlLink')}")
            LoggerService.info(__name__, f"add_event")
            return event["id"]
        except Exception as e:
            print(f"Error to add event: {e}")
            LoggerService.error(__name__, f"add_event", e)
    
    def get_event_by_id(self, id: str):
        try:
            event = self.service.events().get(calendarId=CALENDAR_ID, eventId=id).execute()
            if not event:
                print("❌ Нет событий в указанное время.")
                return
            
            LoggerService.info(__name__, f"get_event_by_id")
            return event
        except Exception as e:
            print(f"Error to get event by id: {e}")
            LoggerService.error(__name__, f"get_event_by_id", e)
    
    def move_event(self, event_id: str, start_datetime: datetime, finish_datetime: datetime):
        try:
            event = self.get_event_by_id(event_id)
            if not event:
                # TODO: log
                return;
        
            event["start"]["dateTime"] = start_datetime.isoformat()
            event["end"]["dateTime"] = finish_datetime.isoformat()
            updated_event = self.service.events().update(calendarId=CALENDAR_ID, eventId=event["id"], body=event).execute()
            
            print(f"✅ Событие перенесено: {updated_event.get('htmlLink')}")
            LoggerService.info(__name__, f"move_event")
        except Exception as e:
            print(f"Error to move event: {e}")
            LoggerService.error(__name__, f"move_event", e)
        
    def cancel_event(self, event_id: str):
        try:
            event = self.get_event_by_id(event_id)
            if not event:
                # TODO: log
                return;
        
            event = self.service.events().get(calendarId=CALENDAR_ID, eventId=event_id).execute()
            event["colorId"] = 8
            event["summary"] = f"Отмена {event['summary']}"
            updated_event = self.service.events().update(
                calendarId=CALENDAR_ID, 
                eventId=event_id, 
                body=event).execute()
            print(f"✅ Событие {event['id']} успешно удалено.")
            LoggerService.info(__name__, f"cancel_event")
        except Exception as e:
            print(f"Error to remove event: {e}")
            LoggerService.error(__name__, f"cancel_event", e)

 