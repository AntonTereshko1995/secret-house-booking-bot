import sys
import os
from src.services.logger_service import LoggerService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.database_service import DatabaseService
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters)
from src.handlers import menu_handler
from src.helpers import string_helper, tariff_helper
from src.constants import (
    END,
    MENU, 
    STOPPING, 
    SET_USER,
    VALIDATE_USER, 
    USER_BOOKING)

user_contact: str
database_service = DatabaseService()

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(enter_user_contact, pattern=f"^{USER_BOOKING}$")],
        states={
            SET_USER: [CallbackQueryHandler(enter_user_contact)],
            VALIDATE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_user_contact)],
        },
        fallbacks=[CallbackQueryHandler(back_navigation, pattern=f"^{END}$")],
        map_to_parent={
            END: MENU,
            STOPPING: END,
        })
    return handler

async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler.show_menu(update, context)
    LoggerService.info(__name__, f"Back to menu", update)
    return END

async def enter_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, "Enter user contact", update)
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
            return await display_bookings(update, context)
        else:
            LoggerService.warning(__name__, "User name is invalid", update)
            await update.message.reply_text(
                "❌ <b>Ошибка!</b>\n"
                "Имя пользователя в Telegram или номер телефона введены некорректно.\n\n"
                "🔄 Пожалуйста, попробуйте еще раз.",
                parse_mode='HTML',)
    return VALIDATE_USER

async def display_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    booking_list = database_service.get_booking_by_user_contact(user_contact)
    message = ""
    if not booking_list or len(booking_list) == 0:
        LoggerService.info(__name__, "Booking not found", update)
        message = ("❌ <b>Ошибка!</b>\n"
            "🔍 Не удалось найти бронирование.\n\n"
            "🔄 Пожалуйста, попробуйте еще раз.\n\n"
            "📲 Укажите ваш <b>Telegram</b> или номер телефона:\n\n"
            "🔹 <b>Telegram:</b> @username (начинайте с @)\n"
            "🔹 <b>Телефон:</b> +375XXXXXXXXX (обязательно с +375)\n"
            "❗️ Пожалуйста, вводите данные строго в указанном формате.")
    else:
        for booking in booking_list:
            LoggerService.info(__name__, "Booking is founded.", update)
            message += (
                f"📌 <b>Бронирование подтверждено</b>\n"
                f"📅 <b>Заезд:</b> {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
                f"📅 <b>Выезд:</b> {booking.end_date.strftime('%d.%m.%Y %H:%M')}\n"
                f"💼 <b>Тариф:</b> {tariff_helper.get_name(booking.tariff)}\n"
                f"💰 <b>Стоимость:</b> {booking.price} руб.\n"
                f"✔ <b>Количество гостей:</b> {booking.number_of_guests}\n"
                f"✔ <b>Сауна:</b> {string_helper.bool_to_str(booking.has_sauna)}\n"
                f"✔ <b>Фотосессия:</b> {string_helper.bool_to_str(booking.has_photoshoot)}\n"
                f"✔ <b>Белая спалня:</b> {string_helper.bool_to_str(booking.has_white_bedroom)}\n"
                f"✔ <b>Зеленая спальня:</b> {string_helper.bool_to_str(booking.has_green_bedroom)}\n"
                f"✔ <b>Секретная комната:</b> {string_helper.bool_to_str(booking.has_secret_room)}\n"
                f"💬 <b>Комментарий:</b> {booking.comment if booking.comment else ''}\n\n\n")
            
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text=message,
        parse_mode='HTML',
        reply_markup=reply_markup)