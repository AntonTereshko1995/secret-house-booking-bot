import sys
import os
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from src.models.enum.tariff import Tariff
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@dataclass_json
@dataclass
class RentalPrice:
    tariff: Tariff
    name: str
    duration_hours: int
    price: int
    sauna_price: int
    secret_room_price: int
    second_bedroom_price: int
    extra_hour_price: int
    extra_people_price: int
    photoshoot_price: int
    max_people: int
    is_check_in_time_limit: bool
    is_photoshoot: bool
    is_transfer: bool
    multi_day_prices: dict