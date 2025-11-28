import sys
import os
from datetime import date, datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.models.base import Base
from sqlalchemy import Boolean, Date, DateTime, Float, String, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column


class PromocodeBase(Base):
    __tablename__ = "promocode"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    promocode_type: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )  # 1 = BOOKING_DATES, 2 = USAGE_PERIOD
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)
    discount_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    applicable_tariffs: Mapped[str] = mapped_column(
        JSON, nullable=True
    )  # null = ALL, or [1,2,3] = specific tariff values
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __repr__(self) -> str:
        return f"PromocodeBase(id={self.id}, name={self.name}, discount={self.discount_percentage}%)"
