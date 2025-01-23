import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from datetime import datetime
from unittest.mock import Base
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String
from sqlalchemy.orm import relationship
from src.models.enum.subscription_type import SubscriptionType

class SubscriptioBase(Base):
    __tablename__ = 'subscription'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    user = relationship("User")
    date_expired: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    subscription_type: Mapped[SubscriptionType] = mapped_column(Integer, nullable=False)
    is_paymented: Mapped[bool] = mapped_column(Boolean, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    code: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    is_done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    number_of_visits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"SubscriptionBase(id={self.id}, code={self.code}, user={self.user_id})"
