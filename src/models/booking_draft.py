from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime
from enum import Enum
from telegram import Document, PhotoSize
from db.models.gift import GiftBase
from db.models.subscription import SubscriptionBase
from src.models.enum.booking_step import BookingStep
from src.models.enum.tariff import Tariff
from src.models.rental_price import RentalPrice
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class BookingDraft:
    user_contact: Optional[str] = None
    start_booking_date: Optional[datetime] = None
    finish_booking_date: Optional[datetime] = None
    tariff: Optional[Tariff] = None
    is_photoshoot_included: bool = False
    is_sauna_included: bool = False
    is_white_room_included: bool = False
    is_green_room_included: bool = False
    is_additional_bedroom_included: bool = False
    is_secret_room_included: bool = False
    number_of_guests: Optional[int] = None
    price: Optional[float] = None
    booking_comment: Optional[str] = None
    gift_id: Optional[int] = None
    subscription_id: Optional[int] = None
    photo: Optional[PhotoSize] = None
    document: Optional[Document] = None
    navigation_step: Optional[BookingStep] = None
    rental_rate: Optional[RentalPrice] = None