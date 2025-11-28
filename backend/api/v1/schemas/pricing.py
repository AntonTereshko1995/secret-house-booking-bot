"""
Pydantic schemas for Pricing API endpoints.
"""
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class PriceCalculationRequest(BaseModel):
    """Request for price calculation"""
    tariff: str
    start_date: datetime
    end_date: datetime
    has_sauna: bool = False
    has_secret_room: bool = False
    has_second_bedroom: bool = False
    has_photoshoot: bool = False
    number_of_guests: int = 2


class PriceCalculationResponse(BaseModel):
    """Response with price breakdown"""
    base_price: float
    sauna_price: float = 0
    secret_room_price: float = 0
    second_bedroom_price: float = 0
    photoshoot_price: float = 0
    extra_people_price: float = 0
    extra_hours_price: float = 0
    total_price: float
    duration_hours: int
    currency: str = "BYN"


class TariffResponse(BaseModel):
    """Response for tariff information"""
    tariff: str
    name: str
    price: float
    duration_hours: int
    max_people: int
    sauna_price: float
    secret_room_price: float
    second_bedroom_price: float
    photoshoot_price: float
    extra_people_price: float
    extra_hour_price: float
    multi_day_prices: Optional[dict] = None
