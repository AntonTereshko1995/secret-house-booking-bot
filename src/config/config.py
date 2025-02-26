from dotenv import load_dotenv
from google.cloud import secretmanager
import os

TELEGRAM_CONTACT = "https://t.me/the_secret_house"
PERIOD_IN_MONTHS = 2
MAX_PERIOD_FOR_GIFT_IN_MONTHS = 3
MAX_PERIOD_FOR_SUBSCRIPTION_IN_MONTHS = 3
PREPAYMENT = 80
CLEANING_HOURS = 2

# projects/535413863315/secrets/TELEGRAM_TOKEN
def get_secret_value():
    client = secretmanager.SecretManagerServiceClient()
    name = client.secret_path("the-secret-house", "the-secret-house-secret")
    response = client.get_secret(request={"name": name})
    # name = f"projects/the-secret-house/secrets/the-secret-house-secret/versions/latest"
    # response = client.access_secret_version(request={"name": name})
    secret_string = response.payload.data.decode("UTF-8")
    secret_dict = dict(line.split("=", 1) for line in secret_string.splitlines() if "=" in line)
    return secret_dict

if "secrets-production" in os.environ:
    secrets = get_secret_value()
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