"""
Availability API endpoints for checking booking dates.
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
from backend.api.v1.schemas.booking import AvailabilityCheck, AvailabilityResponse
from backend.services.booking_service import BookingService
from backend.services.logger_service import LoggerService

router = APIRouter()


@router.post("/check", response_model=AvailabilityResponse)
async def check_availability(
    availability_check: AvailabilityCheck,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Check if dates are available for booking.
    Returns availability status and list of conflicting bookings if any.
    """
    try:
        booking_service = BookingService()

        is_booked = booking_service.is_booking_between_dates(
            start=availability_check.start_date,
            end=availability_check.end_date
        )

        conflicting_bookings = []
        if is_booked:
            # Get the conflicting bookings for details
            # Calculate the date range to check
            start_date = availability_check.start_date.date()
            end_date = availability_check.end_date.date()

            bookings = booking_service.get_booking_by_start_date_period(
                from_date=start_date,
                to_date=end_date,
                is_admin=False
            )

            conflicting_bookings = [
                {
                    "id": booking.id,
                    "start_date": booking.start_date.isoformat(),
                    "end_date": booking.end_date.isoformat()
                }
                for booking in (bookings or [])
            ]

        return AvailabilityResponse(
            available=not is_booked,
            conflicting_bookings=conflicting_bookings
        )

    except Exception as e:
        LoggerService.error(__name__, "check_availability failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while checking availability"
        )


@router.get("/month/{year}/{month}")
async def get_month_availability(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get all bookings for a specific month.
    Returns calendar-friendly format with occupied dates.
    """
    try:
        booking_service = BookingService()

        bookings = booking_service.get_bookings_by_month(
            target_month=month,
            target_year=year
        )

        # Format response
        occupied_dates = []
        booking_details = []

        for booking in (bookings or []):
            booking_details.append({
                "id": booking.id,
                "start_date": booking.start_date.isoformat(),
                "end_date": booking.end_date.isoformat(),
                "tariff": booking.tariff.value if hasattr(booking.tariff, 'value') else str(booking.tariff)
            })

            # Add all dates in the booking range to occupied_dates
            current_date = booking.start_date.date()
            end_date = booking.end_date.date()

            while current_date <= end_date:
                if current_date.isoformat() not in occupied_dates:
                    occupied_dates.append(current_date.isoformat())
                current_date = date.fromordinal(current_date.toordinal() + 1)

        return {
            "year": year,
            "month": month,
            "occupied_dates": sorted(occupied_dates),
            "bookings": booking_details
        }

    except Exception as e:
        LoggerService.error(__name__, "get_month_availability failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching month availability"
        )


@router.get("/dates")
async def get_available_dates(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get occupied dates within a date range.
    Returns list of dates that are not available.
    """
    try:
        booking_service = BookingService()

        bookings = booking_service.get_booking_by_start_date_period(
            from_date=start_date,
            to_date=end_date,
            is_admin=False
        )

        occupied_dates = []

        for booking in (bookings or []):
            # Add all dates in the booking range
            current_date = booking.start_date.date()
            booking_end = booking.end_date.date()

            while current_date <= booking_end:
                date_str = current_date.isoformat()
                if date_str not in occupied_dates:
                    occupied_dates.append(date_str)
                current_date = date.fromordinal(current_date.toordinal() + 1)

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "occupied_dates": sorted(occupied_dates)
        }

    except Exception as e:
        LoggerService.error(__name__, "get_available_dates failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching available dates"
        )
