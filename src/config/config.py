from dotenv import load_dotenv
import os

if "secrets-production" in os.environ:
    pass
    # with open("projects/535413863315/secrets/the-secret-house-secret/versions/2/the-secret-house-secret") as f:
    #     load_dotenv(stream=f)
else:
    ENV_FILE = "src/config/.env.debug" if os.getenv("ENV") == "debug" else "src/config/.env.production"
    load_dotenv(ENV_FILE)

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
TELEGRAM_CONTACT = "https://t.me/the_secret_house"
PERIOD_IN_MONTHS = 2
MAX_PERIOD_FOR_GIFT_IN_MONTHS = 3
MAX_PERIOD_FOR_SUBSCRIPTION_IN_MONTHS = 3
PREPAYMENT = 80
CLEANING_HOURS = 2