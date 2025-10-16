from datetime import date, datetime, timedelta
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db import database
from src.services.logger_service import LoggerService
from db.models.user import UserBase
from db.models.gift import GiftBase
from db.models.booking import BookingBase
from matplotlib.dates import relativedelta
from src.models.enum.tariff import Tariff
from singleton_decorator import singleton
from database import engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Sequence, and_, func, or_, select
from src.config.config import MAX_PERIOD_FOR_GIFT_IN_MONTHS


@singleton
class DatabaseService:
    def __init__(self):
        self.engine = engine
        self.Session = sessionmaker(bind=self.engine)
        database.create_db_and_tables()
        # Clear database
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
                LoggerService.error(__name__, "add_user", e)

    def get_or_create_user(self, contact: str) -> UserBase:
        with self.Session() as session:
            try:
                user = session.scalar(
                    select(UserBase).where(UserBase.contact == contact)
                )
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
                LoggerService.error(__name__, "get_or_create_user", e)
                session.rollback()

    def get_user_by_contact(self, contact: str) -> UserBase:
        try:
            with self.Session() as session:
                user = session.scalar(
                    select(UserBase).where(UserBase.contact == contact)
                )
                return user
        except Exception as e:
            print(f"Error in get_user_by_contact: {e}")
            LoggerService.error(__name__, "get_user_by_contact", e)

    def get_user_by_id(self, user_id: int) -> UserBase:
        try:
            with self.Session() as session:
                user = session.scalar(select(UserBase).where(UserBase.id == user_id))
                return user
        except Exception as e:
            print(f"Error in get_user_by_id: {e}")
            LoggerService.error(__name__, "get_user_by_id", e)

    def add_gift(
        self,
        buyer_contact: str,
        tariff: Tariff,
        has_sauna: bool,
        has_secret_room: bool,
        has_additional_bedroom: bool,
        price: float,
        code: str,
    ) -> GiftBase:
        with self.Session() as session:
            try:
                date_expired = datetime.today() + relativedelta(
                    months=MAX_PERIOD_FOR_GIFT_IN_MONTHS
                )
                new_gift = GiftBase(
                    buyer_contact=buyer_contact,
                    tariff=tariff,
                    date_expired=date_expired,
                    has_sauna=has_sauna,
                    has_secret_room=has_secret_room,
                    has_additional_bedroom=has_additional_bedroom,
                    price=price,
                    code=code,
                )
                session.add(new_gift)
                session.commit()
                print(f"Gift added: {new_gift}")
                return new_gift
            except Exception as e:
                print(f"Error adding gift: {e}")
                session.rollback()
                LoggerService.error(__name__, "add_gift", e)

    def update_gift(
        self,
        gift_id: int,
        user_id: int = None,
        date_expired: datetime = None,
        is_paymented: bool = None,
        is_done: bool = None,
    ) -> GiftBase:
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
                LoggerService.error(__name__, "update_gift", e)

    def get_gift_by_code(self, code: str) -> GiftBase:
        try:
            with self.Session() as session:
                gift = session.scalar(
                    select(GiftBase).where(
                        (GiftBase.code == code)
                        & (GiftBase.is_paymented == True)
                        & (GiftBase.is_done == False)
                    )
                )
                return gift
        except Exception as e:
            print(f"Error in get_gift_by_code: {e}")
            LoggerService.error(__name__, "get_gift_by_code", e)

    def get_gift_by_id(self, id: int) -> GiftBase:
        try:
            with self.Session() as session:
                gift = session.scalar(select(GiftBase).where(GiftBase.id == id))
                return gift
        except Exception as e:
            print(f"Error in get_gift_by_id: {e}")
            LoggerService.error(__name__, "get_gift_by_id", e)

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
        chat_id: int,
        gift_id: int = None,
        wine_preference: str = None,
        transfer_address: str = None,
    ) -> BookingBase:
        user = self.get_or_create_user(user_contact)
        with self.Session() as session:
            try:
                new_booking = BookingBase(
                    user_id=user.id,
                    start_date=start_date,
                    end_date=end_date,
                    tariff=tariff,
                    has_photoshoot=has_photoshoot,
                    has_sauna=has_sauna,
                    has_white_bedroom=has_white_bedroom,
                    has_green_bedroom=has_green_bedroom,
                    has_secret_room=has_secret_room,
                    number_of_guests=number_of_guests,
                    comment=comment,
                    chat_id=chat_id,
                    price=price,
                    wine_preference=wine_preference,
                    transfer_address=transfer_address,
                )

                if gift_id:
                    new_booking.gift_id = gift_id

                session.add(new_booking)
                session.commit()
                print(f"Booking added: {new_booking}")
                return new_booking
            except Exception as e:
                print(f"Error adding booking: {e}")
                session.rollback()
                LoggerService.error(__name__, "add_booking", e)

    def get_booking_by_start_date_user(
        self, user_contact: str, start_date: date
    ) -> BookingBase:
        user = self.get_user_by_contact(user_contact)
        if not user:
            return None
        try:
            with self.Session() as session:
                booking = session.scalar(
                    select(BookingBase).where(
                        and_(
                            BookingBase.user_id == user.id,
                            func.date(BookingBase.start_date) == start_date,
                            BookingBase.is_canceled == False,
                            BookingBase.is_done == False,
                            BookingBase.is_prepaymented == True,
                        )
                    )
                )
                return booking
        except Exception as e:
            print(f"Error in get_booking_by_start_date_user: {e}")
            LoggerService.error(__name__, "get_booking_by_start_date_user", e)

    def get_booking_by_start_date(self, start_date: date):
        try:
            with self.Session() as session:
                bookings = session.scalars(
                    select(BookingBase).where(
                        and_(
                            func.date(BookingBase.start_date) == start_date,
                            BookingBase.is_canceled == False,
                            BookingBase.is_done == False,
                            BookingBase.is_prepaymented == True,
                        )
                    )
                ).all()
                return bookings
        except Exception as e:
            print(f"Error in get_booking_by_start_date: {e}")
            LoggerService.error(__name__, "get_booking_by_start_date", e)

    def get_booking_by_finish_date(self, end_date: date):
        try:
            with self.Session() as session:
                bookings = session.scalars(
                    select(BookingBase).where(
                        and_(
                            func.date(BookingBase.end_date) == end_date,
                            BookingBase.is_canceled == False,
                            BookingBase.is_done == False,
                            BookingBase.is_prepaymented == True,
                        )
                    )
                ).all()
                return bookings
        except Exception as e:
            print(f"Error in get_booking_by_finish_date: {e}")
            LoggerService.error(__name__, "get_booking_by_finish_date", e)

    def get_booking_by_period(
        self, from_date: date, to_date: date, is_admin: bool = False
    ) -> Sequence[BookingBase]:
        try:
            with self.Session() as session:
                if not is_admin:
                    bookings = session.scalars(
                        select(BookingBase)
                        .where(
                            and_(
                                BookingBase.start_date >= from_date,
                                BookingBase.start_date <= to_date,
                                BookingBase.is_canceled == False,
                                BookingBase.is_done == False,
                                BookingBase.is_prepaymented == True,
                            )
                        )
                        .order_by(BookingBase.start_date)
                    ).all()
                else:
                    bookings = session.scalars(
                        select(BookingBase)
                        .where(
                            and_(
                                BookingBase.start_date >= from_date,
                                BookingBase.start_date <= to_date,
                            )
                        )
                        .order_by(BookingBase.start_date)
                    ).all()

                return bookings
        except Exception as e:
            print(f"Error in get_booking_by_period: {e}")
            LoggerService.error(__name__, "get_booking_by_period", e)

    def get_booking_by_day(
        self, target_date: date, except_booking_id: int = None
    ) -> Sequence[BookingBase]:
        try:
            with self.Session() as session:
                start_of_day = datetime.combine(target_date, datetime.min.time())
                end_of_day = datetime.combine(target_date, datetime.max.time())
                bookings = session.scalars(
                    select(BookingBase).where(
                        and_(
                            BookingBase.is_canceled == False,
                            BookingBase.is_done == False,
                            BookingBase.is_prepaymented == True,
                            BookingBase.id != except_booking_id,
                            or_(
                                and_(
                                    BookingBase.start_date >= start_of_day,
                                    BookingBase.start_date <= end_of_day,
                                ),
                                and_(
                                    BookingBase.end_date >= start_of_day,
                                    BookingBase.end_date <= end_of_day,
                                ),
                                and_(
                                    BookingBase.start_date <= start_of_day,
                                    BookingBase.end_date >= end_of_day,
                                ),
                            ),
                        )
                    )
                ).all()
                return bookings
        except Exception as e:
            print(f"Error in get_booking_by_day: {e}")
            LoggerService.error(__name__, "get_booking_by_day", e)

    def get_bookings_by_month(
        self, target_month: int, target_year: int
    ) -> Sequence[BookingBase]:
        """
        Returns a list of bookings for a specific month
        """
        try:
            if target_year is None:
                target_year = datetime.now().year

            with self.Session() as session:
                # Get start and end of the month
                start_of_month = datetime(target_year, target_month, 1)
                if target_month == 12:
                    end_of_month = datetime(target_year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_of_month = datetime(
                        target_year, target_month + 1, 1
                    ) - timedelta(days=1)

                # Get all bookings that overlap with the month
                query = select(BookingBase).where(
                    and_(
                        BookingBase.is_canceled == False,
                        BookingBase.is_done == False,
                        BookingBase.is_prepaymented == True,
                        or_(
                            and_(
                                BookingBase.start_date >= start_of_month,
                                BookingBase.start_date <= end_of_month,
                            ),
                            and_(
                                BookingBase.end_date >= start_of_month,
                                BookingBase.end_date <= end_of_month,
                            ),
                            and_(
                                BookingBase.start_date <= start_of_month,
                                BookingBase.end_date >= end_of_month,
                            ),
                        ),
                    )
                )

                # Order by start date
                query = query.order_by(BookingBase.start_date)
                bookings = session.scalars(query).all()
                return bookings

        except Exception as e:
            print(f"Error in get_available_dayes_by_month: {e}")
            LoggerService.error(__name__, "get_available_dayes_by_month", e)
            return []

    def is_booking_between_dates(self, start: datetime, end: datetime) -> bool:
        try:
            with self.Session() as session:
                overlapping_bookings = session.scalars(
                    select(BookingBase).where(
                        and_(
                            BookingBase.is_canceled == False,
                            BookingBase.is_done == False,
                            BookingBase.is_prepaymented == True,
                            or_(
                                and_(
                                    BookingBase.start_date < end,
                                    BookingBase.start_date > start,
                                ),
                                and_(
                                    BookingBase.end_date > start,
                                    BookingBase.end_date < end,
                                ),
                                and_(
                                    BookingBase.start_date < start,
                                    BookingBase.end_date > end,
                                ),
                            ),
                        )
                    )
                ).first()
                return overlapping_bookings is not None
        except Exception as e:
            print(f"Error in is_booking_between_dates: {e}")
            LoggerService.error(__name__, "is_booking_between_dates", e)

    def get_booking_by_id(self, booking_id: int) -> BookingBase:
        try:
            with self.Session() as session:
                booking = session.scalar(
                    select(BookingBase).where(BookingBase.id == booking_id)
                )
                return booking
        except Exception as e:
            print(f"Error in get_booking_by_id: {e}")
            LoggerService.error(__name__, "get_booking_by_id", e)

    def get_booking_by_user_contact(self, user_contact: str) -> list[BookingBase]:
        user = self.get_user_by_contact(user_contact)
        if not user:
            return []

        try:
            with self.Session() as session:
                bookings = session.scalars(
                    select(BookingBase).where(
                        and_(
                            BookingBase.user_id == user.id,
                            BookingBase.is_canceled == False,
                            BookingBase.is_done == False,
                            BookingBase.is_prepaymented == True,
                        )
                    )
                ).all()
                return bookings
        except Exception as e:
            print(f"Error in get_booking_by_user_contact: {e}")
            LoggerService.error(__name__, "get_booking_by_user_contact", e)

    def get_unpaid_bookings(self) -> Sequence[BookingBase]:
        """Get all unpaid, active bookings"""
        try:
            with self.Session() as session:
                bookings = session.scalars(
                    select(BookingBase).where(
                        and_(
                            BookingBase.is_prepaymented == False,
                            BookingBase.is_canceled == False,
                            BookingBase.is_done == False,
                        )
                    ).order_by(BookingBase.start_date)
                ).all()
                return bookings
        except Exception as e:
            print(f"Error in get_unpaid_bookings: {e}")
            LoggerService.error(__name__, "get_unpaid_bookings", e)
            return []

    def get_done_booking_count(self, user_id: int) -> BookingBase:
        try:
            with self.Session() as session:
                bookings = session.scalars(
                    select(func.count())
                    .select_from(BookingBase)
                    .where(
                        and_(
                            BookingBase.user_id == user_id,
                            BookingBase.is_canceled == False,
                            BookingBase.is_done == True,
                        )
                    )
                ).all()
                return bookings.__len__()
        except Exception as e:
            print(f"Error in get_booking_by_user_contact: {e}")
            LoggerService.error(__name__, "get_booking_by_user_contact", e)

    def update_booking(
        self,
        booking_id: int,
        start_date: datetime = None,
        end_date: datetime = None,
        is_canceled: bool = None,
        is_date_changed: bool = None,
        price: float = None,
        is_prepaymented: bool = None,
        calendar_event_id: str = None,
        is_done: bool = None,
        prepayment: float = None,
    ) -> BookingBase:
        with self.Session() as session:
            try:
                booking = session.scalar(
                    select(BookingBase).where(BookingBase.id == booking_id)
                )
                if not booking:
                    print(f"Booking with id {booking_id} not found.")
                    return

                if start_date:
                    booking.start_date = start_date
                if end_date:
                    booking.end_date = end_date
                if is_canceled:
                    booking.is_canceled = is_canceled
                if is_date_changed:
                    booking.is_date_changed = is_date_changed
                if is_prepaymented:
                    booking.is_prepaymented = is_prepaymented
                if price is not None and price >= 0:
                    booking.price = price
                if calendar_event_id:
                    booking.calendar_event_id = calendar_event_id
                if is_done:
                    booking.is_done = is_done
                if prepayment is not None and prepayment >= 0:
                    booking.prepayment_price = prepayment

                session.commit()
                print(f"Booking updated: {booking}")
                return booking
            except Exception as e:
                session.rollback()
                print(f"Error updating Booking: {e}")
