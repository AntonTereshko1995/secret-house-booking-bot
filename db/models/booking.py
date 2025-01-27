import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.models.enum.tariff import Tariff
from datetime import datetime
from db.models.base import Base
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

class BookingBase(Base):
    __tablename__ = 'booking'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, unique=True, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, unique=True, nullable=False)
    tariff: Mapped[Tariff] = mapped_column(Integer, nullable=False)
    has_photoshoot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_sauna: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_white_bedroom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_green_bedroom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_secret_room: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_canceled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_data_changed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    number_of_guests: Mapped[int] = mapped_column(Integer, nullable=False)
    is_prepaymented: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=False)
    gift_id: Mapped[int] = mapped_column(ForeignKey("gift.id"), nullable=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscription.id"), nullable=True)
    user = relationship("UserBase")
    gift = relationship("GiftBase")
    subscription = relationship("SubscriptionBase")

    def __repr__(self) -> str:
        return f"BookingBase(id={self.id}, user={self.user_id}, tariff={self.tariff}, start_date={self.start_date}, end_date={self.end_date})"
