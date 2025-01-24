import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.models.base import Base
from db.models.user import UserBase
from db.models.booking import BookingBase
from db.models.gift import GiftBase
from db.models.subscription import SubscriptionBase
from sqlalchemy import create_engine
from src.config.config import DATABASE_URL
import os

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables() -> None:
	Base.metadata.create_all(engine)