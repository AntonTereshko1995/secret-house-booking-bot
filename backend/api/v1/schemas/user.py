"""
Pydantic schemas for User API endpoints.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional


class UserBase(BaseModel):
    """Base user fields"""
    contact: Optional[str] = None
    user_name: Optional[str] = None
    chat_id: Optional[int] = None


class UserCreate(UserBase):
    """Schema for creating/updating a user"""
    pass


class UserResponse(UserBase):
    """Schema for user responses"""
    id: int
    has_bookings: bool
    total_bookings: int
    completed_bookings: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserStatistics(BaseModel):
    """User booking statistics"""
    user_id: int
    user_name: Optional[str]
    contact: Optional[str]
    total_bookings: int
    completed_bookings: int
    active_bookings: int
    canceled_bookings: int
