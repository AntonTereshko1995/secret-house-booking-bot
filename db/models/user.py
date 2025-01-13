from unittest.mock import Base
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=False)
    contact = Column(String, unique=True, nullable=False)