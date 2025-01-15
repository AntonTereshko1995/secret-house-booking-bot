import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, CallbackContext)
from src.handlers import start_handler

END = 1

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CommandHandler('available_dates', send_dates)],
        states={ 
            # USER_NAME: [CallbackQueryHandler(enter_user)],
            # START_DATE: [CallbackQueryHandler(enter_start_date)], 
            # END: [CallbackQueryHandler(finish_message)] 
            },
        fallbacks=[CommandHandler('cancel', start_handler.show_menu)])
    return handler

async def send_dates(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")

async def finish_message(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")