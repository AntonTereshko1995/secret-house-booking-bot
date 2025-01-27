from datetime import date, datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database
from src.models.enum.sale import Sale
from db.models.base import Base
from db.models.user import UserBase
from db.models.gift import GiftBase
from db.models.subscription import SubscriptionBase
from db.models.booking import BookingBase
from matplotlib.dates import relativedelta
from src.models.enum.subscription_type import SubscriptionType
from src.models.enum.tariff import Tariff
from typing import List
from singleton_decorator import singleton
from database import engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Date, cast, select
from src.config.config import MAX_PERIOD_FOR_GIFT_IN_MONTHS, MAX_PERIOD_FOR_SUBSCRIPTION_IN_MONTHS

@singleton
class DatabaseService:
    def __init__(self):
        self.engine = engine
        self.Session = sessionmaker(bind=self.engine)
        database.create_db_and_tables()
        # Base.metadata.drop_all(engine)  # Удаляет все таблицы
        # Base.metadata.create_all(engine)  # Создаёт таблицы заново

    def add_user(self, contact: str) -> UserBase:
        with self.Session() as session:
            try:
                new_user = UserBase(contact=contact)
                session.add(new_user)
                session.commit()
                print(f"User added: {new_user}")
                return new_user
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

                new_user = UserBase(contact=contact)
                session.add(new_user)
                session.commit()
                print(f"User created: {new_user}")
                return new_user
            except Exception as e:
                print(f"Error in get_or_create_user: {e}")
                session.rollback()

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
            has_additional_bedroom: bool,
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
                    has_additional_bedroom = has_additional_bedroom, 
                    price = price, 
                    code = code)
                session.add(new_gift)
                session.commit()
                print(f"Gift added: {new_gift}")
                return new_gift
            except Exception as e:
                print(f"Error adding gift: {e}")
                session.rollback()

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
                return gift
            except Exception as e:
                session.rollback()
                print(f"Error updating Gift: {e}")

    def get_gift_by_code(self, code: str) -> GiftBase:
        with self.Session() as session:
            gift = session.scalar(select(GiftBase)
                .where((GiftBase.code == code) & (GiftBase.is_done == False)))
                # Main logic
                # .where((GiftBase.code == code) & (GiftBase.is_paymented == True) & (GiftBase.is_done == False)))
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
                new_subscription = SubscriptionBase(
                    user_id = user.id,
                    subscription_type = subscription_type, 
                    date_expired = date_expired,
                    price = price, 
                    code = code)
                session.add(new_subscription)
                session.commit()
                print(f"Subscription added: {new_subscription}")
                return new_subscription
            except Exception as e:
                session.rollback()
                print(f"Error adding Subscription: {e}")

    def update_subscription(
            self, 
            subscription_id: int,
            date_expired: datetime = None,
            is_paymented: bool = None,
            is_done: bool = None,
            number_of_visits: int = None) -> SubscriptionBase:
        with self.Session() as session:
            try:
                subscription = session.scalar(select(SubscriptionBase).where(SubscriptionBase.id == subscription_id))
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
                return subscription
            except Exception as e:
                session.rollback()
                print(f"Error updating Subscription: {e}")
    
    def get_subscription_by_code(self, code: str) -> SubscriptionBase:
        with self.Session() as session:
            gift = session.scalar(select(SubscriptionBase)
                .where((SubscriptionBase.code == code) & (SubscriptionBase.is_done == False)))
                # .where((SubscriptionBase.code == code) & (SubscriptionBase.is_paymented == True) & (SubscriptionBase.is_done == False)))
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
            comment: str,
            sale: Sale,
            sale_comment: str,
            gift_id: int = None, 
            subscription_id: int = None) -> BookingBase:
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
                    comment = comment,
                    sale = sale,
                    sale_comment = sale_comment,
                    price = price)
                
                if gift_id:
                    new_booking.gift_id = gift_id
                if subscription_id:
                    new_booking.subscription_id = subscription_id

                session.add(new_booking)
                session.commit()
                print(f"Booking added: {new_booking}")
                return new_booking
            except Exception as e:
                print(f"Error adding booking: {e}")
                session.rollback()

    def get_booking_by_start_date(
            self, 
            user_contact: str, 
            start_date: date) -> BookingBase:
        user = self.get_user_by_contact(user_contact)
        if not user:
            return None
        
        with self.Session() as session:
            booking = session.scalar(select(BookingBase)
                .where((BookingBase.user_id == user) & (cast(BookingBase.start_date, Date) == start_date)))
            return booking
        
    def update_booking(
            self, 
            booking_id: int,
            start_date: datetime = None,
            end_date: datetime = None,
            is_canceled: bool = None,
            is_data_changed: bool = None,
            price: float = None,
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
                if price:
                    booking.price = price

                session.commit()
                print(f"Booking updated: {booking}")
                return booking
            except Exception as e:
                session.rollback()
                print(f"Error updating Booking: {e}")