import sys
import os
import locale
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, InvalidCallbackData)
from src.jobs.reminders import run_reminder_jobs
from src.handlers import booking_handler, change_booking_date_handler, menu_handler, cancel_booking_handler, question_handler, price_handler, gift_certificate_handler, available_dates_handler 
from src.config import TELEGRAM_TOKEN

import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, Update,
                      InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler, filters)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(menu_handler.get_handler())
    application.run_polling(allowed_updates=Update.ALL_TYPES)

    locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")

if __name__ == '__main__':
    main()