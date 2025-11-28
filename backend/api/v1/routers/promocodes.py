"""
Promocode API endpoints.
"""
import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

# Add parent paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from backend.api.v1.dependencies import get_db, verify_api_key, verify_admin
from backend.api.v1.schemas.promocode import (
    PromocodeCreate,
    PromocodeResponse,
    PromocodeValidate,
    PromocodeValidateResponse
)
from backend.services.database.promocode_repository import PromocodeRepository
from backend.services.logger_service import LoggerService
from backend.models.enum.promocode_type import PromocodeType

router = APIRouter()


@router.post("", response_model=PromocodeResponse, status_code=status.HTTP_201_CREATED)
async def create_promocode(
    promocode_data: PromocodeCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_admin)
):
    """
    Create a new promocode (admin only).
    """
    try:
        promocode_repo = PromocodeRepository()

        # Convert promocode_type string to enum
        try:
            type_enum = PromocodeType[promocode_data.promocode_type]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid promocode type: {promocode_data.promocode_type}"
            )

        # Check if promocode already exists
        existing = promocode_repo.get_promocode_by_code(promocode_data.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Promocode '{promocode_data.code}' already exists"
            )

        # Create promocode
        promocode = promocode_repo.create_promocode(
            code=promocode_data.code,
            discount_percentage=promocode_data.discount_percentage,
            promocode_type=type_enum
        )

        if not promocode:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create promocode"
            )

        return promocode

    except HTTPException:
        raise
    except Exception as e:
        LoggerService.error(__name__, "create_promocode failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating promocode"
        )


@router.get("", response_model=List[PromocodeResponse])
async def list_promocodes(
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_admin)
):
    """
    List all promocodes (admin only).
    Can filter by is_active status.
    """
    try:
        promocode_repo = PromocodeRepository()

        if is_active is not None:
            promocodes = promocode_repo.get_promocodes_by_active_status(is_active)
        else:
            promocodes = promocode_repo.get_all_promocodes()

        return promocodes or []

    except Exception as e:
        LoggerService.error(__name__, "list_promocodes failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching promocodes"
        )


@router.post("/validate", response_model=PromocodeValidateResponse)
async def validate_promocode(
    validate_data: PromocodeValidate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Validate a promocode.
    Returns validity status and discount information.
    """
    try:
        promocode_repo = PromocodeRepository()
        promocode = promocode_repo.get_promocode_by_code(validate_data.code)

        if not promocode:
            return PromocodeValidateResponse(
                valid=False,
                discount_percentage=None,
                promocode=None,
                message="Promocode not found"
            )

        if not promocode.is_active:
            return PromocodeValidateResponse(
                valid=False,
                discount_percentage=None,
                promocode=None,
                message="Promocode is no longer active"
            )

        return PromocodeValidateResponse(
            valid=True,
            discount_percentage=promocode.discount_percentage,
            promocode=promocode,
            message="Promocode is valid"
        )

    except Exception as e:
        LoggerService.error(__name__, "validate_promocode failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while validating promocode"
        )


@router.delete("/{promocode_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_promocode(
    promocode_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_admin)
):
    """
    Delete a promocode (admin only).
    Performs soft delete by setting is_active to False.
    """
    try:
        promocode_repo = PromocodeRepository()

        promocode = promocode_repo.get_promocode_by_id(promocode_id)
        if not promocode:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Promocode {promocode_id} not found"
            )

        # Soft delete by deactivating
        promocode_repo.deactivate_promocode(promocode_id)

        return None

    except HTTPException:
        raise
    except Exception as e:
        LoggerService.error(__name__, "delete_promocode failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting promocode"
        )
