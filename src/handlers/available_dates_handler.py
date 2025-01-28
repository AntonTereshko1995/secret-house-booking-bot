import calendar
from datetime import date, datetime, timedelta
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.database_service import DatabaseService
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CallbackQueryHandler, CallbackContext)
from src.handlers import menu_handler
from src.helpers import date_time_helper
from src.config.config import CLEANING_HOURS
from src.constants import END, MENU, AVAILABLE_DATES, STOPPING, GET_AVAILABLE_DATES, BACK
from src.config.config import PERIOD_IN_MONTHS

database_service = DatabaseService()

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_month, pattern=f"^{str(AVAILABLE_DATES)}$")],
        states={ 
            GET_AVAILABLE_DATES: [CallbackQueryHandler(get_available_dates)], 
            BACK: [CallbackQueryHandler(select_month, pattern=f"^{BACK}$")], 
            },
        fallbacks=[CallbackQueryHandler(back_navigation, pattern=f"^{END}$")],
        map_to_parent={
            END: MENU,
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
    month, year = parse_callback_data(update)

    keyboard = [
        [InlineKeyboardButton("Выбрать другой месяц", callback_data=BACK)],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    from_date, to_date, booking = get_booking(month, year)
    available_date_message = generate_available_slots(booking, from_date, to_date)

    await update.callback_query.edit_message_text(
        text=f"📅 Доступные даты и время на {date_time_helper.get_month_name(month)}:\n\n"
            f"{available_date_message}",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return BACK

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
    to_date = datetime(day=calendar.monthrange(year, month)[1], month=month, year=year, hour=0) + timedelta(days=1)
    booking = database_service.get_booking_by_period(from_date.date(), to_date.date())
    return (from_date, to_date, booking)

def generate_available_slots(bookings, from_datetime, to_datetime, cleaning_time=timedelta(hours=CLEANING_HOURS), time_step=timedelta(hours=1)):
    if (len(bookings) == 0):
        return "Весь месяц свободен."

    all_slots = []
    current_time = from_datetime

    while current_time < to_datetime:
        all_slots.append(current_time)
        current_time += time_step

    extended_busy_slots = [
        {"start": booking.start_date - cleaning_time, "end": booking.end_date + cleaning_time}
        for booking in bookings
    ]

    available_slots = [
        slot for slot in all_slots
        if all(not (busy["start"] <= slot < busy["end"]) for busy in extended_busy_slots)]

    grouped_slots = {}
    for slot in available_slots:
        date_str = slot.strftime("%Y-%m-%d")
        if date_str not in grouped_slots:
            grouped_slots[date_str] = []
        grouped_slots[date_str].append(slot)

    message = ""
    for date, times in grouped_slots.items():
        time_ranges = []
        start_time = times[0]

        for i in range(1, len(times)):
            if (times[i] - times[i - 1]) > time_step:
                end_time = times[i - 1]
                if start_time == end_time:
                    time_ranges.append(start_time.strftime("%H:%M"))
                else:
                    time_ranges.append(f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}")
                start_time = times[i]

        end_time = times[-1]
        if start_time == end_time:
            time_ranges.append(start_time.strftime("%H:%M"))
        else:
            time_ranges.append(f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}")

        message += f"📍 <b>{date}</b>\n{', '.join(time_ranges)}\n\n"

    return message
    