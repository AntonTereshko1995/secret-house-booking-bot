import sys
import os
from datetime import datetime
from dataclasses import dataclass

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.database_service import DatabaseService
from singleton_decorator import singleton


@dataclass
class BookingStats:
    """Statistics for a specific time period"""

    total_bookings: int
    completed_bookings: int
    canceled_bookings: int
    active_bookings: int
    total_revenue: float
    average_price: float


@dataclass
class UserStats:
    """User-related statistics"""

    total_users: int
    users_with_bookings: int
    users_with_completed: int
    conversion_rate: float
    avg_bookings_per_user: float


@dataclass
class Statistics:
    """Complete statistics report"""

    all_time: BookingStats
    year_to_date: BookingStats
    current_month: BookingStats
    users: UserStats
    generated_at: datetime


@singleton
class StatisticsService:
    """Service for calculating booking and user statistics."""

    def __init__(self):
        self.db = DatabaseService()

    def get_complete_statistics(self) -> Statistics:
        """Generate complete statistics report for all time periods."""
        now = datetime.now()
        year_start = datetime(now.year, 1, 1)
        month_start = datetime(now.year, now.month, 1)

        # All-time stats
        all_time = self._get_booking_stats(start_date=None, end_date=None)

        # Year-to-date
        ytd = self._get_booking_stats(start_date=year_start, end_date=now)

        # Current month
        current_month = self._get_booking_stats(start_date=month_start, end_date=now)

        # User stats
        user_stats = self._get_user_stats()

        return Statistics(
            all_time=all_time,
            year_to_date=ytd,
            current_month=current_month,
            users=user_stats,
            generated_at=now,
        )

    def _get_booking_stats(
        self, start_date: datetime, end_date: datetime
    ) -> BookingStats:
        """Calculate booking statistics for a specific period."""
        # Total bookings (prepaid only)
        total = self.db.get_bookings_count_by_period(
            start_date, end_date, is_completed=None
        )

        # Completed bookings
        completed = self.db.get_bookings_count_by_period(
            start_date, end_date, is_completed=True
        )

        # Canceled bookings
        canceled = self.db.get_canceled_bookings_count(start_date, end_date)

        # Active bookings
        active = self.db.get_active_bookings_count(start_date, end_date)

        # Revenue (only from completed bookings)
        revenue = self.db.get_revenue_by_period(start_date, end_date)

        # Average price
        avg_price = revenue / completed if completed > 0 else 0

        return BookingStats(
            total_bookings=total,
            completed_bookings=completed,
            canceled_bookings=canceled,
            active_bookings=active,
            total_revenue=revenue,
            average_price=avg_price,
        )

    def _get_user_stats(self) -> UserStats:
        """Calculate user-related statistics."""
        # Total users
        total_users = self.db.get_total_users_count()

        # Users with at least 1 booking
        users_with_bookings = self.db.get_users_with_bookings_count()

        # Users with at least 1 completed booking
        users_with_completed = self.db.get_users_with_completed_count()

        # Conversion rate (users with bookings / total users)
        conversion_rate = (
            (users_with_bookings / total_users * 100) if total_users > 0 else 0
        )

        # Average bookings per active user
        avg_bookings = (
            self.db.get_bookings_count_by_period(None, None, is_completed=None)
            / users_with_bookings
            if users_with_bookings > 0
            else 0
        )

        return UserStats(
            total_users=total_users,
            users_with_bookings=users_with_bookings,
            users_with_completed=users_with_completed,
            conversion_rate=conversion_rate,
            avg_bookings_per_user=avg_bookings,
        )
