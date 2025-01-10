from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
# DATABASE_URL = os.getenv("DATABASE_URL")
# LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")