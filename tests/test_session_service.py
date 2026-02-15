"""
Unit tests for SessionService class.
Tests booking, feedback, and other draft operations.
"""
import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.session.session_service import SessionService
from src.models.booking_draft import BookingDraft
from src.models.feedback import Feedback
from src.models.cancel_booking_draft import CancelBookingDraft
from src.models.enum.tariff import Tariff


class TestSessionService:
    """Test suite for SessionService"""

    def setup_method(self):
        """Setup before each test"""
        self.test_file = Path("test_session_service.json")
        if self.test_file.exists():
            self.test_file.unlink()

        # Create mock Update object
        self.mock_update = Mock()
        self.mock_update.effective_chat = Mock()
        self.mock_update.effective_chat.id = 123456

    def teardown_method(self):
        """Cleanup after each test"""
        if self.test_file.exists():
            self.test_file.unlink()

    async def test_booking_operations(self):
        """Test booking CRUD operations"""
        service = SessionService(ttl_days=1)
        await service.initialize()

        # Init booking
        await service.init_booking(self.mock_update)

        # Get booking - should be empty draft
        booking = await service.get_booking(self.mock_update)
        assert booking is not None, "Booking should exist after init"
        assert booking.user_contact is None, "New booking should have no contact"

        # Update field
        await service.update_booking_field(self.mock_update, "user_contact", "+1234567890")

        # Verify update
        booking = await service.get_booking(self.mock_update)
        assert booking.user_contact == "+1234567890", "Contact should be updated"

        # Update tariff
        await service.update_booking_field(self.mock_update, "tariff", Tariff.DAY)
        booking = await service.get_booking(self.mock_update)
        assert booking.tariff == Tariff.DAY, "Tariff should be updated"

        # Clear booking
        await service.clear_booking(self.mock_update)
        booking = await service.get_booking(self.mock_update)
        assert booking is None, "Booking should be None after clear"

        await service.shutdown()
        print("[OK] test_booking_operations passed")

    async def test_booking_multiple_fields(self):
        """Test updating multiple booking fields at once"""
        service = SessionService(ttl_days=1)
        await service.initialize()

        await service.init_booking(self.mock_update)

        # Update multiple fields
        fields = {
            "user_contact": "+9876543210",
            "number_of_guests": 4,
            "is_sauna_included": True,
            "is_photoshoot_included": True,
        }
        await service.update_booking_fields(self.mock_update, fields)

        # Verify all updates
        booking = await service.get_booking(self.mock_update)
        assert booking.user_contact == "+9876543210"
        assert booking.number_of_guests == 4
        assert booking.is_sauna_included is True
        assert booking.is_photoshoot_included is True

        await service.shutdown()
        print("[OK] test_booking_multiple_fields passed")

    async def test_feedback_operations(self):
        """Test feedback CRUD operations"""
        service = SessionService(ttl_days=1)
        await service.initialize()

        # Init feedback
        await service.init_feedback(self.mock_update)

        # Get feedback
        feedback = await service.get_feedback(self.mock_update)
        assert feedback is not None, "Feedback should exist after init"
        assert feedback.booking_id is None, "New feedback should have no booking_id"

        # Update field
        await service.update_feedback_field(self.mock_update, "booking_id", 42)
        await service.update_feedback_field(self.mock_update, "expectations_rating", 9)
        await service.update_feedback_field(self.mock_update, "comfort_rating", 10)

        # Verify updates
        feedback = await service.get_feedback(self.mock_update)
        assert feedback.booking_id == 42
        assert feedback.expectations_rating == 9
        assert feedback.comfort_rating == 10

        # Clear feedback
        await service.clear_feedback(self.mock_update)
        feedback = await service.get_feedback(self.mock_update)
        assert feedback is None, "Feedback should be None after clear"

        await service.shutdown()
        print("[OK] test_feedback_operations passed")

    async def test_cancel_booking_operations(self):
        """Test cancel booking CRUD operations"""
        service = SessionService(ttl_days=1)
        await service.initialize()

        # Init
        await service.init_cancel_booking(self.mock_update)

        # Get
        draft = await service.get_cancel_booking(self.mock_update)
        assert draft is not None
        assert draft.user_contact is None

        # Update
        await service.update_cancel_booking_field(self.mock_update, "user_contact", "+1111111111")
        await service.update_cancel_booking_field(self.mock_update, "selected_booking_id", 99)

        # Verify
        draft = await service.get_cancel_booking(self.mock_update)
        assert draft.user_contact == "+1111111111"
        assert draft.selected_booking_id == 99

        # Clear
        await service.clear_cancel_booking(self.mock_update)
        assert await service.get_cancel_booking(self.mock_update) is None

        await service.shutdown()
        print("[OK] test_cancel_booking_operations passed")

    async def test_gift_certificate_operations(self):
        """Test gift certificate CRUD operations"""
        service = SessionService(ttl_days=1)
        await service.initialize()

        # Init
        await service.init_gift_certificate(self.mock_update)

        # Get
        draft = await service.get_gift_certificate(self.mock_update)
        assert draft is not None
        assert draft.tariff is None

        # Update
        await service.update_gift_certificate_field(self.mock_update, "tariff", Tariff.HOURS_12)
        await service.update_gift_certificate_field(self.mock_update, "is_sauna_included", True)
        await service.update_gift_certificate_field(self.mock_update, "price", 500)

        # Verify
        draft = await service.get_gift_certificate(self.mock_update)
        assert draft.tariff == Tariff.HOURS_12
        assert draft.is_sauna_included is True
        assert draft.price == 500

        # Clear
        await service.clear_gift_certificate(self.mock_update)
        assert await service.get_gift_certificate(self.mock_update) is None

        await service.shutdown()
        print("[OK] test_gift_certificate_operations passed")

    async def test_multiple_users(self):
        """Test that different users have separate sessions"""
        service = SessionService(ttl_days=1)
        await service.initialize()

        # Create second user
        mock_update2 = Mock()
        mock_update2.effective_chat = Mock()
        mock_update2.effective_chat.id = 999999

        # Init bookings for both users
        await service.init_booking(self.mock_update)
        await service.init_booking(mock_update2)

        # Update user 1
        await service.update_booking_field(self.mock_update, "user_contact", "user1@example.com")

        # Update user 2
        await service.update_booking_field(mock_update2, "user_contact", "user2@example.com")

        # Verify separation
        booking1 = await service.get_booking(self.mock_update)
        booking2 = await service.get_booking(mock_update2)

        assert booking1.user_contact == "user1@example.com"
        assert booking2.user_contact == "user2@example.com"

        await service.shutdown()
        print("[OK] test_multiple_users passed")

    async def test_update_nonexistent_booking(self):
        """Test updating field on non-existent booking creates new one"""
        service = SessionService(ttl_days=1)
        await service.initialize()

        # Update field without init
        await service.update_booking_field(self.mock_update, "user_contact", "auto@example.com")

        # Should create new booking
        booking = await service.get_booking(self.mock_update)
        assert booking is not None
        assert booking.user_contact == "auto@example.com"

        await service.shutdown()
        print("[OK] test_update_nonexistent_booking passed")


def run_async_test(coro):
    """Helper to run async test"""
    return asyncio.run(coro)


if __name__ == "__main__":
    print("Running SessionService tests...\n")
    test_suite = TestSessionService()

    tests = [
        test_suite.test_booking_operations(),
        test_suite.test_booking_multiple_fields(),
        test_suite.test_feedback_operations(),
        test_suite.test_cancel_booking_operations(),
        test_suite.test_gift_certificate_operations(),
        test_suite.test_multiple_users(),
        test_suite.test_update_nonexistent_booking(),
    ]

    try:
        for test in tests:
            test_suite.setup_method()
            run_async_test(test)
            test_suite.teardown_method()

        print("\n[SUCCESS] All SessionService tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n[FAILED] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
