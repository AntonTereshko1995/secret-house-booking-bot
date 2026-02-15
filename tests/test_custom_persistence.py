"""
Unit tests for CustomPersistence class.
Tests Telegram conversation state persistence.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.session.persistence import CustomPersistence


class TestCustomPersistence:
    """Test suite for CustomPersistence"""

    def setup_method(self):
        """Setup before each test"""
        self.test_file = Path("test_persistence.json")
        if self.test_file.exists():
            self.test_file.unlink()

    def teardown_method(self):
        """Cleanup after each test"""
        if self.test_file.exists():
            self.test_file.unlink()

    async def test_conversation_state_storage(self):
        """Test storing and retrieving conversation states"""
        persistence = CustomPersistence()

        # Store conversation state
        handler_name = "booking_handler"
        key = (123456, 123456)  # (chat_id, user_id)
        state = "BOOKING_TARIFF"

        await persistence.update_conversation(handler_name, key, state)

        # Retrieve conversation states
        conversations = await persistence.get_conversations(handler_name)

        assert key in conversations, f"Key {key} should exist in conversations"
        assert conversations[key] == state, f"Expected state '{state}', got '{conversations[key]}'"

        print("[OK] test_conversation_state_storage passed")

    async def test_multiple_conversation_keys(self):
        """Test storing multiple conversation keys"""
        persistence = CustomPersistence()

        handler_name = "menu_handler"

        # Store multiple states
        await persistence.update_conversation(handler_name, (111, 111), "STATE_1")
        await persistence.update_conversation(handler_name, (222, 222), "STATE_2")
        await persistence.update_conversation(handler_name, (333, 333), "STATE_3")

        # Retrieve all
        conversations = await persistence.get_conversations(handler_name)

        assert len(conversations) == 3, f"Expected 3 conversations, got {len(conversations)}"
        assert conversations[(111, 111)] == "STATE_1"
        assert conversations[(222, 222)] == "STATE_2"
        assert conversations[(333, 333)] == "STATE_3"

        print("[OK] test_multiple_conversation_keys passed")

    async def test_update_existing_conversation(self):
        """Test updating an existing conversation state"""
        persistence = CustomPersistence()

        handler_name = "test_handler"
        key = (999, 999)

        # Initial state
        await persistence.update_conversation(handler_name, key, "INITIAL_STATE")

        # Update state
        await persistence.update_conversation(handler_name, key, "UPDATED_STATE")

        # Verify update
        conversations = await persistence.get_conversations(handler_name)
        assert conversations[key] == "UPDATED_STATE"

        print("[OK] test_update_existing_conversation passed")

    async def test_delete_conversation(self):
        """Test deleting a conversation by setting state to None"""
        persistence = CustomPersistence()

        handler_name = "delete_test"
        key = (888, 888)

        # Add conversation
        await persistence.update_conversation(handler_name, key, "SOME_STATE")

        # Verify it exists
        conversations = await persistence.get_conversations(handler_name)
        assert key in conversations

        # Delete by setting to None
        await persistence.update_conversation(handler_name, key, None)

        # Verify it's gone
        conversations = await persistence.get_conversations(handler_name)
        assert key not in conversations, "Conversation should be deleted"

        print("[OK] test_delete_conversation passed")

    async def test_nonexistent_handler(self):
        """Test getting conversations for non-existent handler returns empty dict"""
        persistence = CustomPersistence()

        conversations = await persistence.get_conversations("nonexistent_handler")

        assert isinstance(conversations, dict), "Should return dict"
        assert len(conversations) == 0, "Should return empty dict"

        print("[OK] test_nonexistent_handler passed")

    async def test_multiple_handlers(self):
        """Test that different handlers have separate conversation storage"""
        persistence = CustomPersistence()

        # Add conversations to different handlers
        await persistence.update_conversation("handler1", (100, 100), "HANDLER1_STATE")
        await persistence.update_conversation("handler2", (100, 100), "HANDLER2_STATE")

        # Retrieve separately
        conv1 = await persistence.get_conversations("handler1")
        conv2 = await persistence.get_conversations("handler2")

        # Verify separation
        assert conv1[(100, 100)] == "HANDLER1_STATE"
        assert conv2[(100, 100)] == "HANDLER2_STATE"

        print("[OK] test_multiple_handlers passed")

    async def test_tuple_key_serialization(self):
        """Test that tuple keys are properly serialized/deserialized"""
        persistence = CustomPersistence()

        handler_name = "serialization_test"
        key = (12345, 67890)
        state = "TEST_STATE"

        # Store
        await persistence.update_conversation(handler_name, key, state)

        # Retrieve
        conversations = await persistence.get_conversations(handler_name)

        # Verify tuple key is correctly restored
        assert key in conversations, "Tuple key should be restored correctly"
        assert isinstance(key, tuple), "Key should be a tuple"
        assert len(key) == 2, "Key should have 2 elements"
        assert all(isinstance(x, int) for x in key), "Key elements should be integers"

        print("[OK] test_tuple_key_serialization passed")

    async def test_empty_methods_dont_error(self):
        """Test that unimplemented methods don't raise errors"""
        persistence = CustomPersistence()

        # These methods should all be no-ops and not raise errors
        assert await persistence.get_user_data() == {}
        assert await persistence.get_chat_data() == {}
        assert await persistence.get_bot_data() == {}
        assert await persistence.get_callback_data() is None

        await persistence.update_user_data(123, {})
        await persistence.update_chat_data(456, {})
        await persistence.update_bot_data({})
        await persistence.update_callback_data(None)

        await persistence.drop_chat_data(789)
        await persistence.drop_user_data(101)

        await persistence.refresh_user_data(202, {})
        await persistence.refresh_chat_data(303, {})
        await persistence.refresh_bot_data({})

        await persistence.flush()

        print("[OK] test_empty_methods_dont_error passed")


def run_async_test(coro):
    """Helper to run async test"""
    return asyncio.run(coro)


if __name__ == "__main__":
    print("Running CustomPersistence tests...\n")
    test_suite = TestCustomPersistence()

    tests = [
        test_suite.test_conversation_state_storage(),
        test_suite.test_multiple_conversation_keys(),
        test_suite.test_update_existing_conversation(),
        test_suite.test_delete_conversation(),
        test_suite.test_nonexistent_handler(),
        test_suite.test_multiple_handlers(),
        test_suite.test_tuple_key_serialization(),
        test_suite.test_empty_methods_dont_error(),
    ]

    try:
        for test in tests:
            test_suite.setup_method()
            run_async_test(test)
            test_suite.teardown_method()

        print("\n[SUCCESS] All CustomPersistence tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n[FAILED] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
