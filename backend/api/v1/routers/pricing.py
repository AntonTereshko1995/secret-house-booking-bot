"""
Pricing API endpoints for tariff and price calculations.
"""
import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

# Add parent paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from backend.api.v1.dependencies import get_db, verify_api_key
from backend.api.v1.schemas.pricing import (
    PriceCalculationRequest,
    PriceCalculationResponse,
    TariffResponse
)
from backend.services.calculation_rate_service import CalculationRateService
from backend.services.logger_service import LoggerService
from backend.models.enum.tariff import Tariff

router = APIRouter()


@router.post("/calculate", response_model=PriceCalculationResponse)
async def calculate_price(
    calc_request: PriceCalculationRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Calculate price for a booking with all add-ons.
    Returns detailed price breakdown.
    """
    try:
        calc_service = CalculationRateService()

        # Convert tariff string to enum
        try:
            tariff_enum = Tariff[calc_request.tariff]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tariff: {calc_request.tariff}"
            )

        # Calculate duration in hours
        duration = calc_request.end_date - calc_request.start_date
        duration_hours = int(duration.total_seconds() / 3600)

        # Get base price for the date and tariff
        booking_date = calc_request.start_date.date()
        base_price = calc_service.get_effective_price_for_date(
            booking_date=booking_date,
            tariff=tariff_enum,
            duration_hours=duration_hours
        )

        # Get rental price info for add-on prices
        rental_price = calc_service.get_by_tariff(tariff_enum)
        if not rental_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No pricing found for tariff: {calc_request.tariff}"
            )

        # Calculate add-on prices
        sauna_price = rental_price.sauna_price if calc_request.has_sauna else 0
        secret_room_price = rental_price.secret_room_price if calc_request.has_secret_room else 0
        second_bedroom_price = rental_price.second_bedroom_price if calc_request.has_second_bedroom else 0
        photoshoot_price = rental_price.photoshoot_price if calc_request.has_photoshoot else 0

        # Calculate extra people price
        extra_people_price = 0
        if calc_request.number_of_guests > rental_price.max_people:
            extra_people = calc_request.number_of_guests - rental_price.max_people
            extra_people_price = extra_people * rental_price.extra_people_price

        # Calculate extra hours price (already included in base_price for date-specific pricing)
        extra_hours_price = 0

        # Total price
        total_price = (
            base_price +
            sauna_price +
            secret_room_price +
            second_bedroom_price +
            photoshoot_price +
            extra_people_price +
            extra_hours_price
        )

        return PriceCalculationResponse(
            base_price=base_price,
            sauna_price=sauna_price,
            secret_room_price=secret_room_price,
            second_bedroom_price=second_bedroom_price,
            photoshoot_price=photoshoot_price,
            extra_people_price=extra_people_price,
            extra_hours_price=extra_hours_price,
            total_price=total_price,
            duration_hours=duration_hours,
            currency="BYN"
        )

    except HTTPException:
        raise
    except Exception as e:
        LoggerService.error(__name__, "calculate_price failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while calculating price"
        )


@router.get("/tariffs", response_model=List[TariffResponse])
async def list_tariffs(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    List all available tariffs with pricing information.
    """
    try:
        calc_service = CalculationRateService()
        tariffs = calc_service._try_load_tariffs()

        tariff_responses = []
        for tariff in tariffs:
            tariff_responses.append(TariffResponse(
                tariff=tariff.tariff,
                name=tariff.name,
                price=tariff.price,
                duration_hours=tariff.duration_hours,
                max_people=tariff.max_people,
                sauna_price=tariff.sauna_price,
                secret_room_price=tariff.secret_room_price,
                second_bedroom_price=tariff.second_bedroom_price,
                photoshoot_price=tariff.photoshoot_price,
                extra_people_price=tariff.extra_people_price,
                extra_hour_price=tariff.extra_hour_price,
                multi_day_prices=tariff.multi_day_prices
            ))

        return tariff_responses

    except Exception as e:
        LoggerService.error(__name__, "list_tariffs failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching tariffs"
        )
