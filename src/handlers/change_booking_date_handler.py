import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters)
from src.helpers import string_helper, date_time_helper
from src.constants import BACK, END, MENU, STOPPING, CHANGE_BOOKING_DATE, VALIDATE_USER, SET_OLD_START_DATE, SET_NEW_START_DATE

user_contact = ''
start_booking_date = datetime.date.min

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(enter_user_name, pattern=f"^{str(CHANGE_BOOKING_DATE)}$")],
        states={ 
            VALIDATE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_user_name)],
            SET_OLD_START_DATE: [CallbackQueryHandler(enter_old_start_date)], 
            SET_NEW_START_DATE: [CallbackQueryHandler(enter_new_start_date)], 
            BACK: [CallbackQueryHandler(back_navigation, pattern=f"^{str(BACK)}$")],
            },
        fallbacks=[CallbackQueryHandler(back_navigation, pattern=f"^{str(END)}$")],
        map_to_parent={
            # Return to top level menu
            END: MENU,
            # End conversation altogether
            STOPPING: END,
        })
    return handler

async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler.show_menu(update, context)
    return END

async def enter_user_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=str(END))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Напишите Ваш <b>Telegram</b>.\n"
        "Формат ввода @user_name (обязательно начинайте ввод с @).\n"
        "Формат ввода номера телефона +375251111111 (обязательно начинайте ввод с +375).\n",
        reply_markup=reply_markup)
    return VALIDATE_USER

async def enter_old_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")

async def enter_new_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")

async def enter_new_finish_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")

async def finish_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")