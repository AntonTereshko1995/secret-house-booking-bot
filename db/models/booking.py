import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.models.decorator.type_decorator import IntEnumType
from src.models.enum.tariff import Tariff
from datetime import datetime
from db.models.base import Base
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from src.config.config import PREPAYMENT


class BookingBase(Base):
    __tablename__ = "booking"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, unique=False, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, unique=False, nullable=False)
    tariff: Mapped[Tariff] = mapped_column(IntEnumType(Tariff), nullable=False)
    has_photoshoot: Mapped[bool] = mapped_column(Boolean, default=False)
    has_sauna: Mapped[bool] = mapped_column(Boolean, default=False)
    has_white_bedroom: Mapped[bool] = mapped_column(Boolean, default=False)
    has_green_bedroom: Mapped[bool] = mapped_column(Boolean, default=False)
    has_secret_room: Mapped[bool] = mapped_column(Boolean, default=False)
    is_canceled: Mapped[bool] = mapped_column(Boolean, default=False)
    is_date_changed: Mapped[bool] = mapped_column(Boolean, default=False)
    number_of_guests: Mapped[int] = mapped_column(Integer, nullable=False)
    is_prepaymented: Mapped[bool] = mapped_column(Boolean, default=False)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    feedback_submitted: Mapped[bool] = mapped_column(Boolean, default=False)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    prepayment_price: Mapped[float] = mapped_column(
        Float, nullable=False, default=PREPAYMENT
    )
    comment: Mapped[str] = mapped_column(String, nullable=True)
    calendar_event_id: Mapped[str] = mapped_column(String, nullable=True)
    gift_id: Mapped[int] = mapped_column(ForeignKey("gift.id"), nullable=True)
    promocode_id: Mapped[int] = mapped_column(ForeignKey("promocode.id"), nullable=True)
    wine_preference: Mapped[str] = mapped_column(String, nullable=True)
    transfer_address: Mapped[str] = mapped_column(String, nullable=True)
    user = relationship("UserBase")
    gift = relationship("GiftBase")
    promocode = relationship("PromocodeBase")

    def __repr__(self) -> str:
        return f"BookingBase(id={self.id}, user={self.user_id}, tariff={self.tariff}, start_date={self.start_date}, end_date={self.end_date})"
