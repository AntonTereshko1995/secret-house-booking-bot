from datetime import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.helpers import tariff_helper
import database
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

    def add_event(self, booking: BookingBase, user: UserBase):
        event = {
            "summary": tariff_helper.get_name(booking.tariff),
            "description": CALENDAR_ID,
            "start": {"dateTime": booking.start_date.isoformat(), "timeZone": "Europe/Minsk"},
            "end": {"dateTime": booking.end_date.isoformat(), "timeZone": "Europe/Minsk"},
        }
        event = self.service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print(f"Событие добавлено {event.get("id")}: {event.get('htmlLink')}")
    
    def get_events(self):
        now = datetime.datetime.utcnow().isoformat() + "Z"
        events_result = self.service.events().list(
            calendarId=CALENDAR_ID, timeMin=now, maxResults=5, singleEvents=True, orderBy="startTime"
        ).execute()
        events = events_result.get("items", [])
        
        if not events:
            return "Нет предстоящих событий."

        event_list = []
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            event_list.append(f"{start} - {event['summary']}")
        return "\n".join(event_list)