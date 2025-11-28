"""
Booking API endpoints.
"""
import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

# Add parent paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from backend.api.v1.dependencies import get_db, verify_api_key
from backend.api.v1.schemas.booking import (
    BookingCreate,
    BookingUpdate,
    BookingResponse,
)
from backend.services.booking_service import BookingService
from backend.services.calendar_service import CalendarService
from backend.services.logger_service import LoggerService
from backend.models.enum.tariff import Tariff

router = APIRouter()


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Create a new booking.
    Requires API authentication.
    """
    try:
        booking_service = BookingService()

        # Convert tariff string to enum
        tariff_enum = Tariff[booking_data.tariff]

        # Create booking
        new_booking = booking_service.add_booking(
            user_contact=booking_data.user_contact,
            start_date=booking_data.start_date,
            end_date=booking_data.end_date,
            tariff=tariff_enum,
            has_photoshoot=booking_data.has_photoshoot,
            has_sauna=booking_data.has_sauna,
            has_white_bedroom=booking_data.has_white_bedroom,
            has_green_bedroom=booking_data.has_green_bedroom,
            has_secret_room=booking_data.has_secret_room,
            number_of_guests=booking_data.number_of_guests,
            price=booking_data.price or 0,
            comment=booking_data.comment or "",
            chat_id=booking_data.chat_id,
            gift_id=booking_data.gift_id,
            promocode_id=booking_data.promocode_id,
            wine_preference=booking_data.wine_preference,
            transfer_address=booking_data.transfer_address,
        )

        if not new_booking:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create booking"
            )

        return new_booking

    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tariff: {booking_data.tariff}"
        )
    except Exception as e:
        LoggerService.error(__name__, "create_booking failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the booking"
        )


@router.get("", response_model=List[BookingResponse])
async def list_bookings(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    user_contact: Optional[str] = Query(None),
    is_admin: bool = Query(False),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    List bookings with optional filters.
    Requires API authentication.
    """
    try:
        booking_service = BookingService()

        if user_contact:
            bookings = booking_service.get_booking_by_user_contact(user_contact)
        elif start_date and end_date:
            bookings = booking_service.get_booking_by_start_date_period(
                from_date=start_date,
                to_date=end_date,
                is_admin=is_admin
            )
        elif start_date:
            bookings = booking_service.get_booking_by_start_date(start_date)
        else:
            # Return empty list if no filters provided
            bookings = []

        return bookings or []

    except Exception as e:
        LoggerService.error(__name__, "list_bookings failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching bookings"
        )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get a specific booking by ID.
    Requires API authentication.
    """
    try:
        booking_service = BookingService()
        booking = booking_service.get_booking_by_id(booking_id)

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found"
            )

        return booking

    except HTTPException:
        raise
    except Exception as e:
        LoggerService.error(__name__, "get_booking failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the booking"
        )


@router.patch("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: int,
    booking_update: BookingUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Update a booking.
    Requires API authentication.
    """
    try:
        booking_service = BookingService()

        # Check if booking exists
        existing_booking = booking_service.get_booking_by_id(booking_id)
        if not existing_booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found"
            )

        # Update booking
        updated_booking = booking_service.update_booking(
            booking_id=booking_id,
            start_date=booking_update.start_date,
            end_date=booking_update.end_date,
            is_canceled=booking_update.is_canceled,
            is_date_changed=None,  # Not in schema
            price=booking_update.price,
            is_prepaymented=booking_update.is_prepaymented,
            calendar_event_id=booking_update.calendar_event_id,
            is_done=booking_update.is_done,
            prepayment=booking_update.prepayment_price,
        )

        return updated_booking

    except HTTPException:
        raise
    except Exception as e:
        LoggerService.error(__name__, "update_booking failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the booking"
        )


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Cancel a booking (soft delete).
    Requires API authentication.
    """
    try:
        booking_service = BookingService()
        calendar_service = CalendarService()

        # Check if booking exists
        existing_booking = booking_service.get_booking_by_id(booking_id)
        if not existing_booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found"
            )

        # Delete from Google Calendar if event exists
        if existing_booking.calendar_event_id:
            try:
                calendar_service.delete_event(existing_booking.calendar_event_id)
            except Exception as e:
                LoggerService.error(__name__, "Failed to delete calendar event", e)
                # Continue with booking cancellation even if calendar delete fails

        # Cancel booking
        booking_service.update_booking(
            booking_id=booking_id,
            is_canceled=True
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        LoggerService.error(__name__, "cancel_booking failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while canceling the booking"
        )


@router.get("/user/{user_contact}", response_model=List[BookingResponse])
async def get_user_bookings(
    user_contact: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get all bookings for a specific user.
    Requires API authentication.
    """
    try:
        booking_service = BookingService()
        bookings = booking_service.get_booking_by_user_contact(user_contact)

        return bookings or []

    except Exception as e:
        LoggerService.error(__name__, "get_user_bookings failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching user bookings"
        )
