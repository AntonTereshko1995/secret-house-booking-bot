"""
Pydantic schemas for Booking API endpoints.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class BookingBase(BaseModel):
    """Base booking fields shared across requests"""
    start_date: datetime
    end_date: datetime
    tariff: str
    number_of_guests: int
    has_sauna: bool = False
    has_photoshoot: bool = False
    has_white_bedroom: bool = False
    has_green_bedroom: bool = False
    has_secret_room: bool = False
    comment: Optional[str] = None
    wine_preference: Optional[str] = None
    transfer_address: Optional[str] = None


class BookingCreate(BookingBase):
    """Schema for creating a new booking"""
    user_contact: str
    chat_id: int
    gift_id: Optional[int] = None
    promocode_id: Optional[int] = None
    price: Optional[float] = None


class BookingUpdate(BaseModel):
    """Schema for updating an existing booking"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_canceled: Optional[bool] = None
    is_prepaymented: Optional[bool] = None
    is_done: Optional[bool] = None
    price: Optional[float] = None
    prepayment_price: Optional[float] = None
    calendar_event_id: Optional[str] = None


class BookingResponse(BookingBase):
    """Schema for booking responses"""
    id: int
    user_id: int
    price: float
    prepayment_price: float
    is_prepaymented: bool
    is_canceled: bool
    is_done: bool
    is_date_changed: bool
    feedback_submitted: bool
    calendar_event_id: Optional[str] = None
    gift_id: Optional[int] = None
    promocode_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class AvailabilityCheck(BaseModel):
    """Schema for checking date availability"""
    start_date: datetime
    end_date: datetime
    except_booking_id: Optional[int] = None


class AvailabilityResponse(BaseModel):
    """Response for availability check"""
    available: bool
    conflicting_bookings: list[dict] = []
