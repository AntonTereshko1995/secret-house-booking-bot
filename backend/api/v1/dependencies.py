"""
FastAPI dependencies for database sessions and authentication.
"""
from typing import Generator
from fastapi import Header, HTTPException, status
from sqlalchemy.orm import Session
import sys
import os

# Add parent paths for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.db.database import SessionLocal
from backend.config import config


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    Automatically closes the session after the request is complete.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")) -> str:
    """
    Dependency to verify API key for protected endpoints.
    Raises 401 if API key is missing or invalid.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key is missing"
        )

    if x_api_key != config.BACKEND_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )

    return x_api_key


async def verify_admin(x_api_key: str = Header(None, alias="X-API-Key")) -> str:
    """
    Dependency to verify admin access.
    Currently uses same API key, but can be extended for role-based access.
    """
    return await verify_api_key(x_api_key)
