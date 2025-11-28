import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.db import run_migrations
from backend.db.models.base import Base
from backend.db.models.user import UserBase
from backend.db.models.booking import BookingBase
from backend.db.models.gift import GiftBase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True)

# Create session factory for FastAPI dependency injection
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_db_and_tables() -> None:
    # Base.metadata.create_all(engine)  # Disabled: using Alembic migrations instead
    run_migrations.run_migrations_if_needed()
