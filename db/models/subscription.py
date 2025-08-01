import sys
import os
from dataclasses_json import dataclass_json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.models.decorator.type_decorator import IntEnumType
from datetime import datetime
from db.models.base import Base
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String
from sqlalchemy.orm import relationship
from src.models.enum.subscription_type import SubscriptionType

@dataclass_json
class SubscriptionBase(Base):
    __tablename__ = 'subscription'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    date_expired: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    subscription_type: Mapped[SubscriptionType] = mapped_column(IntEnumType(SubscriptionType), nullable=False)
    is_paymented: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    code: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    is_done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    number_of_visits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user = relationship("UserBase")

    def __repr__(self) -> str:
        return f"SubscriptionBase(id={self.id}, code={self.code}, user={self.user_id})"
