import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from telegram.error import Forbidden, BadRequest

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.database_service import DatabaseService
from src.services.chat_validation_service import ChatValidationService
from db.models.user import UserBase


class TestDatabaseServiceChatMethods:
    """Test DatabaseService chat_id management methods."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test database service."""
        self.db_service = DatabaseService()
        # Clean up test data before each test
        yield
        # Clean up after test
        try:
            # Remove test users
            with self.db_service.Session() as session:
                test_contacts = ["test_user_1", "test_user_2", "test_user_3", "test_user_4"]
                for contact in test_contacts:
                    user = session.query(UserBase).filter_by(contact=contact).first()
                    if user:
                        session.delete(user)
                session.commit()
        except Exception:
            pass

    def test_update_user_chat_id_new_user(self):
        """Test creating a new user with chat_id."""
        contact = "test_user_1"
        chat_id = 123456789

        user = self.db_service.update_user_chat_id(contact, chat_id)

        assert user is not None
        assert user.contact == contact
        assert user.chat_id == chat_id

        # Verify it's in database
        retrieved_user = self.db_service.get_user_by_contact(contact)
        assert retrieved_user is not None
        assert retrieved_user.chat_id == chat_id

    def test_update_user_chat_id_duplicate_handling(self):
        """Test that duplicate chat_id removes old user's chat_id."""
        contact_a = "test_user_2"
        contact_b = "test_user_3"
        chat_id = 987654321

        # User A gets chat_id first
        user_a = self.db_service.update_user_chat_id(contact_a, chat_id)
        assert user_a.chat_id == chat_id

        # User B tries to use same chat_id
        user_b = self.db_service.update_user_chat_id(contact_b, chat_id)
        assert user_b.chat_id == chat_id

        # Verify User A's chat_id was set to None
        user_a_updated = self.db_service.get_user_by_contact(contact_a)
        assert user_a_updated.chat_id is None

        # Verify User B has the chat_id
        user_b_updated = self.db_service.get_user_by_contact(contact_b)
        assert user_b_updated.chat_id == chat_id

    def test_get_all_user_chat_ids(self):
        """Test getting all user chat IDs filters out None values."""
        # Create users with chat_ids
        self.db_service.update_user_chat_id("test_user_1", 111111)
        self.db_service.update_user_chat_id("test_user_2", 222222)
        self.db_service.update_user_chat_id("test_user_3", 333333)

        # Create user without chat_id
        self.db_service.get_or_create_user("test_user_4")

        # Get all chat_ids
        chat_ids = self.db_service.get_all_user_chat_ids()

        # Should return only 3 chat_ids (excludes the None value)
        assert len(chat_ids) == 3
        assert 111111 in chat_ids
        assert 222222 in chat_ids
        assert 333333 in chat_ids

    def test_remove_user_chat_id(self):
        """Test removing chat_id from user."""
        contact = "test_user_1"
        chat_id = 555555

        # Create user with chat_id
        user = self.db_service.update_user_chat_id(contact, chat_id)
        assert user.chat_id == chat_id

        # Remove chat_id
        result = self.db_service.remove_user_chat_id(chat_id)
        assert result is True

        # Verify chat_id is None
        user_updated = self.db_service.get_user_by_contact(contact)
        assert user_updated.chat_id is None

        # Try removing non-existent chat_id
        result = self.db_service.remove_user_chat_id(999999)
        assert result is False


class TestChatValidationService:
    """Test ChatValidationService chat validation methods."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test validation service."""
        self.validation_service = ChatValidationService()

    @pytest.mark.asyncio
    async def test_is_chat_valid_with_valid_chat(self):
        """Test is_chat_valid returns True for valid chat."""
        # Mock bot that succeeds
        mock_bot = AsyncMock()
        mock_bot.send_chat_action = AsyncMock(return_value=True)

        chat_id = 123456

        result = await self.validation_service.is_chat_valid(mock_bot, chat_id)

        assert result is True
        mock_bot.send_chat_action.assert_called_once_with(
            chat_id=chat_id,
            action="typing"
        )

    @pytest.mark.asyncio
    async def test_is_chat_valid_with_blocked_chat(self):
        """Test is_chat_valid returns False when user blocked bot."""
        # Mock bot that raises Forbidden
        mock_bot = AsyncMock()
        mock_bot.send_chat_action = AsyncMock(side_effect=Forbidden("User blocked bot"))

        chat_id = 123456

        result = await self.validation_service.is_chat_valid(mock_bot, chat_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_is_chat_valid_with_invalid_chat(self):
        """Test is_chat_valid returns False for non-existent chat."""
        # Mock bot that raises BadRequest
        mock_bot = AsyncMock()
        mock_bot.send_chat_action = AsyncMock(side_effect=BadRequest("Chat not found"))

        chat_id = 123456

        result = await self.validation_service.is_chat_valid(mock_bot, chat_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_all_chat_ids(self):
        """Test validate_all_chat_ids returns correct results."""
        # Mock bot
        mock_bot = AsyncMock()

        # First chat is valid, second is forbidden, third is bad request
        mock_bot.send_chat_action = AsyncMock(side_effect=[
            True,  # Valid
            Forbidden("Blocked"),  # Blocked
            BadRequest("Not found"),  # Not found
        ])

        chat_ids = [111, 222, 333]

        results = await self.validation_service.validate_all_chat_ids(mock_bot, chat_ids)

        assert results["total_checked"] == 3
        assert results["valid"] == 1
        assert results["invalid"] == 2
        assert 222 in results["invalid_ids"]
        assert 333 in results["invalid_ids"]
        assert 111 not in results["invalid_ids"]
