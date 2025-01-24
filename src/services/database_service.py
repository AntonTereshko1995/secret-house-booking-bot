from datetime import datetime
import sys
import os

from matplotlib.dates import relativedelta

from models.booking import BookingBase
from models.gift import GiftBase
from models.subscription import SubscriptioBase
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database
from models.user import UserBase
from src.helpers import sale_halper
from src.models.enum.sale import Sale
from src.models.enum.subscription_type import SubscriptionType
from src.models.enum.tariff import Tariff
from src.models.rental_price import RentalPrice
from src.services.file_service import FileService
from typing import List
from singleton_decorator import singleton
from database import engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from src.config.config import MAX_PERIOD_FOR_GIFT_IN_MONTHS, MAX_PERIOD_FOR_SUBSCRIPTION_IN_MONTHS

@singleton
class DatabaseService:
    def __init__(self):
        self.engine = engine
        self.Session = sessionmaker(bind=self.engine)
        database.create_db_and_tables()

    def add_user(self, contact: str) -> UserBase:
        with self.Session() as session:
            try:
                new_user = UserBase(contact=contact)
                session.add(new_user)
                session.commit()
                print(f"User added: {new_user}")
            except Exception as e:
                session.rollback()
                print(f"Error adding user: {e}")

    def get_or_create_user(self, contact: str) -> UserBase:
        with self.Session() as session:
            try:
                user = session.scalar(select(UserBase).where(UserBase.contact == contact))
                if user:
                    print(f"User already exists: {user}")
                    return user

                new_user = UserBase(email=contact)
                session.add(new_user)
                session.commit()
                print(f"User created: {new_user}")
                return new_user
            except Exception as e:
                session.rollback()
                print(f"Error in get_or_create_user: {e}")

    def get_user_by_contact(self, contact: str) -> UserBase:
        with self.Session() as session:
            user = session.scalar(select(UserBase).where(UserBase.contact == contact))
            return user
        
    def add_gift(
            self, 
            buyer_contact: str, 
            tariff: Tariff, 
            has_sauna: bool, 
            has_secret_room: bool, 
            price: float, 
            code: str) -> GiftBase:
        with self.Session() as session:
            try:
                date_expired = datetime.today() + relativedelta(months=MAX_PERIOD_FOR_GIFT_IN_MONTHS)
                new_gift = GiftBase(
                    buyer_contact = buyer_contact,
                    tariff = tariff, 
                    date_expired = date_expired,
                    has_sauna = has_sauna,
                    has_secret_room = has_secret_room, 
                    price = price, 
                    code = code)
                session.add(new_gift)
                session.commit()
                print(f"Gift added: {new_gift}")
            except Exception as e:
                session.rollback()
                print(f"Error adding gift: {e}")

    def update_gift(
            self, 
            gift_id: int,
            user_id: int = None,
            date_expired: datetime = None,
            is_paymented: bool = None,
            is_done: bool = None) -> GiftBase:
        with self.Session() as session:
            try:
                gift = session.scalar(select(GiftBase).where(GiftBase.id == gift_id))
                if not gift:
                    print(f"Gift with id {gift_id} not found.")
                    return

                if user_id:
                    gift.user_id = user_id
                if date_expired:
                    gift.date_expired = date_expired
                if is_paymented:
                    gift.is_paymented = is_paymented
                if is_done:
                    gift.is_done = is_done

                session.commit()
                print(f"Gift updated: {gift}")
            except Exception as e:
                session.rollback()
                print(f"Error updating Gift: {e}")

    def get_gift_by_code(self, code: str) -> GiftBase:
        with self.Session() as session:
            gift = session.scalar(select(GiftBase).where(GiftBase.code == code))
            return gift

    def add_subscription(
            self, 
            user_contact: str, 
            subscription_type: SubscriptionType, 
            price: float, 
            code: str):
        user = self.get_or_create_user(user_contact)
        with self.Session() as session:
            try:
                date_expired = datetime.today() + relativedelta(months=MAX_PERIOD_FOR_SUBSCRIPTION_IN_MONTHS)
                new_subscription = SubscriptioBase(
                    user_id = user.id,
                    subscription_type = subscription_type, 
                    date_expired = date_expired,
                    price = price, 
                    code = code)
                session.add(new_subscription)
                session.commit()
                print(f"Subscription added: {new_subscription}")
            except Exception as e:
                session.rollback()
                print(f"Error adding Subscription: {e}")

    def update_subscription(
            self, 
            subscription_id: int,
            date_expired: datetime = None,
            is_paymented: bool = None,
            is_done: bool = None,
            number_of_visits: int = None) -> SubscriptioBase:
        with self.Session() as session:
            try:
                subscription = session.scalar(select(SubscriptioBase).where(SubscriptioBase.id == subscription_id))
                if not subscription:
                    print(f"Subscription with id {subscription_id} not found.")
                    return

                if date_expired:
                    subscription.date_expired = date_expired
                if is_paymented:
                    subscription.is_paymented = is_paymented
                if is_done:
                    subscription.is_done = is_done
                if number_of_visits:
                    subscription.number_of_visits = number_of_visits

                session.commit()
                print(f"Subscription updated: {subscription}")
            except Exception as e:
                session.rollback()
                print(f"Error updating Subscription: {e}")
    
    def get_subscription_by_code(self, code: str) -> SubscriptioBase:
        with self.Session() as session:
            gift = session.scalar(select(SubscriptioBase).where(SubscriptioBase.code == code))
            return gift
        
    def add_booking(
            self, 
            user_contact: str, 
            start_date: datetime, 
            end_date: datetime, 
            tariff: Tariff, 
            has_photoshoot: bool, 
            has_sauna: bool, 
            has_white_bedroom: bool, 
            has_green_bedroom: bool, 
            has_secret_room: bool, 
            number_of_guests: int, 
            price: float, 
            gift_id: int = None, 
            subscription_id: int = None):
        user = self.get_or_create_user(user_contact)
        with self.Session() as session:
            try:
                new_booking = BookingBase(
                    user_id = user.id,
                    start_date = start_date, 
                    end_date = end_date,
                    tariff = tariff,
                    has_photoshoot = has_photoshoot,
                    has_sauna = has_sauna,
                    has_white_bedroom = has_white_bedroom,
                    has_green_bedroom = has_green_bedroom,
                    has_secret_room = has_secret_room,
                    number_of_guests = number_of_guests,
                    gift_id = gift_id,
                    subscription_id = subscription_id,
                    price = price)
                session.add(new_booking)
                session.commit()
                print(f"Booking added: {new_booking}")
            except Exception as e:
                session.rollback()
                print(f"Error adding booking: {e}")

    def get_booking_by_start_date(
            self, 
            user_contact: str, 
            start_date: datetime):
        user = self.get_user_by_contact(user_contact)
        if not user:
            return None
        
        with self.Session() as session:
            booking = session.scalar(select(BookingBase).where(BookingBase.user_id == user and BookingBase.start_date == start_date))
            return booking
        
    def update_booking(
            self, 
            booking_id: int,
            start_date: datetime = None,
            end_date: datetime = None,
            is_canceled: bool = None,
            is_data_changed: bool = None,
            is_prepaymented: bool = None) -> BookingBase:
        with self.Session() as session:
            try:
                booking = session.scalar(select(BookingBase).where(BookingBase.id == booking_id))
                if not booking:
                    print(f"Booking with id {booking_id} not found.")
                    return

                if start_date:
                    booking.start_date = start_date
                if end_date:
                    booking.end_date = end_date
                if is_canceled:
                    booking.is_canceled = is_canceled
                if is_data_changed:
                    booking.is_data_changed = is_data_changed
                if is_prepaymented:
                    booking.is_prepaymented = is_prepaymented

                session.commit()
                print(f"Booking updated: {booking}")
            except Exception as e:
                session.rollback()
                print(f"Error updating Booking: {e}")