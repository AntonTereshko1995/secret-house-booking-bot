import calendar
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.logger_service import LoggerService
from src.services.database_service import DatabaseService
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, CallbackQueryHandler, CallbackContext)
from src.handlers import menu_handler
from src.helpers import date_time_helper, string_helper
from src.constants import END, MENU, AVAILABLE_DATES, BACK
from src.config.config import PERIOD_IN_MONTHS

database_service = DatabaseService()

def get_handler():
    return [
        CallbackQueryHandler(get_available_dates, pattern=f"^month_(\d+)_(\d+)$"),
        CallbackQueryHandler(select_month, pattern=f"^{BACK}$",),
        CallbackQueryHandler(back_navigation, pattern=f"^{END}$")
    ]

async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler.show_menu(update, context)
    LoggerService.info(__name__, f"Back to menu", update)
    return MENU

async def select_month(update: Update, context: CallbackContext):
    LoggerService.info(__name__, f"Select month", update)
    months = date_time_helper.get_future_months(PERIOD_IN_MONTHS) 
    keyboard = [[InlineKeyboardButton(text=value, callback_data=f"month_{str(key)}")] for key, value in months.items()]
    keyboard.append([InlineKeyboardButton("Назад в меню", callback_data=END)])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="📅 <b>Выберите доступный месяц для бронирования.</b>",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return AVAILABLE_DATES 

async def get_available_dates(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    if (update.callback_query.data == str(END)):
        return await back_navigation(update, context)

    month, year = parse_callback_data(update)
    LoggerService.info(__name__, f"Available dates", update)
    keyboard = [
        [InlineKeyboardButton("Выбрать другой месяц", callback_data=BACK)],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    from_date, to_date, booking = get_booking(month, year)
    available_date_message = string_helper.generate_available_slots(booking, from_date, to_date)

    await update.callback_query.edit_message_text(
        text=f"📅 Доступные даты и время на {date_time_helper.get_month_name(month)}:\n\n"
            f"{available_date_message}",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return AVAILABLE_DATES

def parse_callback_data(update: Update):
    data = update.callback_query.data
    _, year_str, month_str = data.split("_")
    year = int(year_str)
    month = int(month_str)
    return (month, year)

def get_booking(month, year):
    today = datetime.today()
    if today.month == month and today.year == year:
        from_date = datetime(day=today.day, month=month, year=year, hour=0)
    else:
        from_date = datetime(day=1, month=month, year=year, hour=0)
    to_date = datetime(day=calendar.monthrange(year, month)[1], month=month, year=year, hour=23, minute=59) + timedelta(days=1)
    booking = database_service.get_booking_by_period(from_date.date(), to_date.date())
    return (from_date, to_date, booking)