from dotenv import load_dotenv
from google.cloud import secretmanager
import os

TELEGRAM_CONTACT = "https://t.me/the_secret_house"
PERIOD_IN_MONTHS = 2
MAX_PERIOD_FOR_GIFT_IN_MONTHS = 3
MAX_PERIOD_FOR_SUBSCRIPTION_IN_MONTHS = 3
PREPAYMENT = 80
CLEANING_HOURS = 2

def get_secret(project_id: str) -> secretmanager.GetSecretRequest:
    client = secretmanager.SecretManagerServiceClient()
    name = client.secret_path(project_id, "the-secret-house")
    response = client.get_secret(request={"name": name})
    return response.payload.data.decode("UTF-8")

if "secrets-production" in os.environ:
    TELEGRAM_TOKEN = get_secret("TELEGRAM_TOKEN")
    LOGTAIL_TOKEN = get_secret("LOGTAIL_TOKEN")
    LOGTAIL_SOURCE = get_secret("LOGTAIL_SOURCE")
    DATABASE_URL = get_secret("DATABASE_URL")
    ADMIN_CHAT_ID = get_secret("ADMIN_CHAT_ID")
    INFORM_CHAT_ID = get_secret("INFORM_CHAT_ID")
    GPT_KEY = get_secret("GPT_KEY")
    GPT_PROMPT = get_secret("GPT_PROMPT")
    CALENDAR_ID = get_secret("CALENDAR_ID")
    BANK_CARD_NUMBER = get_secret("BANK_CARD_NUMBER")
    BANK_PHONE_NUMBER = get_secret("BANK_PHONE_NUMBER")
    ADMINISTRATION_CONTACT = get_secret("ADMINISTRATION_CONTACT")
else:
    file = "src/config/.env.debug" if os.getenv("ENV") == "debug" else "src/config/.env.production"
    load_dotenv(file)
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