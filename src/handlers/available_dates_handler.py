import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CallbackQueryHandler, CallbackContext)
from src.handlers import menu_handler
from src.helpers import date_time_helper, string_helper
from src.constants import END, MENU, AVAILABLE_DATES, STOPPING, GET_AVAILABLE_DATES, BACK
from src.config.config import PERIOD_IN_MONTHS

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_month, pattern=f"^{str(AVAILABLE_DATES)}$")],
        states={ 
            GET_AVAILABLE_DATES: [CallbackQueryHandler(get_available_dates, pattern="^month_\d+$")], 
            BACK: [CallbackQueryHandler(select_month, pattern=f"^{BACK}$")], 
            },
        fallbacks=[CallbackQueryHandler(back_navigation, pattern=f"^{END}$")],
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

async def select_month(update: Update, context: CallbackContext):
    months = date_time_helper.get_future_months(PERIOD_IN_MONTHS) 
    keyboard = [[InlineKeyboardButton(text=value, callback_data=f"month_{str(key)}")] for key, value in months.items()]
    keyboard.append([InlineKeyboardButton("Назад в меню", callback_data=END)])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Выберете доступный месяц для бронирования.",
        reply_markup=reply_markup)
    return GET_AVAILABLE_DATES

async def get_available_dates(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    data = update.callback_query.data
    month = string_helper.extract_data(data)
    month_name = date_time_helper.get_month_name(month)

    keyboard = [
        [InlineKeyboardButton("Выбрать другой месяц", callback_data=BACK)],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(f"Свободные даты на {month_name}")
    await update.callback_query.edit_message_text(
        text=f"Свободные даты на {month_name}",
        reply_markup=reply_markup)
    return BACK