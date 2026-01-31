import sys
import os
import re
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from datetime import date, datetime
from typing import Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@dataclass_json
@dataclass
class HolidayPrepaymentRule:
    """Prepayment rule for a holiday."""

    rule_id: str  # Unique identifier (e.g., "new_year_2026")
    date: str  # Specific date in format "YYYY-MM-DD" or "MM-DD" for recurring holidays
    is_recurring: bool  # True if holiday repeats every year
    prepayment_percentage: int  # Prepayment percentage (usually 100 for holidays)
    name: str  # Holiday name
    is_active: bool = True  # Can disable the rule
    description: Optional[str] = None  # Additional description

    def __post_init__(self):
        """Validation after initialization."""
        # Validate date format
        if self.is_recurring:
            # For recurring holidays: MM-DD
            if not re.match(r'^\d{2}-\d{2}$', self.date):
                raise ValueError(
                    f"Recurring date must be in MM-DD format: {self.date}"
                )
            # Additional validation for month and day
            try:
                month, day = map(int, self.date.split('-'))
                if not (1 <= month <= 12):
                    raise ValueError(f"Invalid month in date: {self.date}")
                if not (1 <= day <= 31):
                    raise ValueError(f"Invalid day in date: {self.date}")
            except Exception as e:
                raise ValueError(
                    f"Invalid recurring date format {self.date}: {e}"
                )
        else:
            # For non-recurring holidays: YYYY-MM-DD
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', self.date):
                raise ValueError(
                    f"Non-recurring date must be in YYYY-MM-DD format: {self.date}"
                )
            # Validate date is valid
            try:
                datetime.strptime(self.date, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError(
                    f"Invalid non-recurring date format {self.date}: {e}"
                )

        # Validate percentage
        if not 0 <= self.prepayment_percentage <= 100:
            raise ValueError(
                f"Prepayment percentage must be 0-100: {self.prepayment_percentage}"
            )

    def applies_to_date(self, target_date: date) -> bool:
        """Checks if this rule applies to the specified date."""
        if not self.is_active:
            return False

        if self.is_recurring:
            # Check only month and day
            date_str = target_date.strftime("%m-%d")
            return date_str == self.date
        else:
            # Check full date
            target_str = target_date.strftime("%Y-%m-%d")
            return target_str == self.date
