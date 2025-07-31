import sys
import os
from src.services.logger_service import LoggerService
from src.services.navigation_service import NavigatonService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.calendar_service import CalendarService
from datetime import date
from src.services.database_service import DatabaseService
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, CallbackQueryHandler)
from src.handlers import admin_handler, menu_handler
from src.helpers import string_helper
from src.constants import CANCEL_BOOKING_VALIDATE_USER, END, MENU, CANCEL_BOOKING, CONFIRM

user_contact = ''
database_service = DatabaseService()
calendar_service = CalendarService()
navigation_service = NavigatonService()
selected_bookings = []

def get_handler():
    return [
        CallbackQueryHandler(choose_booking, pattern=f"^CANCEL-BOOKING_(\d+|{END})$"),
        CallbackQueryHandler(confirm_cancel_booking, pattern=f"^CANCEL-CONFIRM_({CONFIRM}|{END})$"),
        CallbackQueryHandler(back_navigation, pattern=f"^{END}$")
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
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="📲 Укажите ваш <b>Telegram</b> или номер телефона:\n\n"
            "🔹 <b>Telegram:</b> @username (начинайте с @)\n"
            "🔹 <b>Телефон:</b> +375XXXXXXXXX (обязательно с +375)\n"
            "❗️ Пожалуйста, вводите данные строго в указанном формате.",
        reply_markup=reply_markup)
    return CANCEL_BOOKING_VALIDATE_USER

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
                "🔄 Пожалуйста, попробуйте еще раз.",
                parse_mode='HTML'
            )
    return CANCEL_BOOKING_VALIDATE_USER

async def choose_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if (data == str(END)):
        return await back_navigation(update, context)

    global booking
    booking = next((b for b in selected_bookings if str(b.id) == data), None)
    LoggerService.info(__name__, f"Choose booking", update, kwargs={'booking_id': booking.id})
    return await confirm_message(update, context)

async def confirm_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if (data == str(END)):
        return await back_navigation(update, context)

    LoggerService.info(__name__, f"Confirm cancel booking", update)
    updated_booking = database_service.update_booking(booking.id, is_canceled=True)
    calendar_service.cancel_event(updated_booking.calendar_event_id)
    await admin_handler.inform_cancel_booking(update, context, updated_booking)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text=f"❌ <b>Бронирование отменено</b> на <b>{booking_date.strftime('%d.%m.%Y')}</b>.\n\n"
            "📌 Если у вас возникли вопросы, свяжитесь с администратором.",
        reply_markup=reply_markup)
    return CANCEL_BOOKING

async def choose_booking_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global selected_bookings
    selected_bookings = database_service.get_booking_by_user_contact(user_contact)
    if not selected_bookings or len(selected_bookings) == 0:
        return await warning_message(update, context)
    
    keyboard = []
    for booking in selected_bookings:
        keyboard.append([InlineKeyboardButton(
            f"{booking.start_date.strftime('%d.%m.%Y %H:%M')} - {booking.end_date.strftime('%d.%m.%Y %H:%M')}", 
            callback_data=f"CANCEL-BOOKING_{booking.id}")])

    keyboard.append([InlineKeyboardButton("Назад в меню", callback_data=f"CANCEL-BOOKING_{END}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="📅 <b>Выберите бронирование, которое хотите отменить.</b>\n",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return CANCEL_BOOKING

async def confirm_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Подтвердить", callback_data=f"CANCEL-CONFIRM_{CONFIRM}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"CANCEL-CONFIRM_{END}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text=f"❌ <b>Подтвердите отмену бронирования</b>.\n\n"
            "🔄 Для продолжения выберите соответствующую опцию.",
        reply_markup=reply_markup)
    return CANCEL_BOOKING

async def warning_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.warning(__name__, f"Booking is empty", update)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="❌ <b>Ошибка!</b>\n"
            "🔍 Не удалось найти бронирование.\n\n"
            "🔄 Пожалуйста, попробуйте еще раз.\n\n"
            "📲 Укажите ваш <b>Telegram</b> или номер телефона:\n\n"
            "🔹 <b>Telegram:</b> @username (начинайте с @)\n"
            "🔹 <b>Телефон:</b> +375XXXXXXXXX (обязательно с +375)\n"
            "❗️ Пожалуйста, вводите данные строго в указанном формате.",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return CANCEL_BOOKING_VALIDATE_USER

def reset_variables():
    global user_contact, booking_date, selected_bookings
    user_contact = ''
    booking_date = date.today()
    selected_bookings = []