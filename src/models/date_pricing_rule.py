import sys
import os
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from datetime import date, datetime
from typing import Optional
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@dataclass_json
@dataclass
class DatePricingRule:
    rule_id: str
    name: str
    start_date: str  # Format: "YYYY-MM-DD"
    end_date: str    # Format: "YYYY-MM-DD"
    price_override: Optional[int] = None  # Fixed price in rubles
    is_active: bool = True
    description: Optional[str] = None
    start_time: Optional[str] = None  # Format: "HH:MM" (24-hour format)
    end_time: Optional[str] = None    # Format: "HH:MM" (24-hour format)

    def __post_init__(self):
        """Validate date format and logical consistency after initialization."""
        try:
            start_date_obj = datetime.strptime(self.start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(self.end_date, "%Y-%m-%d").date()

            if start_date_obj > end_date_obj:
                raise ValueError(f"Start date {self.start_date} cannot be after end date {self.end_date}")

        except ValueError as e:
            if "time data" in str(e):
                raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got start_date: {self.start_date}, end_date: {self.end_date}")
            raise

        # Validate time format if provided
        if self.start_time is not None:
            try:
                datetime.strptime(self.start_time, "%H:%M")
            except ValueError:
                raise ValueError(f"Invalid start_time format. Expected HH:MM, got: {self.start_time}")

        if self.end_time is not None:
            try:
                datetime.strptime(self.end_time, "%H:%M")
            except ValueError:
                raise ValueError(f"Invalid end_time format. Expected HH:MM, got: {self.end_time}")

        if self.price_override is not None and self.price_override < 0:
            raise ValueError(f"Price override cannot be negative: {self.price_override}")

    def applies_to_date(self, target_date: date) -> bool:
        """Check if this rule applies to the given date."""
        if not self.is_active:
            return False

        start_date_obj = datetime.strptime(self.start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(self.end_date, "%Y-%m-%d").date()

        return start_date_obj <= target_date <= end_date_obj

    def applies_to_datetime(self, target_datetime: datetime) -> bool:
        """Check if this rule applies to the given date and time."""
        if not self.is_active:
            return False

        # Check date range first
        target_date = target_datetime.date()
        if not self.applies_to_date(target_date):
            return False

        # If no time constraints specified, rule applies for the whole day
        if self.start_time is None or self.end_time is None:
            return True

        # Check time range
        target_time = target_datetime.time()
        start_time_obj = datetime.strptime(self.start_time, "%H:%M").time()
        end_time_obj = datetime.strptime(self.end_time, "%H:%M").time()

        # Handle time ranges that cross midnight
        if start_time_obj <= end_time_obj:
            # Normal time range (e.g., 09:00 to 18:00)
            return start_time_obj <= target_time <= end_time_obj
        else:
            # Time range crosses midnight (e.g., 22:00 to 06:00)
            return target_time >= start_time_obj or target_time <= end_time_obj

    def get_price_for_duration(self, duration_hours: int) -> Optional[int]:
        """Get the appropriate price for the given duration."""
        return self.price_override