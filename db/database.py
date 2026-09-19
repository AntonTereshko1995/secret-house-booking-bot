import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.models.base import Base
from db.models.user import UserBase
from db.models.booking import BookingBase
from db.models.gift import GiftBase
from sqlalchemy import create_engine
from src.config.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,    # test connection before use, discard stale ones
    pool_recycle=1800,     # recycle connections older than 30 min
)


def create_db_and_tables() -> None:
    pass  # Migrations are managed by secret-house-api
