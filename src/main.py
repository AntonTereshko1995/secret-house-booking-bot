import sys
import os
import threading
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters)
from src.jobs.reminders import run_reminder_jobs
from src.handlers import booking_handler, change_booking_date_handler, start_handler, cancel_booking_handler, question_handler, price_handler, gift_certificate_handler, contact_handler, available_dates_handler 
from src.config import TELEGRAM_TOKEN
from src.constants import Handler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    dispatcher = Application.builder().token(TELEGRAM_TOKEN).build() 

#     dispatcher.add_handler(CommandHandler(Handler.START, start_handler.handle))
#     dispatcher.add_handler(CommandHandler(Handler.BOOKING, booking_handler.handle))
#     dispatcher.add_handler(CommandHandler(Handler.CANCEL_BOOKING, cancel_booking_handler.handle))
#     dispatcher.add_handler(CommandHandler(Handler.CHANGE_BOOKING_DATE, change_booking_date_handler.handle))
#     dispatcher.add_handler(CommandHandler(Handler.AVAILABLE_DATES, available_dates_handler.handle))
#     dispatcher.add_handler(CommandHandler(Handler.QUESTION, question_handler.handle))
#     dispatcher.add_handler(CommandHandler(Handler.PRICE, price_handler.handle))
#     dispatcher.add_handler(CommandHandler(Handler.GIFT_CERTIFICATE, gift_certificate_handler.handle))
#     dispatcher.add_handler(CommandHandler(Handler.CONTACT, contact_handler.handle))

    # Регистрация хэндлеров
    dispatcher.add_handler(CommandHandler("start", start_handler.handle))
    dispatcher.add_handler(CommandHandler("booking", booking_handler.handle))
    dispatcher.add_handler(CommandHandler("cancel_booking", cancel_booking_handler.handle))
    dispatcher.add_handler(CommandHandler("cancel_booking", change_booking_date_handler.handle))
    dispatcher.add_handler(CommandHandler("available_dates", available_dates_handler.handle))
    dispatcher.add_handler(CommandHandler("question", question_handler.handle))
    dispatcher.add_handler(CommandHandler("price", price_handler.handle))
    dispatcher.add_handler(CommandHandler("gift_certificate", gift_certificate_handler.handle))
    dispatcher.add_handler(CommandHandler("contact", contact_handler.handle))

    # Запуск бота
    dispatcher.run_polling()

    # start job
    # reminder_thread = threading.Thread(target=run_reminder_jobs, daemon=True)
    # reminder_thread.start()

if __name__ == "__main__":
    main()