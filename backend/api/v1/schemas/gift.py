"""
Pydantic schemas for Gift Certificate API endpoints.
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class GiftBase(BaseModel):
    """Base gift certificate fields"""
    contact: str
    number: str
    tariff: str


class GiftCreate(GiftBase):
    """Schema for creating a gift certificate"""
    chat_id: int


class GiftResponse(GiftBase):
    """Schema for gift certificate responses"""
    id: int
    is_done: bool
    chat_id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GiftValidate(BaseModel):
    """Schema for validating a gift certificate"""
    certificate_number: str


class GiftValidateResponse(BaseModel):
    """Response for gift validation"""
    valid: bool
    gift: Optional[GiftResponse] = None
    message: Optional[str] = None
