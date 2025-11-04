import sys
import os
from datetime import date, datetime, timedelta
from typing import Sequence

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.base_database_service import BaseDatabaseService
from src.services.logger_service import LoggerService
from src.services.user_service import UserService
from db.models.booking import BookingBase
from src.models.enum.tariff import Tariff
from singleton_decorator import singleton
from sqlalchemy import and_, distinct, func, or_, select


@singleton
class BookingService(BaseDatabaseService):
    """Service for booking-related database operations."""

    def __init__(self):
        super().__init__()
        self.user_service = UserService()

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
        """Add a new booking to the database."""
        user = self.user_service.get_or_create_user(user_contact)
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
        """Get booking for specific user by start date."""
        user = self.user_service.get_user_by_contact(user_contact)
        if not user:
            return None
        try:
            with self.Session() as session:
                booking = session.scalar(
                    select(BookingBase).where(
                        and_(
                            BookingBase.user_id == user.id,
                            func.date(BookingBase.start_date) == start_date,
                            ~BookingBase.is_canceled,
                            ~BookingBase.is_done,
                            BookingBase.is_prepaymented,
                        )
                    )
                )
                return booking
        except Exception as e:
            print(f"Error in get_booking_by_start_date_user: {e}")
            LoggerService.error(__name__, "get_booking_by_start_date_user", e)

    def get_booking_by_start_date(self, start_date: date):
        """Get all bookings starting on a specific date."""
        try:
            with self.Session() as session:
                bookings = session.scalars(
                    select(BookingBase).where(
                        and_(
                            func.date(BookingBase.start_date) == start_date,
                            ~BookingBase.is_canceled,
                            ~BookingBase.is_done,
                            BookingBase.is_prepaymented,
                        )
                    )
                ).all()
                return bookings
        except Exception as e:
            print(f"Error in get_booking_by_start_date: {e}")
            LoggerService.error(__name__, "get_booking_by_start_date", e)

    def get_booking_by_finish_date(self, end_date: date):
        """Get all bookings ending on a specific date."""
        try:
            with self.Session() as session:
                bookings = session.scalars(
                    select(BookingBase).where(
                        and_(
                            func.date(BookingBase.end_date) == end_date,
                            ~BookingBase.is_canceled,
                            ~BookingBase.is_done,
                            BookingBase.is_prepaymented,
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
        """Get bookings within a date range."""
        try:
            with self.Session() as session:
                if not is_admin:
                    bookings = session.scalars(
                        select(BookingBase)
                        .where(
                            and_(
                                BookingBase.start_date >= from_date,
                                BookingBase.start_date <= to_date,
                                ~BookingBase.is_canceled,
                                ~BookingBase.is_done,
                                BookingBase.is_prepaymented,
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
        """Get all bookings overlapping with a specific day."""
        try:
            with self.Session() as session:
                start_of_day = datetime.combine(target_date, datetime.min.time())
                end_of_day = datetime.combine(target_date, datetime.max.time())
                bookings = session.scalars(
                    select(BookingBase).where(
                        and_(
                            ~BookingBase.is_canceled,
                            ~BookingBase.is_done,
                            BookingBase.is_prepaymented,
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
        """Get all bookings overlapping with a specific month."""
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
                        ~BookingBase.is_canceled,
                        ~BookingBase.is_done,
                        BookingBase.is_prepaymented,
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
            print(f"Error in get_bookings_by_month: {e}")
            LoggerService.error(__name__, "get_bookings_by_month", e)
            return []

    def is_booking_between_dates(self, start: datetime, end: datetime) -> bool:
        """Check if there are any bookings between the given dates."""
        try:
            with self.Session() as session:
                overlapping_bookings = session.scalars(
                    select(BookingBase).where(
                        and_(
                            ~BookingBase.is_canceled,
                            ~BookingBase.is_done,
                            BookingBase.is_prepaymented,
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
        """Get booking by ID."""
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
        """Get all active bookings for a user."""
        user = self.user_service.get_user_by_contact(user_contact)
        if not user:
            return []

        try:
            with self.Session() as session:
                bookings = session.scalars(
                    select(BookingBase).where(
                        and_(
                            BookingBase.user_id == user.id,
                            ~BookingBase.is_canceled,
                            ~BookingBase.is_done,
                            BookingBase.is_prepaymented,
                        )
                    )
                ).all()
                return bookings
        except Exception as e:
            print(f"Error in get_booking_by_user_contact: {e}")
            LoggerService.error(__name__, "get_booking_by_user_contact", e)

    def get_unpaid_bookings(self) -> Sequence[BookingBase]:
        """Get all unpaid, active bookings."""
        try:
            with self.Session() as session:
                bookings = session.scalars(
                    select(BookingBase).where(
                        and_(
                            ~BookingBase.is_prepaymented,
                            ~BookingBase.is_canceled,
                            ~BookingBase.is_done,
                        )
                    ).order_by(BookingBase.start_date)
                ).all()
                return bookings
        except Exception as e:
            print(f"Error in get_unpaid_bookings: {e}")
            LoggerService.error(__name__, "get_unpaid_bookings", e)
            return []

    def get_all_chat_ids(self) -> list[int]:
        """Get all unique chat IDs from bookings (legacy method)."""
        try:
            with self.Session() as session:
                # Use distinct() to get unique chat_ids
                # Some users may have multiple bookings
                chat_ids = session.scalars(
                    select(distinct(BookingBase.chat_id))
                ).all()

                # Convert to list and return
                return list(chat_ids)
        except Exception as e:
            print(f"Error in get_all_chat_ids: {e}")
            LoggerService.error(__name__, "get_all_chat_ids", e)
            return []  # Return empty list on error

    def get_done_booking_count(self, user_id: int) -> int:
        """Get count of completed bookings for a user."""
        try:
            with self.Session() as session:
                count = session.scalar(
                    select(func.count())
                    .select_from(BookingBase)
                    .where(
                        and_(
                            BookingBase.user_id == user_id,
                            ~BookingBase.is_canceled,
                            BookingBase.is_done,
                        )
                    )
                )
                return count or 0
        except Exception as e:
            print(f"Error in get_done_booking_count: {e}")
            LoggerService.error(__name__, "get_done_booking_count", e)
            return 0

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
        """Update booking fields."""
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
                LoggerService.error(__name__, "update_booking", e)
