"""Integration tests for PrepaymentService."""
import sys
import os
from datetime import date

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set UTF-8 encoding for Windows console
if os.name == "nt":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from src.services.prepayment_service import PrepaymentService


def test_standard_day_prepayment():
    """Test prepayment for a standard day (50%)."""
    service = PrepaymentService()

    # Test date: regular day (not a holiday)
    test_date = date(2026, 3, 15)  # March 15, 2026
    total_price = 1000.0

    prepayment = service.calculate_prepayment(total_price, test_date)

    expected = 500.0  # 50% of 1000
    assert prepayment == expected, f"Expected {expected}, got {prepayment}"
    print(f"[OK] Standard prepayment: {prepayment} BYN (50%)")


def test_holiday_prepayment():
    """Test prepayment for a holiday (100%)."""
    service = PrepaymentService()

    # Test date: New Year
    test_date = date(2026, 1, 1)  # January 1, 2026
    total_price = 1000.0

    prepayment = service.calculate_prepayment(total_price, test_date)

    expected = 1000.0  # 100% of 1000
    assert prepayment == expected, f"Expected {expected}, got {prepayment}"
    print(f"[OK] Holiday prepayment: {prepayment} BYN (100%)")

    holiday_name = service.get_holiday_name(test_date)
    print(f"     Holiday: {holiday_name}")


def test_recurring_holiday():
    """Test recurring holiday (Victory Day)."""
    service = PrepaymentService()

    # Victory Day: May 9
    test_date = date(2026, 5, 9)
    total_price = 800.0

    prepayment = service.calculate_prepayment(total_price, test_date)

    assert service.is_holiday(test_date), "May 9 must be a holiday"
    assert prepayment == 800.0, f"Expected 800.0, got {prepayment}"
    print(f"[OK] Victory Day: {prepayment} BYN (100%)")


def test_valentines_day():
    """Test Valentine's Day (February 14)."""
    service = PrepaymentService()

    test_date = date(2026, 2, 14)
    total_price = 600.0

    prepayment = service.calculate_prepayment(total_price, test_date)

    assert prepayment == 600.0, f"Expected 600.0, got {prepayment}"
    print(f"[OK] Valentine's Day: {prepayment} BYN (100%)")


def test_rounding():
    """Test prepayment rounding."""
    service = PrepaymentService()

    test_date = date(2026, 3, 20)  # Regular day
    total_price = 333.33

    prepayment = service.calculate_prepayment(total_price, test_date)

    # 50% of 333.33 = 166.665, Python rounds to 166.66 (banker's rounding)
    expected = 166.66
    assert prepayment == expected, f"Expected {expected}, got {prepayment}"
    print(f"[OK] Rounding works correctly: {prepayment}")


def test_new_year_eve():
    """Test New Year's Eve (December 31)."""
    service = PrepaymentService()

    test_date = date(2025, 12, 31)
    total_price = 700.0

    prepayment = service.calculate_prepayment(total_price, test_date)

    assert service.is_holiday(test_date), "December 31 must be a holiday"
    assert prepayment == 700.0, f"Expected 700.0, got {prepayment}"
    print(f"[OK] New Year's Eve: {prepayment} BYN (100%)")


def test_radonitsa_non_recurring():
    """Test Radonitsa (non-recurring holiday for 2026)."""
    service = PrepaymentService()

    test_date = date(2026, 4, 21)  # Radonitsa 2026
    total_price = 500.0

    prepayment = service.calculate_prepayment(total_price, test_date)

    assert service.is_holiday(test_date), "April 21, 2026 must be Radonitsa"
    assert prepayment == 500.0, f"Expected 500.0, got {prepayment}"
    print(f"[OK] Radonitsa 2026: {prepayment} BYN (100%)")


def test_all_holidays():
    """Test that all 13 holidays are recognized."""
    service = PrepaymentService()

    holidays = [
        (date(2026, 12, 31), "New Year's Eve"),
        (date(2026, 1, 1), "New Year"),
        (date(2026, 1, 2), "New Year Day 2"),
        (date(2026, 1, 7), "Orthodox Christmas"),
        (date(2026, 2, 14), "Valentine's Day"),
        (date(2026, 2, 23), "Defender's Day"),
        (date(2026, 3, 8), "Women's Day"),
        (date(2026, 4, 21), "Radonitsa"),
        (date(2026, 5, 1), "Labor Day"),
        (date(2026, 5, 9), "Victory Day"),
        (date(2026, 7, 3), "Independence Day"),
        (date(2026, 11, 7), "October Revolution"),
        (date(2026, 12, 25), "Catholic Christmas"),
    ]

    for test_date, holiday_name in holidays:
        assert service.is_holiday(
            test_date
        ), f"{holiday_name} on {test_date} must be recognized"

    print(f"[OK] All 13 holidays are recognized correctly")


if __name__ == "__main__":
    print("Running PrepaymentService integration tests...\n")

    try:
        test_standard_day_prepayment()
        test_holiday_prepayment()
        test_recurring_holiday()
        test_valentines_day()
        test_rounding()
        test_new_year_eve()
        test_radonitsa_non_recurring()
        test_all_holidays()

        print("\n[OK] All tests passed successfully!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
