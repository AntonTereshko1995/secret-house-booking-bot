import sys
import os
from src.services.logger_service import LoggerService
from src.decorators.callback_error_handler import safe_callback_query
from src.services.navigation_service import NavigationService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.calendar_service import CalendarService
from src.services.redis import RedisSessionService
from datetime import date
from src.services.database_service import DatabaseService
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from src.handlers import admin_handler, menu_handler
from src.helpers import string_helper
from src.constants import (
    CANCEL_BOOKING_VALIDATE_USER,
    END,
    MENU,
    CANCEL_BOOKING,
    CONFIRM,
)

database_service = DatabaseService()
calendar_service = CalendarService()
navigation_service = NavigationService()
redis_service = RedisSessionService()


def get_handler():
    return [
        CallbackQueryHandler(choose_booking, pattern=rf"^CANCEL-BOOKING_(\d+|{END})$"),
        CallbackQueryHandler(
            confirm_cancel_booking, pattern=f"^CANCEL-CONFIRM_({CONFIRM}|{END})$"
        ),
        CallbackQueryHandler(back_navigation, pattern=f"^{END}$"),
    ]


async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler.show_menu(update, context)
    LoggerService.info(__name__, "Back to menu", update)
    redis_service.clear_cancel_booking(update)
    return MENU


@safe_callback_query()
async def enter_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.init_cancel_booking(update)
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
    return CANCEL_BOOKING_VALIDATE_USER


async def check_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user_input = update.message.text
        is_valid, cleaned_contact = string_helper.is_valid_user_contact(user_input)
        if is_valid:
            redis_service.update_cancel_booking_field(update, "user_contact", cleaned_contact)

            # Save contact to database
            try:
                chat_id = navigation_service.get_chat_id(update)
                user = database_service.get_user_by_chat_id(chat_id)

                if user:
                    database_service.update_user_contact(chat_id, cleaned_contact)
                    LoggerService.info(
                        __name__,
                        "User contact saved to database",
                        update,
                        **{"chat_id": chat_id, "contact": cleaned_contact},
                    )
                else:
                    user_name = update.effective_user.username or cleaned_contact
                    database_service.update_user_chat_id(user_name, chat_id)
                    database_service.update_user_contact(chat_id, cleaned_contact)
                    LoggerService.warning(
                        __name__,
                        "User not found by chat_id, created new user",
                        update,
                        **{"chat_id": chat_id, "contact": cleaned_contact},
                    )
            except Exception as e:
                LoggerService.error(
                    __name__,
                    "Failed to save user contact to database",
                    exception=e,
                    **{"contact": cleaned_contact},
                )

            return await choose_booking_message(update, context)
        else:
            LoggerService.warning(__name__, "User name is invalid", update)
            await update.message.reply_text(
                "❌ <b>Ошибка!</b>\n"
                "Имя пользователя в Telegram или номер телефона введены некорректно.\n\n"
                "🔄 Пожалуйста, попробуйте еще раз.",
                parse_mode="HTML",
            )
    return CANCEL_BOOKING_VALIDATE_USER


@safe_callback_query()
async def choose_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    redis_service.update_cancel_booking_field(update, "selected_booking_id", int(data))
    LoggerService.info(
        __name__, "Choose booking", update, **{"booking_id": data}
    )
    return await confirm_message(update, context)


@safe_callback_query()
async def confirm_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    LoggerService.info(__name__, "Confirm cancel booking", update)

    draft = redis_service.get_cancel_booking(update)
    if not draft or not draft.selected_booking_id:
        LoggerService.warning(__name__, "Draft is None or booking_id is missing (double click protection)", update)
        return await back_navigation(update, context)

    booking = database_service.get_booking_by_id(draft.selected_booking_id)

    updated_booking = database_service.update_booking(booking.id, is_canceled=True)
    calendar_service.cancel_event(updated_booking.calendar_event_id)
    await admin_handler.inform_cancel_booking(update, context, updated_booking)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text=f"❌ <b>Бронирование отменено</b> на <b>{booking.start_date.strftime('%d.%m.%Y')}</b>.\n\n"
        "📌 Если у вас возникли вопросы, свяжитесь с администратором.",
        reply_markup=reply_markup,
    )
    redis_service.clear_cancel_booking(update)
    return CANCEL_BOOKING


async def choose_booking_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    draft = redis_service.get_cancel_booking(update)
    selected_bookings = database_service.get_booking_by_user_contact(draft.user_contact)

    if not selected_bookings or len(selected_bookings) == 0:
        return await warning_message(update, context)

    # Store booking IDs in Redis
    booking_ids = [b.id for b in selected_bookings]
    redis_service.update_cancel_booking_field(update, "selected_bookings", booking_ids)

    keyboard = []
    for booking in selected_bookings:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{booking.start_date.strftime('%d.%m.%Y %H:%M')} - {booking.end_date.strftime('%d.%m.%Y %H:%M')}",
                    callback_data=f"CANCEL-BOOKING_{booking.id}",
                )
            ]
        )

    keyboard.append(
        [InlineKeyboardButton("Назад в меню", callback_data=f"CANCEL-BOOKING_{END}")]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="📅 <b>Выберите бронирование, которое хотите отменить.</b>\n",
        parse_mode="HTML",
        reply_markup=reply_markup,
    )
    return CANCEL_BOOKING


@safe_callback_query()
async def confirm_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(
                "Подтвердить", callback_data=f"CANCEL-CONFIRM_{CONFIRM}"
            )
        ],
        [InlineKeyboardButton("Назад в меню", callback_data=f"CANCEL-CONFIRM_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="❌ <b>Подтвердите отмену бронирования</b>.\n\n"
        "🔄 Для продолжения выберите соответствующую опцию.",
        reply_markup=reply_markup,
    )
    return CANCEL_BOOKING


async def warning_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.warning(__name__, "Booking is empty", update)
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
        parse_mode="HTML",
        reply_markup=reply_markup,
    )
    return CANCEL_BOOKING_VALIDATE_USER
