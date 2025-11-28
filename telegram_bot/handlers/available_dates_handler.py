import calendar
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from telegram_bot.client.backend_api import BackendAPIClient, APIError
from telegram_bot.services.navigation_service import NavigationService
from telegram_bot.services.logger_service import LoggerService
from telegram_bot.decorators.callback_error_handler import safe_callback_query
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CallbackContext
from telegram_bot.handlers import menu_handler
from telegram_bot.helpers import date_time_helper, string_helper
from telegram_bot.constants import END, MENU, AVAILABLE_DATES, BACK
from telegram_bot.config.config import PERIOD_IN_MONTHS
import logging

logger = logging.getLogger(__name__)
navigation_service = NavigationService()


def get_handler():
    return [
        CallbackQueryHandler(get_available_dates, pattern="^month_(\d+)_(\d+)$"),
        CallbackQueryHandler(
            select_month,
            pattern=f"^{BACK}$",
        ),
        CallbackQueryHandler(back_navigation, pattern=f"^{END}$"),
    ]


@safe_callback_query()
async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler.show_menu(update, context)
    LoggerService.info(__name__, "Back to menu", update)
    return MENU


async def select_month(update: Update, context: CallbackContext):
    LoggerService.info(__name__, "Available months", update)
    months = date_time_helper.get_future_months(PERIOD_IN_MONTHS)
    keyboard = [
        [InlineKeyboardButton(text=value, callback_data=f"month_{str(key)}")]
        for key, value in months.items()
    ]
    keyboard.append([InlineKeyboardButton("Назад в меню", callback_data=END)])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="📅 <b>Выберите доступный месяц для бронирования.</b>",
        reply_markup=reply_markup,
    )
    return AVAILABLE_DATES


async def get_available_dates(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    if update.callback_query.data == str(END):
        return await back_navigation(update, context)

    month, year = parse_callback_data(update)
    LoggerService.info(__name__, "Select month", update, kwargs={"month": month})
    keyboard = [
        [InlineKeyboardButton("Выбрать другой месяц", callback_data=BACK)],
        [InlineKeyboardButton("Назад в меню", callback_data=END)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        from_date, to_date, booking = await get_booking(month, year)
        available_date_message = string_helper.generate_available_slots(
            booking, from_date, to_date
        )

        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=f"📅 Доступные даты и время на {date_time_helper.get_month_name(month)}:\n\n"
            f"{available_date_message}",
            reply_markup=reply_markup,
        )
    except APIError as e:
        logger.error(f"Failed to fetch bookings from API: {e}")
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text="Извините, произошла ошибка при получении доступных дат. Пожалуйста, попробуйте позже.",
            reply_markup=reply_markup,
        )

    return AVAILABLE_DATES


def parse_callback_data(update: Update):
    data = update.callback_query.data
    _, year_str, month_str = data.split("_")
    year = int(year_str)
    month = int(month_str)
    return (month, year)


async def get_booking(month, year):
    api_client = BackendAPIClient()

    today = datetime.today()
    if today.month == month and today.year == year:
        from_date = datetime(day=today.day, month=month, year=year, hour=0)
    else:
        from_date = datetime(day=1, month=month, year=year, hour=0)
    to_date = datetime(
        day=calendar.monthrange(year, month)[1],
        month=month,
        year=year,
        hour=23,
        minute=59,
    ) + timedelta(days=1)

    # Get bookings for the date range via API
    booking = await api_client.get_bookings_by_date_range(
        from_date.date().isoformat(),
        to_date.date().isoformat()
    )
    return (from_date, to_date, booking)
