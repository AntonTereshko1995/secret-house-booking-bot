import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
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
from src.helpers import date_time_helper, string_helper
from src.date_time_picker import calendar_picker, hours_picker
from src.config.config import PERIOD_IN_MONTHS, CLEANING_HOURS
from dateutil.relativedelta import relativedelta
from src.constants import (
    BACK, 
    END,
    MENU, 
    STOPPING, 
    CHANGE_BOOKING_DATE, 
    VALIDATE_USER, 
    CHOOSE_BOOKING, 
    SET_START_DATE, 
    SET_START_TIME, 
    SET_FINISH_DATE, 
    SET_FINISH_TIME, 
    CONFIRM)

user_contact = ''
old_booking_date = date.today()
start_booking_date = datetime.today()
finish_booking_date = datetime.today()
max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
min_date_booking = date.today() - relativedelta(day=1)
database_service = DatabaseService()
calculation_rate_service = CalculationRateService()
calendar_service = CalendarService()
booking: BookingBase = None
rental_price: RentalPrice = None
selected_bookings = []

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(enter_user_contact, pattern=f"^{str(CHANGE_BOOKING_DATE)}$")],
        states={ 
            VALIDATE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_user_contact)],
            CHOOSE_BOOKING: [CallbackQueryHandler(choose_booking)], 
            SET_START_DATE: [CallbackQueryHandler(enter_start_date)], 
            SET_START_TIME: [CallbackQueryHandler(enter_start_time)], 
            SET_FINISH_DATE: [CallbackQueryHandler(enter_finish_date)], 
            SET_FINISH_TIME: [CallbackQueryHandler(enter_finish_time)], 
            CONFIRM: [CallbackQueryHandler(confirm_booking, pattern=f"^{CONFIRM}$")], 
            BACK: [CallbackQueryHandler(back_navigation, pattern=f"^{BACK}$")],
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

async def enter_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_variables()

    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="📲 Укажите ваш <b>Telegram</b> или номер телефона:\n\n"
            "🔹 <b>Telegram:</b> @username (начинайте с @)\n"
            "🔹 <b>Телефон:</b> +375XXXXXXXXX (обязательно с +375)\n"
            "❗️ Пожалуйста, вводите данные строго в указанном формате.",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return VALIDATE_USER

async def check_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user_input = update.message.text
        is_valid = string_helper.is_valid_user_contact(user_input)
        if is_valid:
            global user_contact
            user_contact = user_input
            return await choose_booking_message(update, context)
        else:
            await update.message.reply_text(
                "❌ <b>Ошибка!</b>\n"
                "Имя пользователя в Telegram или номер телефона введены некорректно.\n\n"
                "🔄 Пожалуйста, попробуйте еще раз.")
    else:
        await update.message.reply_text(
            "❌ <b>Ошибка:</b> Пустая строка.\n\n"
            "🔄 Пожалуйста, введите данные еще раз."
        )

    return VALIDATE_USER

async def choose_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    if (update.callback_query.data == str(END)):
        return await back_navigation(update, context)

    global booking, old_booking_date
    booking = next((b for b in selected_bookings if str(b.id) == update.callback_query.data), None)
    old_booking_date = booking.start_date
    return await start_date_message(update, context)

async def enter_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    selected, selected_date, is_action = await calendar_picker.process_calendar_selection(update, context, min_date=min_date_booking, max_date=max_date_booking, action_text="Назад в меню")
    if selected:
        global start_booking_date
        start_booking_date = selected_date
        return await start_time_message(update, context)
    elif is_action:
        return await back_navigation(update, context)
    return SET_START_DATE

async def enter_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    selected, time, is_action = await hours_picker.process_hours_selection(update, context)
    if selected:
        global start_booking_date
        start_booking_date = start_booking_date.replace(hour=time.hour, minute=time.minute)
        return await finish_date_message(update, context)
    elif is_action:
        return await back_navigation(update, context)
    return SET_START_TIME

async def enter_finish_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = start_booking_date.date() - timedelta(days=1)
    selected, selected_date, is_action = await calendar_picker.process_calendar_selection(update, context, min_date=min_date_booking, max_date=max_date_booking, action_text="Назад в меню")
    if selected:
        global finish_booking_date
        finish_booking_date = selected_date
        return await finish_time_message(update, context)
    elif is_action:
        return await back_navigation(update, context)
    return SET_FINISH_DATE

async def enter_finish_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    selected, time, is_action = await hours_picker.process_hours_selection(update, context)
    if selected:
        global finish_booking_date
        finish_booking_date = finish_booking_date.replace(hour=time.hour)
        is_any_booking = database_service.is_booking_between_dates(start_booking_date - timedelta(hours=CLEANING_HOURS), finish_booking_date + timedelta(hours=CLEANING_HOURS))
        if is_any_booking:
            return await start_date_message(update, context, is_error=True)
        
        selected_duration = finish_booking_date - start_booking_date
        duration_booking_hours = date_time_helper.seconds_to_hours(selected_duration.total_seconds())
        global rental_price
        rental_price = calculation_rate_service.get_tariff(booking.tariff)
        if duration_booking_hours > rental_price.duration_hours:
            return await start_date_message(update, context, incorrect_duration=True)

        return await confirm_message(update, context)
    elif is_action:
        return await back_navigation(update, context)
    return SET_FINISH_TIME

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    updated_booking = database_service.update_booking(booking.id, start_date=start_booking_date, end_date=finish_booking_date)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    admin_handler.inform_changing_booking_date(update, context, updated_booking, old_booking_date)
    calendar_service.move_event(updated_booking.calendar_event_id, start_booking_date, finish_booking_date)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=f"✅ <b>Бронирование успешно перенесено!</b>\n\n"
            f"📅 <b>С:</b> {start_booking_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"📅 <b>До:</b> {finish_booking_date.strftime('%d.%m.%Y %H:%M')}.\n",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return MENU

async def choose_booking_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global selected_bookings
    selected_bookings = database_service.get_booking_by_user_contact(user_contact)
    if not selected_bookings or len(selected_bookings) == 0:
        return await warning_message(update, context)
    
    keyboard = []
    for booking in selected_bookings:
        keyboard.append([InlineKeyboardButton(f"{booking.start_date.strftime('%d.%m.%Y %H:%M')} - {booking.end_date.strftime('%d.%m.%Y %H:%M')}", callback_data=str(booking.id))])

    keyboard.append([InlineKeyboardButton("Назад в меню", callback_data=END)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="📅 <b>Выберите бронирование, которое хотите изменить.</b>\n",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return CHOOSE_BOOKING

async def start_date_message(update: Update, context: ContextTypes.DEFAULT_TYPE, is_error: bool = False, incorrect_duration: bool = False):
    today = date.today()
    if is_error:
        message = ("❌ <b>Ошибка!</b>\n\n"
            "⏳ <b>Выбранные дата и время недоступны.</b>\n"
            "⚠️ Дата начала и конца бронирования пересекается с другим бронированием.\n\n"
            f"🧹 После каждого клиента нам нужно подготовить дом. Уборка занимает <b>{CLEANING_HOURS} часа</b>.\n\n"
            "🔄 Пожалуйста, выберите новую дату начала бронирования.")
    elif incorrect_duration:
        message = ("❌ <b>Ошибка!</b>\n\n"
            "⏳ <b>Максимальная продолжительность тарифа превышена.</b>\n"
            f"🕒 Длительность <b>{rental_price.name}</b>: {rental_price.duration_hours} ч.\n\n"
            "🔄 Пожалуйста, повторите попытку и выберите доступный вариант.\n\n"
            "📅 Выберите новую дату начала бронирования.")
    else:
        message = ("✅ <b>Ваше бронирование найдено!</b>\n\n"
            "📅 <b>Введите новую дату, на которую хотите перенести бронирование.</b>")
    await update.callback_query.edit_message_text(
        text=message, 
        parse_mode='HTML',
        reply_markup=calendar_picker.create_calendar(today, min_date=min_date_booking, max_date=max_date_booking, action_text="Назад в меню"))
    return SET_START_DATE

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
    await update.callback_query.edit_message_text(
        text=message, 
        parse_mode='HTML',
        reply_markup = hours_picker.create_hours_picker(action_text="Назад в меню", free_slots=available_slots, date=start_booking_date.date()))
    return SET_START_TIME

async def finish_date_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    min_date_booking = start_booking_date.date() - timedelta(days=1)
    await update.callback_query.edit_message_text(
        text="📅 <b>Выберите дату завершения бронирования.</b>\n"
            f"Вы выбрали дату и время заезда: {start_booking_date.strftime('%d.%m.%Y %H:%M')}.\n"
            "Теперь укажите день, когда планируете выехать.\n"
            "📌 Выезд должен быть позже времени заезда.", 
        reply_markup=calendar_picker.create_calendar(start_booking_date.date(), min_date=min_date_booking, max_date=max_date_booking, action_text="Назад в меню"))
    return SET_FINISH_DATE

async def finish_time_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feature_booking = database_service.get_booking_by_day(finish_booking_date.date(), booking.id)
    start_time = time(0, 0) if start_booking_date.date() != finish_booking_date.date() else start_booking_date.time()
    available_slots = date_time_helper.get_free_time_slots(feature_booking, finish_booking_date.date(), start_time=start_time, minus_time_from_start=True, add_time_to_end=True)
    await update.callback_query.edit_message_text(
        text="⏳ <b>Выберите времня завершения бронирования.</b>\n"
            f"Вы выбрали заезд: {start_booking_date.strftime('%d.%m.%Y %H:%M')}.\n"
            f"Вы выбрали дату выезда: {finish_booking_date.strftime('%d.%m.%Y')}.\n"
            "Теперь укажите время, когда хотите освободить дом.\n\n"
            "📌 Обратите внимание:\n"
            "🔹 Выезд должен быть позже времени заезда.\n"
            f"🔹 После каждого бронирования требуется {CLEANING_HOURS} часа на уборку.\n", 
        reply_markup=hours_picker.create_hours_picker(action_text="Назад в меню", free_slots=available_slots, date=finish_booking_date.date()))
    return SET_FINISH_TIME

async def confirm_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Подтвердить", callback_data=CONFIRM)],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        text = (f"📅 Подтвердите изменение даты бронирования:\n"
            f"🔹 <b>С</b> {old_booking_date.strftime('%d.%m.%Y')} \n"
            f"🔹 <b>На</b> {start_booking_date.strftime('%d.%m.%Y %H:%M')} "
            f"до {finish_booking_date.strftime('%d.%m.%Y %H:%M')}.\n\n"
            "✅ Подтвердить изменения?"), 
        parse_mode='HTML',
        reply_markup=reply_markup)
    return CONFIRM

async def warning_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    return VALIDATE_USER

def reset_variables():
    global user_contact, old_booking_date, start_booking_date, finish_booking_date, max_date_booking, min_date_booking, booking, rental_price
    user_contact = ''
    old_booking_date = date.today()
    start_booking_date = datetime.today()
    finish_booking_date = datetime.today()
    max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = date.today() - timedelta(days=1)
    booking = None
    rental_price = None
    selected_bookings.clear()