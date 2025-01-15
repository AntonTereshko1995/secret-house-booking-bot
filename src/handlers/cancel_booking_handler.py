import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, CallbackContext)
from src.handlers import start_handler

USER_NAME, START_DATE, END = map(chr, range(0, 3))

def get_handler() -> ConversationHandler:
    menu_handler = ConversationHandler(
        entry_points=[CommandHandler('cancel_booking', enter_user)],
        states={ 
            USER_NAME: [CallbackQueryHandler(enter_user)],
            START_DATE: [CallbackQueryHandler(enter_start_date)], 
            END: [CallbackQueryHandler(finish_message)] 
            },
        fallbacks=[CommandHandler('cancel', start_handler.show_menu)])
    return menu_handler

async def call_from_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await enter_user(update, context)

async def enter_user(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")

async def enter_start_date(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")

async def finish_message(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")