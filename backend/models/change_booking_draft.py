from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class ChangeBookingDraft:
    """Draft data for change booking date flow to avoid global variables"""
    user_contact: Optional[str] = None
    selected_bookings: Optional[List[int]] = None  # List of booking IDs
    selected_booking_id: Optional[int] = None
    old_booking_date: Optional[datetime] = None
    start_booking_date: Optional[datetime] = None
    finish_booking_date: Optional[datetime] = None
    booking_price: Optional[int] = None  # Original booking price
    booking_tariff: Optional[str] = None  # For validation
    booking_has_sauna: Optional[bool] = None
    booking_has_photoshoot: Optional[bool] = None
    booking_has_secret_room: Optional[bool] = None
    booking_has_white_bedroom: Optional[bool] = None
    booking_has_green_bedroom: Optional[bool] = None
