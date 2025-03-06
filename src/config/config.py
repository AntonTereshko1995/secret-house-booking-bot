from dotenv import load_dotenv
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.secret_manager_service import SecretManagerService
from src.services.logger_service import LoggerService

secre_manager_service = SecretManagerService()

TELEGRAM_CONTACT = "https://t.me/the_secret_house"
PERIOD_IN_MONTHS = 2
MAX_PERIOD_FOR_GIFT_IN_MONTHS = 3
MAX_PERIOD_FOR_SUBSCRIPTION_IN_MONTHS = 3
PREPAYMENT = 80
CLEANING_HOURS = 2

if "secrets-production" in os.environ:
    secrets = secre_manager_service.get_secret_by_dict("the-secret-house-secret")
    DEBUG = False
    TELEGRAM_TOKEN = secrets.get("TELEGRAM_TOKEN")
    LOGTAIL_TOKEN = secrets.get("LOGTAIL_TOKEN")
    LOGTAIL_SOURCE = secrets.get("LOGTAIL_SOURCE")
    DATABASE_URL = secrets.get("DATABASE_URL")
    ADMIN_CHAT_ID = secrets.get("ADMIN_CHAT_ID")
    INFORM_CHAT_ID = secrets.get("INFORM_CHAT_ID")
    GPT_KEY = secrets.get("GPT_KEY")
    GPT_PROMPT = secrets.get("GPT_PROMPT")
    CALENDAR_ID = secrets.get("CALENDAR_ID")
    BANK_CARD_NUMBER = secrets.get("BANK_CARD_NUMBER")
    BANK_PHONE_NUMBER = secrets.get("BANK_PHONE_NUMBER")
    ADMINISTRATION_CONTACT = secrets.get("ADMINISTRATION_CONTACT")
    LoggerService.warning(__name__, f"Config {DATABASE_URL}")
else:
    file = "src/config/.env.debug" if os.getenv("ENV") == "debug" else "src/config/.env.production"
    load_dotenv(file)
    DEBUG = True
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    LOGTAIL_TOKEN = os.getenv("LOGTAIL_TOKEN")
    LOGTAIL_SOURCE = os.getenv("LOGTAIL_SOURCE")
    DATABASE_URL = os.getenv("DATABASE_URL")
    ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
    INFORM_CHAT_ID = os.getenv("INFORM_CHAT_ID")
    GPT_KEY = os.getenv("GPT_KEY")
    GPT_PROMPT = os.getenv("GPT_PROMPT")
    CALENDAR_ID = os.getenv("CALENDAR_ID")
    BANK_CARD_NUMBER = os.getenv("BANK_CARD_NUMBER")
    BANK_PHONE_NUMBER = os.getenv("BANK_PHONE_NUMBER")
    ADMINISTRATION_CONTACT = os.getenv("ADMINISTRATION_CONTACT")