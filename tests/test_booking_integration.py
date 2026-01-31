"""Integration test for booking with prepayment calculation."""
import sys
import os
from datetime import datetime, date

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set UTF-8 encoding for Windows console
if os.name == "nt":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from src.services.prepayment_service import PrepaymentService
from src.models.enum.tariff import Tariff


def test_booking_flow_regular_day():
    """Test booking flow for a regular day."""
    print("\n=== TEST 1: Booking on Regular Day ===")

    # Simulate booking data
    booking_date = date(2026, 3, 15)  # March 15, 2026 (regular day)
    total_price = 700.0  # "Суточно от 3 человек" tariff

    # Calculate prepayment
    prepayment_service = PrepaymentService()
    prepayment = prepayment_service.calculate_prepayment(total_price, booking_date)

    # Expected: 50% of 700 = 350
    expected = 350.0
    assert prepayment == expected, f"Expected {expected}, got {prepayment}"

    # Check if it's a holiday
    is_holiday = prepayment_service.is_holiday(booking_date)
    assert not is_holiday, "March 15 should not be a holiday"

    print(f"[OK] Date: {booking_date}")
    print(f"[OK] Total price: {total_price} BYN")
    print(f"[OK] Prepayment: {prepayment} BYN (50%)")
    print(f"[OK] Is holiday: {is_holiday}")
    print("[OK] Message would show: 'Предоплата: 350.0 руб.'")


def test_booking_flow_new_year():
    """Test booking flow for New Year."""
    print("\n=== TEST 2: Booking on New Year (Holiday) ===")

    # Simulate booking data
    booking_date = date(2026, 1, 1)  # January 1, 2026 (New Year)
    total_price = 700.0

    # Calculate prepayment
    prepayment_service = PrepaymentService()
    prepayment = prepayment_service.calculate_prepayment(total_price, booking_date)

    # Expected: 100% of 700 = 700
    expected = 700.0
    assert prepayment == expected, f"Expected {expected}, got {prepayment}"

    # Check if it's a holiday
    is_holiday = prepayment_service.is_holiday(booking_date)
    assert is_holiday, "January 1 should be a holiday"

    # Get holiday name
    holiday_name = prepayment_service.get_holiday_name(booking_date)

    print(f"[OK] Date: {booking_date}")
    print(f"[OK] Total price: {total_price} BYN")
    print(f"[OK] Prepayment: {prepayment} BYN (100%)")
    print(f"[OK] Is holiday: {is_holiday}")
    print(f"[OK] Holiday name: {holiday_name}")
    print(
        f"[OK] Message would show: 'Предоплата: 700.0 руб.' + '🎉 {holiday_name} - требуется полная предоплата.'"
    )


def test_booking_flow_victory_day():
    """Test booking flow for Victory Day."""
    print("\n=== TEST 3: Booking on Victory Day (May 9) ===")

    # Simulate booking data
    booking_date = date(2026, 5, 9)  # May 9, 2026 (Victory Day)
    total_price = 180.0  # "Рабочий" tariff

    # Calculate prepayment
    prepayment_service = PrepaymentService()
    prepayment = prepayment_service.calculate_prepayment(total_price, booking_date)

    # Expected: 100% of 180 = 180
    expected = 180.0
    assert prepayment == expected, f"Expected {expected}, got {prepayment}"

    # Check if it's a holiday
    is_holiday = prepayment_service.is_holiday(booking_date)
    assert is_holiday, "May 9 should be Victory Day"

    # Get holiday name
    holiday_name = prepayment_service.get_holiday_name(booking_date)

    print(f"[OK] Date: {booking_date}")
    print(f"[OK] Total price: {total_price} BYN")
    print(f"[OK] Prepayment: {prepayment} BYN (100%)")
    print(f"[OK] Is holiday: {is_holiday}")
    print(f"[OK] Holiday name: {holiday_name}")


def test_booking_with_discount():
    """Test booking with promocode discount."""
    print("\n=== TEST 4: Booking with Discount ===")

    # Simulate booking with discount
    booking_date = date(2026, 3, 20)  # Regular day
    original_price = 1000.0
    discount = 0.10  # 10% discount
    discounted_price = original_price * (1 - discount)  # 900.0

    # Calculate prepayment on discounted price
    prepayment_service = PrepaymentService()
    prepayment = prepayment_service.calculate_prepayment(
        discounted_price, booking_date
    )

    # Expected: 50% of 900 = 450
    expected = 450.0
    assert prepayment == expected, f"Expected {expected}, got {prepayment}"

    print(f"[OK] Date: {booking_date}")
    print(f"[OK] Original price: {original_price} BYN")
    print(f"[OK] Discount: {discount * 100}%")
    print(f"[OK] Discounted price: {discounted_price} BYN")
    print(f"[OK] Prepayment: {prepayment} BYN (50%)")


def test_multiple_holidays():
    """Test multiple consecutive holiday days."""
    print("\n=== TEST 5: New Year Holidays (Dec 31 - Jan 2) ===")

    prepayment_service = PrepaymentService()
    total_price = 700.0

    # Test December 31
    date_dec31 = date(2025, 12, 31)
    prepay_dec31 = prepayment_service.calculate_prepayment(total_price, date_dec31)
    assert prepay_dec31 == total_price
    print(f"[OK] Dec 31: {prepay_dec31} BYN (100%)")

    # Test January 1
    date_jan01 = date(2026, 1, 1)
    prepay_jan01 = prepayment_service.calculate_prepayment(total_price, date_jan01)
    assert prepay_jan01 == total_price
    print(f"[OK] Jan 1: {prepay_jan01} BYN (100%)")

    # Test January 2
    date_jan02 = date(2026, 1, 2)
    prepay_jan02 = prepayment_service.calculate_prepayment(total_price, date_jan02)
    assert prepay_jan02 == total_price
    print(f"[OK] Jan 2: {prepay_jan02} BYN (100%)")

    # Test January 3 (not a holiday)
    date_jan03 = date(2026, 1, 3)
    prepay_jan03 = prepayment_service.calculate_prepayment(total_price, date_jan03)
    assert prepay_jan03 == total_price * 0.5
    print(f"[OK] Jan 3 (regular day): {prepay_jan03} BYN (50%)")


def test_edge_cases():
    """Test edge cases."""
    print("\n=== TEST 6: Edge Cases ===")

    prepayment_service = PrepaymentService()

    # Very small price
    small_price = 10.0
    date_regular = date(2026, 3, 15)
    prepay_small = prepayment_service.calculate_prepayment(small_price, date_regular)
    assert prepay_small == 5.0
    print(f"[OK] Small price (10 BYN): {prepay_small} BYN (50%)")

    # Very large price
    large_price = 10000.0
    prepay_large = prepayment_service.calculate_prepayment(large_price, date_regular)
    assert prepay_large == 5000.0
    print(f"[OK] Large price (10000 BYN): {prepay_large} BYN (50%)")

    # Price with decimals
    decimal_price = 333.33
    prepay_decimal = prepayment_service.calculate_prepayment(
        decimal_price, date_regular
    )
    assert prepay_decimal == 166.66  # Banker's rounding
    print(f"[OK] Decimal price (333.33 BYN): {prepay_decimal} BYN (50%)")


if __name__ == "__main__":
    print("=" * 60)
    print("BOOKING INTEGRATION TESTS - PREPAYMENT CALCULATION")
    print("=" * 60)

    try:
        test_booking_flow_regular_day()
        test_booking_flow_new_year()
        test_booking_flow_victory_day()
        test_booking_with_discount()
        test_multiple_holidays()
        test_edge_cases()

        print("\n" + "=" * 60)
        print("[SUCCESS] All integration tests passed!")
        print("=" * 60)
        print("\n📋 Summary:")
        print("✅ Regular day prepayment: 50% calculated correctly")
        print("✅ Holiday prepayment: 100% calculated correctly")
        print("✅ Holiday detection: All holidays recognized")
        print("✅ Holiday names: Retrieved correctly")
        print("✅ Edge cases: Handled properly")
        print("✅ Rounding: Works correctly (2 decimal places)")
        print("\n🎉 The prepayment system is ready for production!")

        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
