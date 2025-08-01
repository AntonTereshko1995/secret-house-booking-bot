import sys
import os

from src.services.navigation_service import NavigatonService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.logger_service import LoggerService
from src.models.enum.tariff import Tariff
from src.services.calendar_service import CalendarService
from src.models.rental_price import RentalPrice
from src.services.calculation_rate_service import CalculationRateService
from db.models.booking import BookingBase
from src.services.database_service import DatabaseService
from datetime import datetime, date, time, timedelta
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters)
from src.handlers import admin_handler, menu_handler
from src.helpers import date_time_helper, string_helper, tariff_helper
from src.date_time_picker import calendar_picker, hours_picker
from src.config.config import MIN_BOOKING_HOURS, PERIOD_IN_MONTHS, CLEANING_HOURS
from dateutil.relativedelta import relativedelta
from typing import Optional
from src.constants import (
    CHANGE_BOOKING_DATE_VALIDATE_USER, 
    END,
    MENU, 
    CHANGE_BOOKING_DATE, 
    CONFIRM)

database_service = DatabaseService()
calculation_rate_service = CalculationRateService()
calendar_service = CalendarService()
navigation_service = NavigatonService()

user_contact = ''
old_booking_date = date.today()
start_booking_date = datetime.today()
finish_booking_date = datetime.today()
max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
min_date_booking = date.today() - relativedelta(day=1)
booking: BookingBase = None
rental_price: RentalPrice = None
selected_bookings = []

def get_handler():
    return [
        CallbackQueryHandler(choose_booking, pattern=f"^CHANGE-BOOKING_(\d+|{END})$"),
        CallbackQueryHandler(enter_start_date, pattern=f"^CALENDAR-CALLBACK-START_(.+|{END})$"),
        CallbackQueryHandler(enter_start_time, pattern=f"^HOURS-CALLBACK-START_(.+|{END})$"),
        CallbackQueryHandler(enter_finish_date, pattern=f"^CALENDAR-CALLBACK-FINISH_(.+|{END})$"),
        CallbackQueryHandler(enter_finish_time, pattern=f"^HOURS-CALLBACK-FINISH_(.+|{END})$"),
        CallbackQueryHandler(confirm_booking, pattern=f"^CHANGE-CONFIRM_({CONFIRM}|{END})$"),
        CallbackQueryHandler(back_navigation, pattern=f"^{END}$"),
    ]

async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler.show_menu(update, context)
    LoggerService.info(__name__, f"Back to menu", update)
    return MENU

async def enter_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_variables()
    LoggerService.info(__name__, f"Enter user contact", update)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await safe_edit_message_text(
        callback_query=update.callback_query,
        text="📲 Укажите ваш <b>Telegram</b> или номер телефона:\n\n"
            "🔹 <b>Telegram:</b> @username (начинайте с @)\n"
            "🔹 <b>Телефон:</b> +375XXXXXXXXX (обязательно с +375)\n"
            "❗️ Пожалуйста, вводите данные строго в указанном формате.",
        reply_markup=reply_markup)
    return CHANGE_BOOKING_DATE_VALIDATE_USER

async def check_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user_input = update.message.text
        is_valid = string_helper.is_valid_user_contact(user_input)
        if is_valid:
            global user_contact
            user_contact = user_input
            return await choose_booking_message(update, context)
        else:
            LoggerService.warning(__name__, "User name is invalid", update)
            await update.message.reply_text(
                "❌ <b>Ошибка!</b>\n"
                "Имя пользователя в Telegram или номер телефона введены некорректно.\n\n"
                "🔄 Пожалуйста, попробуйте еще раз.")

    return CHANGE_BOOKING_DATE_VALIDATE_USER

async def choose_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if (data == str(END)):
        return await back_navigation(update, context)

    global booking, old_booking_date
    booking = next((b for b in selected_bookings if str(b.id) == data), None)

    if booking.is_date_changed:
        error_message = ("❌ <b>Ошибка!</b>\n\n"
            "⏳ <b>Вы превысили лимит переносов бронирования.</b>\n"
            "🔄 Пожалуйста, обратитесь к администратору для решения этой проблемы.")
        LoggerService.warning(__name__, f"reschedule count is more than 1", update)
        return await choose_booking_message(update, context, error_message=error_message)

    LoggerService.info(__name__, "Choose booking", update)
    old_booking_date = booking.start_date
    return await start_date_message(update, context)

async def enter_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = date.today()
    selected, selected_date, is_action = await calendar_picker.process_calendar_selection(update, context, min_date=min_date_booking, max_date=max_date_booking, action_text="Назад в меню", callback_prefix="-START")
    if selected:
        if not tariff_helper.is_booking_available(booking.tariff, selected_date):
            LoggerService.warning(__name__, f"start date is incorrect for {booking.tariff}", update)
            error_message = ("❌ <b>Ошибка!</b>\n\n"
                "⏳ <b>Тариф 'Рабочий' доступен только с понедельника по четверг.</b>\n"
                "🔄 Пожалуйста, выберите новую дату начала бронирования.")
            LoggerService.warning(__name__, f"there are bookings between the selected dates", update)
            return await start_date_message(update, context, error_message=error_message)

        global start_booking_date
        start_booking_date = selected_date
        LoggerService.info(__name__, f"select start date", update, kwargs={'start_date': start_booking_date.date()})
        return await start_time_message(update, context)
    elif is_action:
        LoggerService.info(__name__, f"select start date", update, kwargs={'start_date': 'cancel'})
        return await back_navigation(update, context)
    return CHANGE_BOOKING_DATE

async def enter_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    selected, time, is_action = await hours_picker.process_hours_selection(update, context)
    if selected:
        global start_booking_date
        start_booking_date = start_booking_date.replace(hour=time.hour, minute=time.minute)
        LoggerService.info(__name__, f"select start time", update, kwargs={'start_time': start_booking_date.time()})
        return await finish_date_message(update, context)
    elif is_action:
        LoggerService.info(__name__, f"select start time", update, kwargs={'start_time': 'back'})
        return await start_date_message(update, context)
    return CHANGE_BOOKING_DATE

async def enter_finish_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = (start_booking_date + timedelta(hours=MIN_BOOKING_HOURS)).date()
    selected, selected_date, is_action = await calendar_picker.process_calendar_selection(update, context, min_date=min_date_booking, max_date=max_date_booking, action_text="Назад в меню", callback_prefix="-FINISH")
    if selected:
        global finish_booking_date
        finish_booking_date = selected_date
        LoggerService.info(__name__, f"select finish date", update, kwargs={'finish_date': finish_booking_date.date()})
        return await finish_time_message(update, context)
    elif is_action:
        LoggerService.info(__name__, f"select finish date", update, kwargs={'finish_date': 'back'})
        return await start_time_message(update, context)
    return CHANGE_BOOKING_DATE

async def enter_finish_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    selected, time, is_action = await hours_picker.process_hours_selection(update, context)
    if selected:
        global finish_booking_date
        finish_booking_date = finish_booking_date.replace(hour=time.hour)
        LoggerService.info(__name__, f"select finish time", update, kwargs={'finish_time': finish_booking_date.time()})
        created_bookings = database_service.get_booking_by_period(start_booking_date, finish_booking_date)

        if booking.tariff == Tariff.WORKER and tariff_helper.is_interval_in_allowed_ranges(start_booking_date.time(), finish_booking_date.time()) == False:
            error_message = ("❌ <b>Ошибка!</b>\n\n"
                "⏳ <b>Выбранные дата и время не соответствуют условиям тарифа 'Рабочий'.</b>\n"
                "⚠️ В рамках этого тарифа бронирование возможно только с 11:00 до 20:00 или с 22:00 до 9:00.\n\n"
                "🔄 Пожалуйста, выберите другое время начала бронирования.\n\n"
                "ℹ️ Если вы планируете забронировать в другое время — выберите, пожалуйста, тариф '12 часов', 'Суточно' или 'Инкогнито'.")
            LoggerService.warning(__name__, f"incorect time for tariff Worker", update)
            return await start_date_message(update, context, error_message=error_message)

        is_any_booking = any(b.id != booking.id for b in created_bookings)
        if is_any_booking:
            error_message = ("❌ <b>Ошибка!</b>\n\n"
                "⏳ <b>Выбранные дата и время недоступны.</b>\n"
                "⚠️ Дата начала и конца бронирования пересекается с другим бронированием.\n\n"
                f"🧹 После каждого клиента нам нужно подготовить дом. Уборка занимает <b>{CLEANING_HOURS} часа</b>.\n\n"
                "🔄 Пожалуйста, выберите новую дату начала бронирования.")
            LoggerService.info(__name__, f"there are bookings between the selected dates", update)
            return await start_date_message(update, context, error_message=error_message)
        
        selected_duration = finish_booking_date - start_booking_date
        duration_booking_hours = date_time_helper.seconds_to_hours(selected_duration.total_seconds())
        global rental_price
        rental_price = calculation_rate_service.get_tariff(booking.tariff)
        booking_duration_hours = max((booking.end_date - booking.start_date).total_seconds() / 3600, rental_price.duration_hours);
        if duration_booking_hours > booking_duration_hours:
            error_message = ("❌ <b>Ошибка!</b>\n\n"
                "⏳ <b>Максимальная продолжительность тарифа превышена.</b>\n"
                f"🕒 Длительность <b>{rental_price.name}</b>: {rental_price.duration_hours} ч.\n\n"
                "🔄 Пожалуйста, повторите попытку и выберите доступный вариант.\n\n"
                "📅 Выберите новую дату начала бронирования.")
            return await start_date_message(update, context, error_message=error_message)

        return await confirm_message(update, context)
    elif is_action:
        LoggerService.info(__name__, f"select finish time", update, kwargs={'finish_time': "back"})
        return await finish_date_message(update, context)
    return CHANGE_BOOKING_DATE

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if (data == str(END)):
        return await back_navigation(update, context)

    LoggerService.info(__name__, f"Confirm booking", update)
    updated_booking = database_service.update_booking(booking.id, start_date=start_booking_date, end_date=finish_booking_date, is_date_changed=True)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await admin_handler.inform_changing_booking_date(update, context, updated_booking, old_booking_date)
    calendar_service.move_event(updated_booking.calendar_event_id, start_booking_date, finish_booking_date)
    await safe_edit_message_text(
        callback_query=update.callback_query,
        text=f"✅ <b>Бронирование успешно перенесено!</b>\n\n"
            f"📅 <b>С:</b> {start_booking_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"📅 <b>До:</b> {finish_booking_date.strftime('%d.%m.%Y %H:%M')}.\n",
        reply_markup=reply_markup)

async def choose_booking_message(update: Update, context: ContextTypes.DEFAULT_TYPE, error_message: Optional[str] = None):
    global selected_bookings
    booking_list = database_service.get_booking_by_user_contact(user_contact)
    selected_bookings = list(filter(lambda x: x.start_date.date() >= date.today(), booking_list))
    
    if not selected_bookings or len(selected_bookings) == 0:
        return await warning_message(update, context)
    
    keyboard = []
    for booking in selected_bookings:
        keyboard.append([InlineKeyboardButton(f"{booking.start_date.strftime('%d.%m.%Y %H:%M')} - {booking.end_date.strftime('%d.%m.%Y %H:%M')}", 
                                              callback_data=f"CHANGE-BOOKING_{booking.id}")])

    keyboard.append([InlineKeyboardButton("Назад в меню", callback_data=END)])
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "📅 <b>Выберите бронирование, которое хотите изменить.</b>\n"
    if error_message:
        message = message + "\n\n" + error_message

    if update.message == None:
        await update.callback_query.answer()
        await safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
            reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup)

    return CHANGE_BOOKING_DATE

async def start_date_message(update: Update, context: ContextTypes.DEFAULT_TYPE, error_message: Optional[str] = None):
    today = date.today()
    max_date_booking = today + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = today
 
    if error_message:
        message = error_message
    else:
        message = ("✅ <b>Ваше бронирование найдено!</b>\n\n"
            "📅 <b>Введите новую дату, на которую хотите перенести бронирование.</b>")
        
    await safe_edit_message_text(
        callback_query=update.callback_query,
        text=message, 
        reply_markup=calendar_picker.create_calendar(today, min_date=min_date_booking, max_date=max_date_booking, action_text="Назад в меню", callback_prefix="-START"))
    return CHANGE_BOOKING_DATE

async def start_time_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feature_booking = database_service.get_booking_by_day(start_booking_date.date(), booking.id)
    available_slots = date_time_helper.get_free_time_slots(feature_booking, start_booking_date.date(), minus_time_from_start=True, add_time_to_end=True)
    message = ("⏳ <b>Выберите время начала бронирования.</b>\n"
        f"Вы выбрали дату заезда: {start_booking_date.strftime('%d.%m.%Y')}.\n"
        "Теперь укажите удобное время заезда.\n")
    if booking.tariff == Tariff.WORKER:
        message += (
            "\n📌 <b>Для тарифа 'Рабочий' доступны интервалы:</b>\n"
            "🕚 11:00 – 20:00\n"
            "🌙 22:00 – 09:00")
    await safe_edit_message_text(
        callback_query=update.callback_query,
        text=message, 
        reply_markup = hours_picker.create_hours_picker(action_text="Назад", free_slots=available_slots, date=start_booking_date.date(), callback_prefix="-START"))
    return CHANGE_BOOKING_DATE

async def finish_date_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = date.today()
    max_date_booking = today + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = (start_booking_date + timedelta(hours=MIN_BOOKING_HOURS)).date()
    await safe_edit_message_text(
        callback_query=update.callback_query,
        text="📅 <b>Выберите дату завершения бронирования.</b>\n"
            f"Вы выбрали дату и время заезда: {start_booking_date.strftime('%d.%m.%Y %H:%M')}.\n"
            "Теперь укажите день, когда планируете выехать.\n"
            "📌 Выезд должен быть позже времени заезда.", 
        reply_markup=calendar_picker.create_calendar(min_date_booking, min_date=min_date_booking, max_date=max_date_booking, action_text="Назад", callback_prefix="-FINISH"))
    return CHANGE_BOOKING_DATE

async def finish_time_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feature_booking = database_service.get_booking_by_day(finish_booking_date.date(), booking.id)
    start_time = time(0, 0) if start_booking_date.date() != finish_booking_date.date() else (start_booking_date + timedelta(hours=MIN_BOOKING_HOURS)).time()
    available_slots = date_time_helper.get_free_time_slots(feature_booking, finish_booking_date.date(), start_time=start_time, minus_time_from_start=True, add_time_to_end=True)
    await safe_edit_message_text(
        callback_query=update.callback_query,
        text="⏳ <b>Выберите времня завершения бронирования.</b>\n"
            f"Вы выбрали заезд: {start_booking_date.strftime('%d.%m.%Y %H:%M')}.\n"
            f"Вы выбрали дату выезда: {finish_booking_date.strftime('%d.%m.%Y')}.\n"
            "Теперь укажите время, когда хотите освободить дом.\n\n"
            "📌 Обратите внимание:\n"
            "🔹 Выезд должен быть позже времени заезда.\n"
            f"🔹 После каждого бронирования требуется {CLEANING_HOURS} часа на уборку.\n", 
        reply_markup=hours_picker.create_hours_picker(action_text="Назад", free_slots=available_slots, date=finish_booking_date.date(), callback_prefix="-FINISH"))
    return CHANGE_BOOKING_DATE

async def confirm_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Подтвердить", callback_data=f"CHANGE-CONFIRM_{CONFIRM}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"CHANGE-CONFIRM_{END}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await safe_edit_message_text(
        callback_query=update.callback_query,
        text = (f"📅 Подтвердите изменение даты бронирования:\n"
            f"🔹 <b>С</b> {old_booking_date.strftime('%d.%m.%Y')} \n"
            f"🔹 <b>На</b> {start_booking_date.strftime('%d.%m.%Y %H:%M')} "
            f"до {finish_booking_date.strftime('%d.%m.%Y %H:%M')}.\n\n"
            "✅ Подтвердить изменения?"), 
        reply_markup=reply_markup)
    return CHANGE_BOOKING_DATE

async def warning_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, f"Not found bookings", update)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="❌ <b>Ошибка!</b>\n"
            f"🔍 Не удалось найти бронирование для аккаунта {user_contact}.\n"
            "🔄 Пожалуйста, попробуйте еще раз.\n\n"
            "📲 Укажите ваш <b>Telegram</b> или номер телефона:\n\n"
            "🔹 <b>Telegram:</b> @username (начинайте с @)\n"
            "🔹 <b>Телефон:</b> +375XXXXXXXXX (обязательно с +375)\n"
            "❗️ Пожалуйста, вводите данные строго в указанном формате.",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return CHANGE_BOOKING_DATE_VALIDATE_USER

def reset_variables():
    global user_contact, old_booking_date, start_booking_date, finish_booking_date, max_date_booking, min_date_booking, booking, rental_price, selected_bookings
    user_contact = ''
    old_booking_date = date.today()
    start_booking_date = datetime.today()
    finish_booking_date = datetime.today()
    max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = date.today() - timedelta(days=1)
    booking = None
    rental_price = None
    selected_bookings = []