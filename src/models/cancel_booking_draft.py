from dataclasses import dataclass
from typing import Optional, List
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class CancelBookingDraft:
    """Draft data for cancel booking flow to avoid global variables"""
    user_contact: Optional[str] = None
    selected_bookings: Optional[List[int]] = None  # List of booking IDs
    selected_booking_id: Optional[int] = None
