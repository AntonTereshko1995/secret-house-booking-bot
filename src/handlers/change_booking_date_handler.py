import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.models.booking import BookingBase
from src.services.database_service import DatabaseService
from datetime import datetime, date, time, timedelta
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters)
from src.handlers import menu_handler
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
    SET_OLD_START_DATE, 
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
booking: BookingBase = None

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(enter_user_contact, pattern=f"^{str(CHANGE_BOOKING_DATE)}$")],
        states={ 
            VALIDATE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_user_contact)],
            SET_OLD_START_DATE: [CallbackQueryHandler(enter_old_start_date)], 
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
        text="Напишите Ваш <b>Telegram</b>.\n"
        "Формат ввода @user_name (обязательно начинайте ввод с @).\n"
        "Формат ввода номера телефона +375251111111 (обязательно начинайте ввод с +375).\n",
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
            return await old_start_date_message(update, context)
        else:
            await update.message.reply_text("Ошибка: имя пользователя в Telegram или номер телефона введены не коректно.\n"
                                            "Повторите ввод еще раз.")
    else:
        await update.message.reply_text("Ошибка: Пустая строка.\n"
                                        "Повторите ввод еще раз.")

    return VALIDATE_USER

async def enter_old_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    if (update.callback_query.data == str(END)):
        return await back_navigation(update, context)

    selected, selected_date, is_action = await calendar_picker.process_calendar_selection(update, context, min_date=min_date_booking, max_date=max_date_booking, action_text="Назад в меню")
    if selected:
        global old_booking_date
        old_booking_date = selected_date
        is_loaded = load_booking()
        if is_loaded:
            return await start_date_message(update, context)
        else:
            return await warning_message(update, context)

    elif is_action:
        return await back_navigation(update, context)
    return SET_OLD_START_DATE

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
        return await confirm_message(update, context)
    elif is_action:
        return await back_navigation(update, context)
    return SET_FINISH_TIME

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    updated_booking = database_service.update_booking(booking.id, start_date=start_booking_date, end_date=finish_booking_date)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=f"Бронирование успешно перенесено:\n"
            f"c {start_booking_date.strftime('%d.%m.%Y %H:%M')} \n"
            f"до {finish_booking_date.strftime('%d.%m.%Y %H:%M')}.\n",
        reply_markup=reply_markup)
    return MENU

async def old_start_date_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = date.today()
    await update.message.reply_text(
        text="Введите дату заезда Вашего бронирования.\n",
        reply_markup=calendar_picker.create_calendar(today.year, today.month, min_date=min_date_booking, max_date=max_date_booking, action_text="Назад в меню"))
    return SET_OLD_START_DATE

async def start_date_message(update: Update, context: ContextTypes.DEFAULT_TYPE, is_error: bool = False):
    today = date.today()
    if is_error:
        message = ("Ощибка! Время и дата выбране не правильно.\n"
                   "Дата начала и конца бронирования пересекается с другим бронированием.\n"
                   f"После каждого клиента нам нужно убрать дом. Для этого нам нужно {CLEANING_HOURS} часа.\n"
                   "Повторите попытку заново.\n\n"
                   "Выберете дату начала бронирования.")
    else:
        message = ("Нашли Ваше бронирование.\n"
            "Введите дату на которую Вы хотите перенести бронирование.\n")
    await update.callback_query.edit_message_text(
        text=message, 
        reply_markup=calendar_picker.create_calendar(today.year, today.month, min_date=min_date_booking, max_date=max_date_booking, action_text="Назад в меню"))
    return SET_START_DATE

async def start_time_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feature_booking = database_service.get_booking_by_day(start_booking_date.date(), booking.id)
    available_slots = date_time_helper.get_free_time_slots(feature_booking, start_booking_date.date(), minus_time_from_start=True, add_time_to_end=True)
    await update.callback_query.edit_message_text(
        text="Выберете время начала бронирования.\n", 
        reply_markup = hours_picker.create_hours_picker(action_text="Назад в меню", free_slots=available_slots, date=start_booking_date.date()))
    return SET_START_TIME

async def finish_date_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = date.today()
    min_date_booking = start_booking_date.date() - timedelta(days=1)
    await update.callback_query.edit_message_text(
        text="Выберете дату завершения бронирования.\n", 
        reply_markup=calendar_picker.create_calendar(today.year, today.month, min_date=min_date_booking, max_date=max_date_booking, action_text="Назад в меню"))
    return SET_FINISH_DATE

async def finish_time_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feature_booking = database_service.get_booking_by_day(finish_booking_date.date(), booking.id)
    start_time = time(0, 0) if start_booking_date.date() != finish_booking_date.date() else start_booking_date.time()
    available_slots = date_time_helper.get_free_time_slots(feature_booking, finish_booking_date.date(), start_time=start_time, minus_time_from_start=True, add_time_to_end=True)
    await update.callback_query.edit_message_text(
        text="Выберете время завершения бронирования.\n", 
        reply_markup=hours_picker.create_hours_picker(action_text="Назад в меню", free_slots=available_slots, date=finish_booking_date.date()))
    return SET_FINISH_TIME

async def confirm_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Подтвердить", callback_data=CONFIRM)],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        text=f"Подтвердите изменение даты бронирования с {old_booking_date.strftime('%d.%m.%Y')} "
            f"на {start_booking_date.strftime('%d.%m.%Y %H:%M')} "
            f"до {finish_booking_date.strftime('%d.%m.%Y %H:%M')}.", 
        reply_markup=reply_markup)
    return CONFIRM

async def warning_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        text="Ошибка!\n"
            "Не удалось найти брониование.\n"
            "Повторите попытку еще раз.\n"
            "\n"
            "Введите имя пользователя повторно. \n"
            "Напишите Ваш <b>Telegram</b>.\n"
            "Формат ввода @user_name (обязательно начинайте ввод с @).\n"
            "Формат ввода номера телефона +375251111111 (обязательно начинайте ввод с +375).\n",
        reply_markup=reply_markup)
    return VALIDATE_USER

def reset_variables():
    global user_contact, old_booking_date, start_booking_date, finish_booking_date, max_date_booking, min_date_booking, booking
    user_contact = ''
    old_booking_date = date.today()
    start_booking_date = datetime.today()
    finish_booking_date = datetime.today()
    max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = date.today() - timedelta(days=1)
    booking = None

def load_booking() -> bool:
    global booking
    booking = database_service.get_booking_by_start_date(user_contact, old_booking_date.date())
    return True if booking else False