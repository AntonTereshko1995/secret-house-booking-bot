"""
Pydantic schemas for Promocode API endpoints.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional


class PromocodeBase(BaseModel):
    """Base promocode fields"""
    code: str
    discount_percentage: float
    promocode_type: str


class PromocodeCreate(PromocodeBase):
    """Schema for creating a promocode"""
    is_active: bool = True


class PromocodeResponse(PromocodeBase):
    """Schema for promocode responses"""
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class PromocodeValidate(BaseModel):
    """Schema for validating a promocode"""
    code: str


class PromocodeValidateResponse(BaseModel):
    """Response for promocode validation"""
    valid: bool
    discount_percentage: Optional[float] = None
    promocode: Optional[PromocodeResponse] = None
    message: Optional[str] = None
