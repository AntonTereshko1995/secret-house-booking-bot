from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from telegram import Document, PhotoSize
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
    photo: Optional[PhotoSize] = None
    document: Optional[Document] = None
    navigation_step: Optional[BookingStep] = None
    rental_rate: Optional[RentalPrice] = None
    wine_preference: Optional[str] = None
    transfer_address: Optional[str] = None
    promocode_id: Optional[int] = None
    promocode_discount: Optional[float] = None
    prepayment_price: Optional[float] = None
