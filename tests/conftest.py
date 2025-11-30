"""
Pytest configuration and shared fixtures.
"""
import pytest
import sys
import os
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, Mock, patch
from pathlib import Path

# Set test environment variables BEFORE any imports
os.environ.setdefault("TELEGRAM_TOKEN", "test_token_123456")
os.environ.setdefault("BACKEND_API_URL", "http://localhost:8000")
os.environ.setdefault("BACKEND_API_KEY", "test_key")
os.environ.setdefault("ADMIN_CHAT_ID", "123456789")
os.environ.setdefault("INFORM_CHAT_ID", "123456789")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("CLEANING_HOURS", "2")
os.environ.setdefault("ENV", "test")

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from models.rental_price import RentalPrice
from models.enum.tariff import Tariff
from models.enum.bedroom import Bedroom
from models.date_pricing_rule import DatePricingRule


@pytest.fixture
def test_date():
    """Standard test date."""
    return date(2024, 6, 15)


@pytest.fixture
def test_datetime():
    """Standard test datetime."""
    return datetime(2024, 6, 15, 14, 0, 0)


@pytest.fixture
def sample_rental_price():
    """Sample rental price for testing."""
    return RentalPrice(
        tariff=1,  # DAY tariff
        name="Standard Day Rate",
        duration_hours=24,
        price=700,
        sauna_price=100,
        secret_room_price=50,
        second_bedroom_price=200,
        extra_hour_price=30,
        extra_people_price=50,
        photoshoot_price=100,
        max_people=6,
        is_check_in_time_limit=False,
        is_photoshoot=True,
        is_transfer=False,
        multi_day_prices={"1": 700, "2": 1300, "3": 1850},
    )


@pytest.fixture
def sample_date_pricing_rules():
    """Sample date pricing rules for testing."""
    return [
        DatePricingRule(
            rule_id="summer_2024",
            name="Summer Promotion",
            start_date="2024-06-01",
            end_date="2024-08-31",
            price_override=900,
        ),
        DatePricingRule(
            rule_id="new_year_2025",
            name="New Year Week",
            start_date="2024-12-31",
            end_date="2025-01-07",
            price_override=1500,
        ),
    ]


@pytest.fixture
def mock_telegram_update():
    """Mock Telegram Update object."""
    update = MagicMock()
    update.effective_chat.id = 123456789
    update.effective_user.id = 123456789
    update.effective_user.username = "test_user"
    update.effective_user.first_name = "Test"
    update.effective_user.last_name = "User"
    update.callback_query = None
    update.message = MagicMock()
    update.message.text = "/start"
    update.message.chat.id = 123456789
    return update


@pytest.fixture
def mock_telegram_context():
    """Mock Telegram Context object."""
    context = MagicMock()
    context.bot_data = {}
    context.user_data = {}
    context.chat_data = {}
    return context


@pytest.fixture
def mock_file_service():
    """Mock FileService for testing."""
    with patch("services.file_service.FileService") as mock:
        instance = mock.return_value
        instance.get_tariff_rates.return_value = []
        instance.get_date_pricing_rules.return_value = []
        yield instance


@pytest.fixture
def mock_redis_service():
    """Mock Redis service for testing."""
    with patch("services.redis.redis_session_service.RedisSessionService") as mock:
        instance = mock.return_value
        instance.get.return_value = None
        instance.set.return_value = True
        instance.delete.return_value = True
        yield instance


@pytest.fixture
def mock_database_service():
    """Mock DatabaseService for testing."""
    with patch("db.database_service.DatabaseService") as mock:
        instance = mock.return_value
        instance.session = MagicMock()
        yield instance


@pytest.fixture
def mock_calendar_service():
    """Mock CalendarService for testing."""
    with patch("services.calendar_service.CalendarService") as mock:
        instance = mock.return_value
        instance.get_available_dates.return_value = []
        instance.is_date_available.return_value = True
        yield instance


@pytest.fixture
def mock_gpt_service():
    """Mock GPTService for testing."""
    with patch("services.gpt_service.GPTService") as mock:
        instance = mock.return_value
        instance.get_response.return_value = "Test GPT response"
        yield instance


@pytest.fixture
def mock_settings_service():
    """Mock SettingsService for testing."""
    with patch("services.settings_service.SettingsService") as mock:
        instance = mock.return_value
        instance.get_admin_chat_ids.return_value = [123456789]
        yield instance


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    yield
    # Clear any singleton state if needed


@pytest.fixture
def temp_test_db(tmp_path):
    """Create a temporary test database."""
    db_path = tmp_path / "test.db"
    return str(db_path)


@pytest.fixture
def sample_booking_data():
    """Sample booking data for testing."""
    return {
        "user_id": 123456789,
        "chat_id": 123456789,
        "check_in": date(2024, 6, 15),
        "check_out": date(2024, 6, 16),
        "tariff": Tariff.DAY,
        "duration_hours": 24,
        "bedroom": Bedroom.MAIN_BEDROOM,
        "is_sauna": True,
        "is_photoshoot": False,
        "count_people": 2,
        "total_price": 800,
        "name": "Test User",
        "phone": "+1234567890",
    }


@pytest.fixture
def sample_gift_certificate_data():
    """Sample gift certificate data for testing."""
    return {
        "user_id": 123456789,
        "chat_id": 123456789,
        "recipient_name": "John Doe",
        "recipient_phone": "+1234567890",
        "sender_name": "Jane Doe",
        "amount": 5000,
        "message": "Happy Birthday!",
    }
