import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from telegram_bot.client.backend_api import BackendAPIClient, APIError
from telegram_bot.services.logger_service import LoggerService
from telegram_bot.services.navigation_service import NavigationService
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram_bot.handlers import menu_handler
from telegram_bot.helpers import string_helper, tariff_helper
from backend.models.enum.tariff import Tariff
from telegram_bot.constants import END, MENU, USER_BOOKING_VALIDATE_USER, USER_BOOKING
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
user_contact: str
navigation_service = NavigationService()


def get_handler():
    return [CallbackQueryHandler(back_navigation, pattern=f"^{END}$")]


async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler.show_menu(update, context)
    LoggerService.info(__name__, "Back to menu", update)
    return MENU


async def enter_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, "Enter user contact", update)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="📲 Укажите ваш <b>Telegram</b> или номер телефона:\n\n"
        "🔹 <b>Telegram:</b> @username (начинайте с @)\n"
        "🔹 <b>Телефон:</b> +375XXXXXXXXX (обязательно с +375)\n"
        "❗️ Пожалуйста, вводите данные строго в указанном формате.",
        reply_markup=reply_markup,
    )
    return USER_BOOKING_VALIDATE_USER


async def check_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user_input = update.message.text
        is_valid, cleaned_contact = string_helper.is_valid_user_contact(user_input)
        if is_valid:
            global user_contact
            user_contact = cleaned_contact

            # Save contact via API
            api_client = BackendAPIClient()
            try:
                chat_id = navigation_service.get_chat_id(update)
                user = await api_client.get_user_by_chat_id(chat_id)

                if user:
                    await api_client.create_or_update_user({
                        "contact": cleaned_contact,
                        "chat_id": chat_id
                    })
                    LoggerService.info(
                        __name__,
                        "User contact saved to database",
                        update,
                        kwargs={"chat_id": chat_id, "contact": cleaned_contact},
                    )
                else:
                    user_name = update.effective_user.username or cleaned_contact
                    await api_client.create_or_update_user({
                        "contact": cleaned_contact,
                        "chat_id": chat_id,
                        "name": user_name
                    })
                    LoggerService.warning(
                        __name__,
                        "User not found by chat_id, created new user",
                        update,
                        kwargs={"chat_id": chat_id, "contact": cleaned_contact},
                    )
            except APIError as e:
                logger.error(f"Failed to save user contact: {e}")
                LoggerService.error(
                    __name__,
                    "Failed to save user contact to database",
                    exception=e,
                    kwargs={"contact": cleaned_contact},
                )

            return await display_bookings(update, context)
        else:
            LoggerService.warning(__name__, "User name is invalid", update)
            await update.message.reply_text(
                "❌ <b>Ошибка!</b>\n"
                "Имя пользователя в Telegram или номер телефона введены некорректно.\n\n"
                "🔄 Пожалуйста, попробуйте еще раз.",
                parse_mode="HTML",
            )
    return USER_BOOKING_VALIDATE_USER


async def display_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_client = BackendAPIClient()
    message = ""

    try:
        booking_list = await api_client.get_user_bookings(user_contact)

        if not booking_list or len(booking_list) == 0:
            LoggerService.info(__name__, "Booking not found", update)
            message = (
                "❌ <b>Ошибка!</b>\n"
                "🔍 Не удалось найти бронирование.\n\n"
                "🔄 Пожалуйста, попробуйте еще раз.\n\n"
                "📲 Укажите ваш <b>Telegram</b> или номер телефона:\n\n"
                "🔹 <b>Telegram:</b> @username (начинайте с @)\n"
                "🔹 <b>Телефон:</b> +375XXXXXXXXX (обязательно с +375)\n"
                "❗️ Пожалуйста, вводите данные строго в указанном формате."
            )
        else:
            for booking in booking_list:
                LoggerService.info(__name__, "Booking is founded.", update)
                start_date = datetime.fromisoformat(booking["start_date"])
                end_date = datetime.fromisoformat(booking["end_date"])
                booking_tariff = Tariff[booking["tariff"]]

                message += (
                    f"📌 <b>Бронирование подтверждено</b>\n"
                    f"📅 <b>Заезд:</b> {start_date.strftime('%d.%m.%Y %H:%M')}\n"
                    f"📅 <b>Выезд:</b> {end_date.strftime('%d.%m.%Y %H:%M')}\n"
                    f"💼 <b>Тариф:</b> {tariff_helper.get_name(booking_tariff)}\n"
                    f"💰 <b>Стоимость:</b> {booking['price']} руб.\n"
                    f"✔ <b>Количество гостей:</b> {booking.get('number_of_guests', 'N/A')}\n"
                    f"✔ <b>Сауна:</b> {string_helper.bool_to_str(booking.get('has_sauna', False))}\n"
                    f"✔ <b>Фотосессия:</b> {string_helper.bool_to_str(booking.get('has_photoshoot', False))}\n"
                    f"✔ <b>Белая спалня:</b> {string_helper.bool_to_str(booking.get('has_white_bedroom', False))}\n"
                    f"✔ <b>Зеленая спальня:</b> {string_helper.bool_to_str(booking.get('has_green_bedroom', False))}\n"
                    f"✔ <b>Секретная комната:</b> {string_helper.bool_to_str(booking.get('has_secret_room', False))}\n"
                    f"💬 <b>Комментарий:</b> {booking.get('comment', '')}\n\n\n"
                )
    except APIError as e:
        logger.error(f"Failed to get user bookings: {e}")
        message = (
            "❌ <b>Ошибка!</b>\n"
            "Произошла ошибка при получении бронирований. Пожалуйста, попробуйте позже."
        )

    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text=message, parse_mode="HTML", reply_markup=reply_markup
    )
    return USER_BOOKING
