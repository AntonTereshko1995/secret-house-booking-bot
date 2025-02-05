from datetime import datetime
import sys
import os
from time import strptime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.helpers import string_helper, tariff_helper
from google.oauth2 import service_account
from googleapiclient.discovery import build
from db.models.user import UserBase
from db.models.booking import BookingBase
from singleton_decorator import singleton
from src.config.config import CALENDAR_ID

SERVICE_ACCOUNT_FILE = "src/config/credentials.json"  
SCOPES = ["https://www.googleapis.com/auth/calendar"]

@singleton
class CalendarService:
    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, 
            scopes=SCOPES)
        self.service = build("calendar", "v3", credentials=credentials)

    def add_event(self, booking: BookingBase, user: UserBase) -> str:
        event = {
            "summary": tariff_helper.get_name(booking.tariff),
            "description": string_helper.generate_info_message(booking, user),
            "start": {"dateTime": booking.start_date.isoformat(), "timeZone": "Europe/Minsk"},
            "end": {"dateTime": booking.end_date.isoformat(), "timeZone": "Europe/Minsk"},
        }
        event = self.service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print(f"Событие добавлено: {event.get('htmlLink')}")
        return event["id"]
    
    def get_event_by_id(self, id: str):
        event = self.service.events().get(calendarId=CALENDAR_ID, eventId=id).execute()
        if not event:
            print("❌ Нет событий в указанное время.")
            return
        
        return event
    
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
        except Exception as e:
            print(f"Error to move event: {e}")
        
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
        except Exception as e:
            print(f"Error to remove event: {e}")