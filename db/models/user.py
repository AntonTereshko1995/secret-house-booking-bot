import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.models.base import Base
from sqlalchemy import String, BigInteger, Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class UserBase(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contact: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    user_name: Mapped[str] = mapped_column(String, unique=False, nullable=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=True)
    has_bookings: Mapped[bool] = mapped_column(Integer, default=0, nullable=False)
    total_bookings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_bookings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"UserBase(id={self.id}, user_name={self.user_name}, contact={self.contact}, total={self.total_bookings}, completed={self.completed_bookings})"
