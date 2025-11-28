"""
User API endpoints.
"""
import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# Add parent paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from backend.api.v1.dependencies import get_db, verify_api_key, verify_admin
from backend.api.v1.schemas.user import UserCreate, UserResponse
from backend.services.user_service import UserService
from backend.services.logger_service import LoggerService

router = APIRouter()


@router.post("", response_model=UserResponse)
async def create_or_update_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Create or update a user.
    If user with contact exists, updates it. Otherwise creates new user.
    """
    try:
        user_service = UserService()

        if user_data.contact:
            user = user_service.get_or_create_user(user_data.contact)

            # Update user fields if provided
            if user_data.user_name:
                user_service.update_user_name(user_data.contact, user_data.user_name)
            if user_data.chat_id:
                user_service.update_chat_id(user_data.contact, user_data.chat_id)

            # Refresh user object
            user = user_service.get_user_by_contact(user_data.contact)
        elif user_data.chat_id:
            # Try to find by chat_id
            user = user_service.get_user_by_chat_id(user_data.chat_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot create user without contact information"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either contact or chat_id must be provided"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        LoggerService.error(__name__, "create_or_update_user failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating/updating user"
        )


@router.get("/{user_contact}", response_model=UserResponse)
async def get_user(
    user_contact: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get user by contact.
    """
    try:
        user_service = UserService()
        user = user_service.get_user_by_contact(user_contact)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with contact {user_contact} not found"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        LoggerService.error(__name__, "get_user failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching user"
        )


@router.get("/chat/{chat_id}", response_model=UserResponse)
async def get_user_by_chat_id(
    chat_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get user by Telegram chat ID.
    """
    try:
        user_service = UserService()
        user = user_service.get_user_by_chat_id(chat_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with chat_id {chat_id} not found"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        LoggerService.error(__name__, "get_user_by_chat_id failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching user"
        )


@router.get("", response_model=List[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_admin)
):
    """
    List all users (admin only).
    """
    try:
        user_service = UserService()
        users = user_service.get_all_users()

        return users or []

    except Exception as e:
        LoggerService.error(__name__, "list_users failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching users"
        )
