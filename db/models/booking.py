from unittest.mock import Base
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

class Booking(Base):
    __tablename__ = 'booking'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    start_date = Column(DateTime, unique=True, nullable=False)
    end_date = Column(String, unique=True, nullable=False)
    tariff = Column(Integer, unique=False, nullable=False) 
    has_photoshoot = Column(Boolean, unique=False, nullable=False)
    has_sauna = Column(Boolean, unique=False, nullable=False)
    has_white_bedroom = Column(Boolean, unique=False, nullable=False)
    has_green_bedroom = Column(Boolean, unique=False, nullable=False)
    has_secret_room = Column(Boolean, unique=False, nullable=False, default=True)
    has_contract = Column(Boolean, unique=False, nullable=False)
    is_canceled = Column(Boolean, unique=False, nullable=False)
    number_of_guests = Column(Integer, unique=False, nullable=False, default=2)
    prepayment = Column(Float, nullable=False, nullable=False)
    price = Column(Float, nullable=False, nullable=False)

    user = relationship("User")