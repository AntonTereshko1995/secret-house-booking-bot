from dataclasses import dataclass
from typing import Optional
from dataclasses_json import dataclass_json
from telegram_bot.models.enum.tariff import Tariff
from telegram_bot.models.rental_price import RentalPrice


@dataclass_json
@dataclass
class GiftCertificateDraft:
    """Draft data for gift certificate flow to avoid global variables"""
    user_contact: Optional[str] = None
    tariff: Optional[Tariff] = None
    is_sauna_included: Optional[bool] = None
    is_secret_room_included: Optional[bool] = None
    is_additional_bedroom_included: Optional[bool] = None
    rental_rate: Optional[RentalPrice] = None
    price: Optional[int] = None
