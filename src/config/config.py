from dotenv import load_dotenv
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.secret_manager_service import SecretManagerService

secret_manager_service = SecretManagerService()

TELEGRAM_CONTACT = "https://t.me/the_secret_house"
PERIOD_IN_MONTHS = 6
MAX_PERIOD_FOR_GIFT_IN_MONTHS = 3
PREPAYMENT = 80
CLEANING_HOURS = 2
MIN_BOOKING_HOURS = 1

if "secrets-production" in os.environ:
    secrets = secret_manager_service.get_secret_by_dict("the-secret-house-secret")
    DEBUG = False
    TELEGRAM_TOKEN = secrets.get("TELEGRAM_TOKEN")
    LOGTAIL_TOKEN = secrets.get("LOGTAIL_TOKEN")
    LOGTAIL_SOURCE = secrets.get("LOGTAIL_SOURCE")
    DATABASE_URL = secrets.get("DATABASE_URL")
    ADMIN_CHAT_ID = int(secrets.get("ADMIN_CHAT_ID"))
    INFORM_CHAT_ID = int(secrets.get("INFORM_CHAT_ID"))
    GPT_KEY = secrets.get("GPT_KEY")
    GPT_PROMPT = secrets.get("GPT_PROMPT")
    CALENDAR_ID = secrets.get("CALENDAR_ID")
    BANK_CARD_NUMBER = secrets.get("BANK_CARD_NUMBER")
    BANK_PHONE_NUMBER = secrets.get("BANK_PHONE_NUMBER")
    ADMINISTRATION_CONTACT = secrets.get("ADMINISTRATION_CONTACT")
    GOOGLE_CREDENTIALS = secret_manager_service.get_secret("GOOGLE_CREDENTIALS")
    REDIS_URL = secret_manager_service.get_secret("REDIS_URL")
    REDIS_PORT = int(secret_manager_service.get_secret("REDIS_PORT"))
    REDIS_SSL = secret_manager_service.get_secret("REDIS_SSL").strip().lower() in ("true", "1", "yes", "on")
    SETTINGS_PATH = secret_manager_service.get_secret("SETTINGS_PATH")
else:
    # AMVERA deployment: When AMVERA=1, environment variables are set directly (no .env file)
    # DATABASE_URL format: postgresql://admin:password@host/database
    if os.environ.get("AMVERA") != "1":
        # Get config directory (where this file is located)
        config_dir = os.path.dirname(os.path.abspath(__file__))
        env_file_name = ".env.debug" if os.getenv("ENV") == "debug" else ".env.production"
        env_file_path = os.path.join(config_dir, env_file_name)
        print(f"[CONFIG] Loading environment from: {env_file_path}")
        print(f"[CONFIG] File exists: {os.path.exists(env_file_path)}")
        load_dotenv(env_file_path)
        print(f"[CONFIG] DATABASE_URL after load: {os.getenv('DATABASE_URL')}")

    DEBUG = os.getenv("DEBUG", "false").strip().lower() in ("true", "1", "yes", "on")
    GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    LOGTAIL_TOKEN = os.getenv("LOGTAIL_TOKEN", "")
    LOGTAIL_SOURCE = os.getenv("LOGTAIL_SOURCE", "")
    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL is None:
        raise ValueError(
            "DATABASE_URL is not set! Please check:\n"
            "1. ENV variable is set correctly (should be 'debug' or 'production')\n"
            "2. .env.debug or .env.production file exists in src/config/\n"
            "3. DATABASE_URL is defined in the .env file"
        )

    ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))
    INFORM_CHAT_ID = int(os.getenv("INFORM_CHAT_ID", "0"))
    GPT_KEY = os.getenv("GPT_KEY")
    GPT_PROMPT = os.getenv("GPT_PROMPT")
    CALENDAR_ID = os.getenv("CALENDAR_ID")
    BANK_CARD_NUMBER = os.getenv("BANK_CARD_NUMBER")
    BANK_PHONE_NUMBER = os.getenv("BANK_PHONE_NUMBER")
    ADMINISTRATION_CONTACT = os.getenv("ADMINISTRATION_CONTACT")
    REDIS_URL = os.getenv("REDIS_URL", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_SSL = os.getenv("REDIS_SSL", "false").strip().lower() in ("true", "1", "yes", "on")
    SETTINGS_PATH = os.getenv("SETTINGS_PATH", "data/settings.json")
