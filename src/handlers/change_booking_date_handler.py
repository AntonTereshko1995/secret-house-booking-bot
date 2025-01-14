import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, CallbackContext)
from src.handlers import start_handler

USER_NAME, OLD_START_DATE, NEW_START_DATE, NEW_FINISH_DATE, END = map(chr, range(0, 4))

def get_handler() -> ConversationHandler:
    menu_handler = ConversationHandler(
        entry_points=[CommandHandler('change_booking_date', enter_user)],
        states={ 
            USER_NAME: [CallbackQueryHandler(enter_user)],
            OLD_START_DATE: [CallbackQueryHandler(enter_old_start_date)], 
            NEW_START_DATE: [CallbackQueryHandler(enter_new_start_date)], 
            NEW_FINISH_DATE: [CallbackQueryHandler(enter_new_finish_date)], 
            END: [CallbackQueryHandler(finish_message)] 
            },
        fallbacks=[CommandHandler('cancel', start_handler.show_menu)])
    return menu_handler

async def enter_user(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")

async def enter_old_start_date(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")

async def enter_new_start_date(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")

async def enter_new_finish_date(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")

async def finish_message(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")