# Date-Specific Pricing Rules Implementation

## Goal
Create a configurable system for setting specific prices and minimum booking duration for individual dates or date ranges, allowing fine-grained control over pricing based on special occasions, holidays, or promotional periods.

## Why
- **Business Flexibility**: Enable dynamic pricing for high-demand periods (holidays, events)
- **Revenue Optimization**: Set premium prices for peak dates and promotional rates for off-peak periods
- **Operational Control**: Override standard tariff calculations with date-specific rules
- **User Experience**: Clear communication of special pricing when customers select dates

## What
A JSON-based configuration system that allows administrators to define:
1. **Date-specific pricing**: Fixed prices for specific dates or date ranges
2. **Minimum booking rules**: Custom minimum booking duration overrides
3. **Priority system**: Rule precedence when multiple rules apply to the same date
4. **Integration**: Seamless integration with existing rate calculation system

### Success Criteria
- [ ] JSON configuration file for date-specific pricing rules
- [ ] Modified calculation service to check date-specific rules before standard tariff calculation
- [ ] Support for single dates and date ranges
- [ ] Minimum booking duration overrides
- [ ] Rule validation and conflict resolution
- [ ] Integration with existing booking workflow
- [ ] Comprehensive test coverage for all rule scenarios

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- file: src/services/calculation_rate_service.py
  why: Current pricing calculation logic to extend
  critical: Uses FileService to load tariff_rate_sale.json, singleton pattern

- file: src/config/tariff_rate_sale.json
  why: Existing JSON structure pattern for pricing configuration
  critical: RentalPrice model structure with multi_day_prices dict

- file: src/models/rental_price.py
  why: Data model for pricing information
  critical: RentalPrice dataclass with price, duration_hours, multi_day_prices

- file: src/services/file_service.py
  why: File loading pattern to follow for new configuration
  critical: Singleton pattern, JSON loading with error handling

- file: src/helpers/date_time_helper.py
  why: Date range handling and overlap detection patterns
  critical: get_free_dayes_slots function for date availability logic

- url: https://stackoverflow.com/questions/9044084/efficient-date-range-overlap-calculation
  why: DateTime range overlap detection algorithms for date range rules
  critical: max(start1, start2) < min(end1, end2) for overlap detection

- url: https://configu.com/blog/working-with-python-configuration-files-tutorial-best-practices/
  why: JSON configuration best practices for Python
  critical: Validation, type safety, modular structure principles
```

### Current Codebase Tree
```bash
src/
├── config/
│   ├── tariff_rate.json              # Standard pricing config
│   ├── tariff_rate_sale.json         # Current sale pricing (active)
│   └── config.py                     # Environment configuration
├── services/
│   ├── calculation_rate_service.py   # Main pricing calculation service
│   └── file_service.py               # JSON file loading service
├── models/
│   ├── rental_price.py               # RentalPrice dataclass
│   └── enum/
│       └── tariff.py                 # Tariff enumeration
└── helpers/
    └── date_time_helper.py           # Date manipulation utilities
```

### Desired Codebase Tree with New Files
```bash
src/
├── config/
│   ├── tariff_rate.json
│   ├── tariff_rate_sale.json
│   └── date_pricing_rules.json      # NEW: Date-specific pricing rules
├── services/
│   ├── calculation_rate_service.py  # MODIFIED: Add date rule checking
│   ├── file_service.py               # MODIFIED: Add date rules loading
│   └── date_pricing_service.py      # NEW: Date-specific pricing logic
├── models/
│   ├── rental_price.py
│   └── date_pricing_rule.py          # NEW: Date pricing rule dataclass
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: FileService uses singleton pattern
# Example: Must follow existing pattern for consistency
@singleton
class FileService:
    _TARIFF_JSON = "src/config/tariff_rate_sale.json"

# CRITICAL: CalculationRateService is singleton and loads rates once
# Example: Need to ensure date rules are also cached properly
_rates = List[RentalPrice]  # Existing pattern

# CRITICAL: Date handling uses specific format and timezone considerations
# Example: date_time_helper.py uses %d.%m.%Y format for date parsing
parse_date(date_string: str, date_format="%d.%m.%Y") -> datetime

# CRITICAL: RentalPrice uses multi_day_prices dict for extended stays
# Example: {"1": 500, "2": 900, "3": 1300} for day-based pricing

# CRITICAL: Current system switches between tariff_rate.json and tariff_rate_sale.json
# Example: FileService._TARIFF_JSON points to sale version currently
```

## Implementation Blueprint

### Data Models and Structure

Create core data models for date-specific pricing rules:

```python
# src/models/date_pricing_rule.py
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from datetime import date
from typing import Optional, Dict
from enum import IntEnum

class RulePriority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass_json
@dataclass
class DatePricingRule:
    rule_id: str
    name: str
    start_date: str  # Format: "YYYY-MM-DD"
    end_date: str    # Format: "YYYY-MM-DD"
    price_override: Optional[int] = None  # Fixed price in rubles
    min_duration_hours: Optional[int] = None  # Minimum booking duration
    priority: RulePriority = RulePriority.MEDIUM
    is_active: bool = True
    description: Optional[str] = None

    # Multi-day pricing overrides (similar to existing pattern)
    multi_day_price_overrides: Optional[Dict[str, int]] = None
```

### List of Tasks to be Completed

```yaml
Task 1:
CREATE src/models/date_pricing_rule.py:
  - DEFINE DatePricingRule dataclass following RentalPrice pattern
  - INCLUDE dataclass_json decorator for JSON serialization
  - ADD validation for date format and logical consistency
  - IMPLEMENT priority system for rule conflicts

Task 2:
CREATE src/config/date_pricing_rules.json:
  - DESIGN JSON structure following tariff_rate.json pattern
  - INCLUDE example rules for documentation
  - ADD validation schema comments
  - STRUCTURE for single dates and date ranges

Task 3:
CREATE src/services/date_pricing_service.py:
  - IMPLEMENT DatePricingService as singleton following existing pattern
  - ADD rule loading from JSON configuration
  - IMPLEMENT date range overlap detection
  - ADD rule priority resolution logic
  - INCLUDE caching mechanism similar to CalculationRateService

Task 4:
MODIFY src/services/file_service.py:
  - ADD get_date_pricing_rules() method
  - FOLLOW existing pattern from get_tariff_rates()
  - INCLUDE error handling for missing/invalid files
  - MAINTAIN singleton consistency

Task 5:
MODIFY src/services/calculation_rate_service.py:
  - INJECT date rule checking in get_by_tariff method
  - ADD new method get_effective_price_for_date()
  - PRESERVE existing method signatures
  - IMPLEMENT rule precedence over standard tariffs

Task 6:
CREATE comprehensive test suite:
  - TEST date range overlap scenarios
  - TEST rule priority resolution
  - TEST integration with existing calculation service
  - TEST edge cases (invalid dates, conflicting rules)

Task 7:
UPDATE booking workflow integration:
  - MODIFY booking handlers to use new date-aware pricing
  - ENSURE minimum duration rules are enforced
  - ADD user feedback for special pricing
```

### Per Task Pseudocode

```python
# Task 3: DatePricingService Implementation
class DatePricingService:
    def __init__(self):
        self._rules: List[DatePricingRule] = []
        self._load_rules()

    def get_applicable_rules(self, target_date: date) -> List[DatePricingRule]:
        # PATTERN: Filter active rules by date overlap
        applicable = []
        for rule in self._rules:
            if self._date_in_range(target_date, rule.start_date, rule.end_date):
                applicable.append(rule)

        # PATTERN: Sort by priority (highest first)
        return sorted(applicable, key=lambda x: x.priority, reverse=True)

    def get_effective_rule(self, target_date: date) -> Optional[DatePricingRule]:
        # CRITICAL: Return highest priority rule for date
        rules = self.get_applicable_rules(target_date)
        return rules[0] if rules else None

    def _date_in_range(self, target: date, start_str: str, end_str: str) -> bool:
        # PATTERN: Use existing date parsing from date_time_helper
        start = datetime.strptime(start_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_str, "%Y-%m-%d").date()
        return start <= target <= end

# Task 5: CalculationRateService Integration
def get_effective_price_for_date(
    self,
    booking_date: date,
    tariff: Tariff,
    duration_hours: int
) -> int:
    # PATTERN: Check date rules first, fallback to standard calculation
    date_service = DatePricingService()
    effective_rule = date_service.get_effective_rule(booking_date)

    if effective_rule and effective_rule.price_override:
        # CRITICAL: Use date-specific pricing
        if duration_hours > 24:
            days = duration_hours // 24
            if effective_rule.multi_day_price_overrides:
                return effective_rule.multi_day_price_overrides.get(str(days),
                       effective_rule.price_override)
        return effective_rule.price_override

    # FALLBACK: Use standard tariff calculation
    return self.get_by_tariff(tariff).price
```

### Integration Points
```yaml
CONFIGURATION:
  - add file: src/config/date_pricing_rules.json
  - pattern: Follow tariff_rate.json structure with "pricing_rules" array

SERVICE LAYER:
  - modify: src/services/calculation_rate_service.py
  - pattern: Add date-aware methods while preserving existing API

VALIDATION:
  - add to: booking workflow handlers
  - pattern: Check minimum duration rules before confirming booking

CACHING:
  - implement: In-memory rule caching following singleton pattern
  - pattern: Load once, cache forever like existing tariff loading
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
uv run ruff check src/models/date_pricing_rule.py --fix
uv run ruff check src/services/date_pricing_service.py --fix
uv run mypy src/models/date_pricing_rule.py
uv run mypy src/services/date_pricing_service.py

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests
```python
# CREATE tests/test_date_pricing_service.py
def test_single_date_rule_applies():
    """Test rule applies to specific single date"""
    rule = DatePricingRule(
        rule_id="test_rule",
        name="Test Rule",
        start_date="2024-12-25",
        end_date="2024-12-25",
        price_override=1500
    )
    service = DatePricingService()
    service._rules = [rule]

    target_date = date(2024, 12, 25)
    effective_rule = service.get_effective_rule(target_date)
    assert effective_rule.price_override == 1500

def test_date_range_rule_applies():
    """Test rule applies across date range"""
    rule = DatePricingRule(
        rule_id="range_rule",
        name="Holiday Range",
        start_date="2024-12-31",
        end_date="2025-01-02",
        price_override=3000,
        min_duration_hours=48
    )
    # Test all dates in range apply the rule

def test_priority_resolution():
    """Test higher priority rules override lower priority"""
    low_rule = DatePricingRule(priority=RulePriority.LOW, price_override=1000)
    high_rule = DatePricingRule(priority=RulePriority.HIGH, price_override=2000)
    # Test high priority rule wins

def test_no_applicable_rules():
    """Test fallback when no rules apply to date"""
    service = DatePricingService()
    target_date = date(2024, 6, 15)
    effective_rule = service.get_effective_rule(target_date)
    assert effective_rule is None

def test_minimum_duration_enforcement():
    """Test minimum booking duration rules are enforced"""
    # Test booking validation with date-specific minimum durations
```

```bash
# Run and iterate until passing:
uv run pytest tests/test_date_pricing_service.py -v
# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Tests
```bash
# Test the complete pricing calculation flow
uv run python -c "
from src.services.calculation_rate_service import CalculationRateService
from src.models.enum.tariff import Tariff
from datetime import date

calc_service = CalculationRateService()
test_date = date(2024, 12, 25)  # Christmas day with special pricing
price = calc_service.get_effective_price_for_date(test_date, Tariff.DAY, 24)
print(f'Christmas Day Price: {price} rubles')
"

# Expected: Should show date-specific price if rule exists, standard price otherwise
```

## Final Validation Checklist
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `uv run ruff check src/`
- [ ] No type errors: `uv run mypy src/`
- [ ] Date rule configuration loads successfully
- [ ] Integration with existing booking flow works
- [ ] Rule priority resolution works correctly
- [ ] Edge cases handled gracefully (invalid dates, overlapping rules)
- [ ] Performance acceptable with rule checking enabled

## JSON Configuration Example

```json
{
  "pricing_rules": [
    {
      "rule_id": "christmas_2024",
      "name": "Christmas Day Premium",
      "start_date": "2024-12-25",
      "end_date": "2024-12-25",
      "price_override": 1500,
      "min_duration_hours": 24,
      "priority": 4,
      "is_active": true,
      "description": "Premium pricing for Christmas Day"
    },
    {
      "rule_id": "new_year_week_2025",
      "name": "New Year Week Special",
      "start_date": "2024-12-31",
      "end_date": "2025-01-07",
      "price_override": 1200,
      "min_duration_hours": 12,
      "priority": 3,
      "is_active": true,
      "description": "New Year celebration week pricing",
      "multi_day_price_overrides": {
        "1": 1200,
        "2": 2200,
        "3": 3000
      }
    },
    {
      "rule_id": "summer_promotion_2024",
      "name": "Summer Promotion",
      "start_date": "2024-06-01",
      "end_date": "2024-08-31",
      "price_override": 600,
      "min_duration_hours": 6,
      "priority": 1,
      "is_active": true,
      "description": "Summer promotional pricing"
    }
  ]
}
```

## Anti-Patterns to Avoid
- ❌ Don't modify existing tariff JSON files - create separate date rules file
- ❌ Don't skip date validation - malformed dates will cause runtime errors
- ❌ Don't ignore rule priority - multiple rules for same date need resolution
- ❌ Don't break existing pricing API - preserve backward compatibility
- ❌ Don't hardcode date formats - use consistent parsing throughout
- ❌ Don't forget to handle timezone considerations in date comparisons

## Confidence Score: 9/10

This PRP provides comprehensive context for one-pass implementation with:
- ✅ Complete existing codebase analysis and patterns to follow
- ✅ External documentation for date range overlap detection
- ✅ Detailed implementation blueprint with pseudocode
- ✅ Executable validation steps
- ✅ JSON configuration structure with examples
- ✅ Integration points clearly defined
- ✅ Error handling and edge cases covered
- ✅ Test cases for critical scenarios

The implementation should succeed in one pass due to the detailed context, existing patterns to follow, and comprehensive validation framework.