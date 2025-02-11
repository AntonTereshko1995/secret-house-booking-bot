import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from matplotlib.dates import relativedelta
from src.config.config import PERIOD_IN_MONTHS
from src.services.calendar_service import CalendarService
from datetime import datetime, date, timedelta
from src.date_time_picker import calendar_picker
from src.services.database_service import DatabaseService
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters)
from src.handlers import admin_handler, menu_handler
from src.helpers import string_helper
from src.constants import BACK, END, MENU, STOPPING, CANCEL_BOOKING, VALIDATE_USER, CHOOSE_BOOKING, CONFIRM

user_contact = ''
database_service = DatabaseService()
calendar_service = CalendarService()
selected_bookings = []

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(enter_user_contact, pattern=f"^{str(CANCEL_BOOKING)}$")],
        states={ 
            VALIDATE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_user_contact)],
            CHOOSE_BOOKING: [CallbackQueryHandler(choose_booking)], 
            CONFIRM: [CallbackQueryHandler(confirm_cancel_booking, pattern=f"^{CONFIRM}$")], 
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
                "🔄 Пожалуйста, попробуйте еще раз.",
                parse_mode='HTML'
            )
    else:
        await update.message.reply_text(
            "❌ <b>Ошибка:</b> Пустая строка.\n\n"
            "🔄 Пожалуйста, введите данные еще раз.",
            parse_mode='HTML'
        )

    return VALIDATE_USER

async def choose_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    if (update.callback_query.data == str(END)):
        return await back_navigation(update, context)

    global booking
    booking = next((b for b in selected_bookings if str(b.id) == update.callback_query.data), None)
    return await confirm_message(update, context)

async def confirm_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    updated_booking = database_service.update_booking(booking.id, is_canceled=True)
    calendar_service.cancel_event(updated_booking.calendar_event_id)
    admin_handler.inform_cancel_booking(update, context, updated_booking)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=f"❌ <b>Бронирование отменено</b> на <b>{booking_date.strftime('%d.%m.%Y')}</b>.\n\n"
            "📌 Если у вас возникли вопросы, свяжитесь с администратором.",
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
        text="📅 <b>Выберите бронирование, которое хотите отменить.</b>\n",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return CHOOSE_BOOKING

async def confirm_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Подтвердить", callback_data=CONFIRM)],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=f"❌ <b>Подтвердите отмену бронирования</b>.\n\n"
            "🔄 Для продолжения выберите соответствующую опцию.",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return CONFIRM

async def warning_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    return VALIDATE_USER

def reset_variables():
    global user_contact, booking_date, selected_bookings
    user_contact = ''
    booking_date = date.today()
    selected_bookings = []