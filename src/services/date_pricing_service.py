import sys
import os
from datetime import date
from typing import List, Optional
from singleton_decorator import singleton
from src.models.date_pricing_rule import DatePricingRule
from src.services.file_service import FileService

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@singleton
class DatePricingService:
    _rules: List[DatePricingRule] = []

    def get_applicable_rules(self, target_date: date) -> List[DatePricingRule]:
        """Get all active rules that apply to the target date, sorted by priority (highest first)."""
        rules = self._try_load_rules()
        applicable = []

        for rule in rules:
            if rule.applies_to_date(target_date):
                applicable.append(rule)

        # Sort by rule_id for consistent ordering
        return sorted(applicable, key=lambda x: x.rule_id)

    def get_effective_rule(self, target_date: date) -> Optional[DatePricingRule]:
        """Get the highest priority rule that applies to the target date."""
        applicable_rules = self.get_applicable_rules(target_date)
        return applicable_rules[0] if applicable_rules else None

    def has_date_override(self, target_date: date) -> bool:
        """Check if there's any pricing override for the target date."""
        effective_rule = self.get_effective_rule(target_date)
        return effective_rule is not None and effective_rule.price_override is not None

    def get_price_override(
        self, target_date: date, duration_hours: int
    ) -> Optional[int]:
        """Get the price override for the target date and duration, if any."""
        effective_rule = self.get_effective_rule(target_date)
        if effective_rule and effective_rule.price_override is not None:
            return effective_rule.get_price_for_duration(duration_hours)
        return None

    def get_rule_description(self, target_date: date) -> Optional[str]:
        """Get the description of the effective rule for the target date."""
        effective_rule = self.get_effective_rule(target_date)
        if effective_rule:
            return effective_rule.description or effective_rule.name
        return None

    def _try_load_rules(self) -> List[DatePricingRule]:
        """Load date pricing rules using the singleton pattern similar to CalculationRateService."""
        if not self._rules:
            file_service = FileService()
            self._rules = file_service.get_date_pricing_rules()
        return self._rules
