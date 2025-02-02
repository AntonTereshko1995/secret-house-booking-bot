import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.models.base import Base
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String

class UserBase(Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contact: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    telegram_id: Mapped[str] = mapped_column(String, unique=True, nullable=True)

    def __repr__(self) -> str:
        return f"UserBase(id={self.id}, contact={self.contact})"