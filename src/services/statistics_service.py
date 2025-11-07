import sys
import os
from datetime import datetime, timedelta
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
    active_users: int
    deactivated_users: int
    users_with_bookings: int
    users_with_completed: int
    conversion_rate: float
    avg_bookings_per_user: float


@dataclass
class GiftStats:
    """Gift certificate statistics"""

    total_gifts: int
    paid_gifts: int
    used_gifts: int
    unused_gifts: int
    gift_revenue: float


@dataclass
class Statistics:
    """Complete statistics report"""

    all_time: BookingStats
    year_to_date: BookingStats
    current_month: BookingStats
    users: UserStats
    gifts: GiftStats
    total_revenue: float
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
        year_end = datetime(now.year, 12, 31, 23, 59, 59)
        month_start = datetime(now.year, now.month, 1)

        # Calculate month end (last day of current month)
        if now.month == 12:
            month_end = datetime(now.year, 12, 31, 23, 59, 59)
        else:
            next_month = datetime(now.year, now.month + 1, 1)
            month_end = next_month - timedelta(seconds=1)

        # All-time stats
        all_time = self._get_booking_stats(start_date=None, end_date=None)

        # Year (full year, not just to date)
        ytd = self._get_booking_stats(start_date=year_start, end_date=year_end)

        # Current month (full month, not just to date)
        current_month = self._get_booking_stats(start_date=month_start, end_date=month_end)

        # User stats
        user_stats = self._get_user_stats()

        # Gift stats
        gift_stats = self._get_gift_stats()

        # Total revenue (bookings + gifts)
        total_revenue = all_time.total_revenue + gift_stats.gift_revenue

        return Statistics(
            all_time=all_time,
            year_to_date=ytd,
            current_month=current_month,
            users=user_stats,
            gifts=gift_stats,
            total_revenue=total_revenue,
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

        # Active and deactivated users
        active_users = self.db.get_active_users_count()
        deactivated_users = self.db.get_deactivated_users_count()

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
            active_users=active_users,
            deactivated_users=deactivated_users,
            users_with_bookings=users_with_bookings,
            users_with_completed=users_with_completed,
            conversion_rate=conversion_rate,
            avg_bookings_per_user=avg_bookings,
        )

    def _get_gift_stats(self) -> GiftStats:
        """Calculate gift certificate statistics."""
        # Total gifts
        total_gifts = self.db.get_total_gifts_count()

        # Paid gifts
        paid_gifts = self.db.get_paid_gifts_count()

        # Used gifts
        used_gifts = self.db.get_used_gifts_count()

        # Unused gifts (paid but not used)
        unused_gifts = paid_gifts - used_gifts

        # Gift revenue
        gift_revenue = self.db.get_gift_revenue()

        return GiftStats(
            total_gifts=total_gifts,
            paid_gifts=paid_gifts,
            used_gifts=used_gifts,
            unused_gifts=unused_gifts,
            gift_revenue=gift_revenue,
        )
