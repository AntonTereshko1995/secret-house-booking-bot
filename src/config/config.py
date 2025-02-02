from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
TELEGRAM_CONTACT = "https://t.me/the_secret_house"
PERIOD_IN_MONTHS = 2
MAX_PERIOD_FOR_GIFT_IN_MONTHS = 3
MAX_PERIOD_FOR_SUBSCRIPTION_IN_MONTHS = 3
PREPAYMENT = 80
CLEANING_HOURS = 2