"""
Gift Certificate API endpoints.
"""
import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Add parent paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from backend.api.v1.dependencies import get_db, verify_api_key
from backend.api.v1.schemas.gift import (
    GiftCreate,
    GiftResponse,
    GiftValidate,
    GiftValidateResponse
)
from backend.services.gift_service import GiftService
from backend.services.logger_service import LoggerService
from backend.models.enum.tariff import Tariff

router = APIRouter()


@router.post("", response_model=GiftResponse, status_code=status.HTTP_201_CREATED)
async def create_gift(
    gift_data: GiftCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Create a new gift certificate.
    """
    try:
        gift_service = GiftService()

        # Convert tariff string to enum
        try:
            tariff_enum = Tariff[gift_data.tariff]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tariff: {gift_data.tariff}"
            )

        gift = gift_service.add_gift(
            contact=gift_data.contact,
            number=gift_data.number,
            tariff=tariff_enum,
            chat_id=gift_data.chat_id
        )

        if not gift:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create gift certificate"
            )

        return gift

    except HTTPException:
        raise
    except Exception as e:
        LoggerService.error(__name__, "create_gift failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating gift certificate"
        )


@router.get("/{gift_id}", response_model=GiftResponse)
async def get_gift(
    gift_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get gift certificate by ID.
    """
    try:
        gift_service = GiftService()
        gift = gift_service.get_gift_by_id(gift_id)

        if not gift:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gift certificate {gift_id} not found"
            )

        return gift

    except HTTPException:
        raise
    except Exception as e:
        LoggerService.error(__name__, "get_gift failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching gift certificate"
        )


@router.post("/validate", response_model=GiftValidateResponse)
async def validate_gift(
    validate_data: GiftValidate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Validate a gift certificate by number.
    Returns validity status and gift details if valid.
    """
    try:
        gift_service = GiftService()
        gift = gift_service.get_gift_by_number(validate_data.certificate_number)

        if not gift:
            return GiftValidateResponse(
                valid=False,
                gift=None,
                message="Gift certificate not found"
            )

        if gift.is_done:
            return GiftValidateResponse(
                valid=False,
                gift=None,
                message="Gift certificate has already been used"
            )

        return GiftValidateResponse(
            valid=True,
            gift=gift,
            message="Gift certificate is valid"
        )

    except Exception as e:
        LoggerService.error(__name__, "validate_gift failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while validating gift certificate"
        )


@router.patch("/{gift_id}/redeem", response_model=GiftResponse)
async def redeem_gift(
    gift_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Mark a gift certificate as used/redeemed.
    """
    try:
        gift_service = GiftService()

        gift = gift_service.get_gift_by_id(gift_id)
        if not gift:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gift certificate {gift_id} not found"
            )

        if gift.is_done:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gift certificate has already been used"
            )

        # Mark as used
        gift_service.mark_gift_as_used(gift_id)

        # Refresh and return
        updated_gift = gift_service.get_gift_by_id(gift_id)
        return updated_gift

    except HTTPException:
        raise
    except Exception as e:
        LoggerService.error(__name__, "redeem_gift failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while redeeming gift certificate"
        )
