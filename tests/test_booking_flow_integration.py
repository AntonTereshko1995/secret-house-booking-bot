"""
Integration test for complete booking flow.
Tests the exact sequence used in booking_handler.py
"""
import sys
import os
from unittest.mock import Mock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.session.session_service import SessionService
from src.models.enum.booking_step import BookingStep
from src.models.enum.tariff import Tariff
from datetime import datetime, timedelta


async def test_complete_booking_flow():
    """Test complete booking flow as used in booking_handler"""
    print("Testing complete booking flow...\n")

    # Setup
    service = SessionService(ttl_days=1)
    await service.initialize()

    # Create mock Update object
    mock_update = Mock()
    mock_update.effective_chat = Mock()
    mock_update.effective_chat.id = 123456

    print("Step 1: Initialize booking")
    await service.init_booking(mock_update)

    booking = await service.get_booking(mock_update)
    assert booking is not None, "[FAILED] Booking should exist after init"
    print("[OK] Booking initialized successfully")

    print("\nStep 2: Set navigation step")
    await service.update_booking_field(mock_update, "navigation_step", BookingStep.TARIFF)

    booking = await service.get_booking(mock_update)
    assert booking is not None, "[FAILED] Booking should exist after updating navigation_step"
    assert booking.navigation_step == BookingStep.TARIFF, f"[FAILED] Expected BookingStep.TARIFF, got {booking.navigation_step}"
    print(f"[OK] Navigation step set to: {booking.navigation_step}")

    print("\nStep 3: Set tariff")
    await service.update_booking_field(mock_update, "tariff", Tariff.DAY)

    booking = await service.get_booking(mock_update)
    assert booking is not None, "[FAILED] Booking should exist after updating tariff"
    assert booking.tariff == Tariff.DAY, f"[FAILED] Expected Tariff.DAY, got {booking.tariff}"
    print(f"[OK] Tariff set to: {booking.tariff}")

    print("\nStep 4: Set user contact")
    await service.update_booking_field(mock_update, "user_contact", "+1234567890")

    booking = await service.get_booking(mock_update)
    assert booking is not None, "[FAILED] Booking should exist after updating user_contact"
    assert booking.user_contact == "+1234567890", f"[FAILED] Expected +1234567890, got {booking.user_contact}"
    print(f"[OK] User contact set to: {booking.user_contact}")

    print("\nStep 5: Set booking dates")
    # Use timezone-aware datetime to match JSON serialization behavior
    from datetime import timezone
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=1)

    await service.update_booking_field(mock_update, "start_booking_date", start_date)
    await service.update_booking_field(mock_update, "finish_booking_date", end_date)

    booking = await service.get_booking(mock_update)
    assert booking is not None, "[FAILED] Booking should exist after updating dates"

    print(f"  DEBUG: Expected start_date type: {type(start_date)}, value: {start_date}")
    print(f"  DEBUG: Retrieved start_booking_date type: {type(booking.start_booking_date)}, value: {booking.start_booking_date}")
    print(f"  DEBUG: Are equal? {booking.start_booking_date == start_date}")

    # Dates might have microsecond differences, check if they're close
    if booking.start_booking_date and booking.finish_booking_date:
        start_diff = abs((booking.start_booking_date - start_date).total_seconds()) if isinstance(booking.start_booking_date, datetime) else 999
        end_diff = abs((booking.finish_booking_date - end_date).total_seconds()) if isinstance(booking.finish_booking_date, datetime) else 999

        assert start_diff < 1, f"[FAILED] Start date mismatch: diff={start_diff}s"
        assert end_diff < 1, f"[FAILED] End date mismatch: diff={end_diff}s"
        print(f"[OK] Dates set: {start_date.date()} to {end_date.date()}")
    else:
        print(f"[FAILED] Dates are None or wrong type!")
        print(f"  start_booking_date: {booking.start_booking_date}")
        print(f"  finish_booking_date: {booking.finish_booking_date}")
        raise AssertionError("[FAILED] Dates validation failed")

    print("\nStep 6: Set number of guests")
    await service.update_booking_field(mock_update, "number_of_guests", 4)

    booking = await service.get_booking(mock_update)
    assert booking is not None, "[FAILED] Booking should exist after updating guests"
    assert booking.number_of_guests == 4, f"[FAILED] Expected 4 guests, got {booking.number_of_guests}"
    print(f"[OK] Number of guests set to: {booking.number_of_guests}")

    print("\nStep 7: Add extras (sauna, photoshoot)")
    await service.update_booking_field(mock_update, "is_sauna_included", True)
    await service.update_booking_field(mock_update, "is_photoshoot_included", True)

    booking = await service.get_booking(mock_update)
    assert booking is not None, "[FAILED] Booking should exist after updating extras"
    assert booking.is_sauna_included is True, "[FAILED] Sauna should be included"
    assert booking.is_photoshoot_included is True, "[FAILED] Photoshoot should be included"
    print(f"[OK] Extras added: sauna={booking.is_sauna_included}, photoshoot={booking.is_photoshoot_included}")

    print("\nStep 8: Set price")
    await service.update_booking_field(mock_update, "price", 500.50)

    booking = await service.get_booking(mock_update)
    assert booking is not None, "[FAILED] Booking should exist after updating price"
    assert booking.price == 500.50, f"[FAILED] Expected 500.50, got {booking.price}"
    print(f"[OK] Price set to: {booking.price}")

    print("\nStep 9: Set booking comment")
    await service.update_booking_field(mock_update, "booking_comment", "Test booking comment")

    booking = await service.get_booking(mock_update)
    assert booking is not None, "[FAILED] Booking should exist after updating comment"
    assert booking.booking_comment == "Test booking comment", f"[FAILED] Comment mismatch"
    print(f"[OK] Comment set to: {booking.booking_comment}")

    print("\nStep 10: Final verification - get all data")
    final_booking = await service.get_booking(mock_update)

    assert final_booking is not None, "[FAILED] Final booking should not be None"
    assert final_booking.navigation_step == BookingStep.TARIFF
    assert final_booking.tariff == Tariff.DAY
    assert final_booking.user_contact == "+1234567890"
    assert final_booking.number_of_guests == 4
    assert final_booking.is_sauna_included is True
    assert final_booking.is_photoshoot_included is True
    assert final_booking.price == 500.50
    assert final_booking.booking_comment == "Test booking comment"

    print("\n[SUCCESS] ALL BOOKING FLOW TESTS PASSED!")
    print("\nFinal booking state:")
    print(f"  - Tariff: {final_booking.tariff}")
    print(f"  - Contact: {final_booking.user_contact}")
    print(f"  - Guests: {final_booking.number_of_guests}")
    print(f"  - Sauna: {final_booking.is_sauna_included}")
    print(f"  - Photoshoot: {final_booking.is_photoshoot_included}")
    print(f"  - Price: {final_booking.price}")
    print(f"  - Comment: {final_booking.booking_comment}")

    # Cleanup
    await service.clear_booking(mock_update)
    booking = await service.get_booking(mock_update)
    assert booking is None, "[FAILED] Booking should be None after clear"
    await service.shutdown()
    print("\n[OK] Cleanup successful")


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(test_complete_booking_flow())
        print("\n[SUCCESS] Integration test completed successfully!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
