import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.models.base import Base
from sqlalchemy import String, BigInteger, Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

class UserBase(Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contact: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=True)
    has_bookings: Mapped[bool] = mapped_column(Integer, default=0, nullable=False)
    total_bookings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"UserBase(id={self.id}, contact={self.contact}, bookings={self.total_bookings})"