"""
Telegram Bot Configuration
Minimal configuration - all business logic handled by backend API
"""
from dotenv import load_dotenv
import os

# Load environment variables
file = (
    "src/config/.env.debug"
    if os.getenv("ENV") == "debug"
    else "src/config/.env.production"
)
if os.path.exists(file):
    load_dotenv(file)

# Telegram Bot Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
# Allow missing token in test environment
if not TELEGRAM_TOKEN and os.getenv("ENV") not in ("test", "pytest"):
    raise ValueError("TELEGRAM_TOKEN must be set in environment variables")

# Backend API Configuration
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY", "dev-api-key-12345")

# Admin Configuration
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))
INFORM_CHAT_ID = int(os.getenv("INFORM_CHAT_ID", "0"))

# Redis Configuration (for bot conversation state only)
REDIS_URL = os.getenv("REDIS_URL", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_SSL = os.getenv("REDIS_SSL", "0") == "1"

# Debug mode
DEBUG = os.getenv("DEBUG", "true").strip().lower() in ("true", "1", "yes", "on")

# Telegram Contact (for user messages)
TELEGRAM_CONTACT = "https://t.me/the_secret_house"

# Logging Configuration
LOGTAIL_TOKEN = os.getenv("LOGTAIL_TOKEN", "")
LOGTAIL_SOURCE = os.getenv("LOGTAIL_SOURCE", "")

# Payment Configuration
BANK_CARD_NUMBER = os.getenv("BANK_CARD_NUMBER", "")
BANK_PHONE_NUMBER = os.getenv("BANK_PHONE_NUMBER", "")

# Administration Contact
ADMINISTRATION_CONTACT = os.getenv("ADMINISTRATION_CONTACT", "")

# Settings
SETTINGS_PATH = os.getenv("SETTINGS_PATH", "data/settings.json")

# Booking Configuration
MIN_BOOKING_HOURS = int(os.getenv("MIN_BOOKING_HOURS", "4"))
PERIOD_IN_MONTHS = int(os.getenv("PERIOD_IN_MONTHS", "3"))
PREPAYMENT = int(os.getenv("PREPAYMENT", "30"))
CLEANING_HOURS = int(os.getenv("CLEANING_HOURS", "2"))
