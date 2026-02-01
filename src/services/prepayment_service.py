import sys
import os
from datetime import date
from typing import List, Optional
from singleton_decorator import singleton
from src.models.holiday_prepayment_rule import HolidayPrepaymentRule
from src.services.file_service import FileService
from src.services.logger_service import LoggerService

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@singleton
class PrepaymentService:
    """Service for calculating prepayment with holiday rules."""

    _rules: List[HolidayPrepaymentRule] = []

    def get_applicable_rules(self, target_date: date) -> List[HolidayPrepaymentRule]:
        """Get all active rules for the specified date."""
        rules = self._try_load_rules()
        applicable = []

        for rule in rules:
            if rule.applies_to_date(target_date):
                applicable.append(rule)

        return applicable

    def get_effective_rule(
        self, target_date: date
    ) -> Optional[HolidayPrepaymentRule]:
        """
        Get the highest priority rule for the specified date.
        If multiple rules apply - take the first one (by rule_id).
        """
        applicable_rules = self.get_applicable_rules(target_date)
        return applicable_rules[0] if applicable_rules else None

    def is_holiday(self, target_date: date) -> bool:
        """Check if the date is a holiday."""
        return self.get_effective_rule(target_date) is not None

    def calculate_prepayment(self, total_price: float, booking_date: date) -> float:
        """
        Calculate prepayment based on price and date.

        PATTERN: Check rules -> apply percentage -> round

        Args:
            total_price: Total booking price
            booking_date: Booking start date

        Returns:
            Prepayment amount in rubles (rounded to 2 decimal places)
        """
        effective_rule = self.get_effective_rule(booking_date)

        if effective_rule:
            # HOLIDAY: apply percentage from rule
            percentage = effective_rule.prepayment_percentage
            prepayment = total_price * (percentage / 100.0)

            LoggerService.info(
                __name__,
                f"Holiday prepayment calculation: {effective_rule.name}, "
                f"{percentage}% of {total_price} = {prepayment}",
            )
        else:
            # REGULAR DAY: 50% prepayment
            prepayment = total_price * 0.5

            LoggerService.info(
                __name__,
                f"Standard prepayment calculation: 50% of {total_price} = {prepayment}",
            )

        # CRITICAL: round to 2 decimal places
        return round(prepayment, 2)

    def get_holiday_name(self, target_date: date) -> Optional[str]:
        """Get holiday name for the specified date (if any)."""
        rule = self.get_effective_rule(target_date)
        return rule.name if rule else None

    def get_prepayment_explanation(self, target_date: date) -> str:
        """Returns explanation text for prepayment amount."""
        rule = self.get_effective_rule(target_date)
        if rule:
            return f"🎉 <b>{rule.name}</b> - требуется полная предоплата (100%)"
        else:
            return "Стандартная предоплата составляет 50% от стоимости"

    def _try_load_rules(self) -> List[HolidayPrepaymentRule]:
        """
        Ленивая загрузка правил предоплаты.
        ПАТТЕРН: Singleton + lazy loading (как в DatePricingService)
        """
        if not self._rules:
            file_service = FileService()
            self._rules = file_service.get_holiday_prepayment_rules()
        return self._rules
