from datetime import date, datetime, time, timedelta
import asyncio
import sys
import os
from typing import Sequence
from src.services.logger_service import LoggerService

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.navigation_service import NavigatonService
from src.services.settings_service import SettingsService
from src.services.file_service import FileService
from src.services.calculation_rate_service import CalculationRateService
from db.models.gift import GiftBase
from matplotlib.dates import relativedelta
from src.constants import (
    END,
    SET_PASSWORD,
    ENTER_PRICE,
    ENTER_PREPAYMENT,
    BROADCAST_INPUT,
)
from src.services.calendar_service import CalendarService
from db.models.user import UserBase
from db.models.booking import BookingBase
from src.services.database_service import DatabaseService
from src.config.config import (
    ADMIN_CHAT_ID,
    PERIOD_IN_MONTHS,
    INFORM_CHAT_ID,
    BANK_CARD_NUMBER,
    BANK_PHONE_NUMBER,
    ADMINISTRATION_CONTACT,
)
from telegram.error import TelegramError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from src.helpers import string_helper, tariff_helper

database_service = DatabaseService()
calendar_service = CalendarService()
calculation_rate_service = CalculationRateService()
file_service = FileService()
settings_service = SettingsService()
navigation_service = NavigatonService()


def entry_points():
    """Returns list of entry points for ConversationHandler"""
    return [
        CallbackQueryHandler(
            booking_callback,
            pattern=r"^booking_\d+_chatid_(\d+)_bookingid_(\d+)_cash_(True|False)$",
        ),
        CallbackQueryHandler(
            gift_callback, pattern=r"^gift_\d+_chatid_(\d+)_giftid_(\d+)$"
        ),
    ]


def get_purchase_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=entry_points(),
        states={
            ENTER_PRICE: [
                MessageHandler(
                    filters.Chat(chat_id=ADMIN_CHAT_ID)
                    & filters.TEXT
                    & ~filters.COMMAND,
                    handle_price_input,
                ),
                CallbackQueryHandler(
                    cancel_price_input, pattern="^cancel_price_input$"
                ),
                CallbackQueryHandler(
                    booking_callback,
                    pattern=r"^booking_\d+_chatid_(\d+)_bookingid_(\d+)_cash_(True|False)$",
                ),
            ],
            ENTER_PREPAYMENT: [
                MessageHandler(
                    filters.Chat(chat_id=ADMIN_CHAT_ID)
                    & filters.TEXT
                    & ~filters.COMMAND,
                    handle_prepayment_input,
                ),
                CallbackQueryHandler(
                    cancel_prepayment_input, pattern="^cancel_prepayment_input$"
                ),
                CallbackQueryHandler(
                    booking_callback,
                    pattern=r"^booking_\d+_chatid_(\d+)_bookingid_(\d+)_cash_(True|False)$",
                ),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(
                booking_callback,
                pattern=r"^booking_\d+_chatid_(\d+)_bookingid_(\d+)_cash_(True|False)$",
            ),
            CallbackQueryHandler(
                gift_callback, pattern=r"^gift_\d+_chatid_(\d+)_giftid_(\d+)$"
            ),
        ],
    )
    return handler


def get_password_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CommandHandler("change_password", change_password)],
        states={
            SET_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password_input),
                CallbackQueryHandler(
                    cancel_password_change, pattern="^cancel_password_change$"
                ),
            ],
        },
        fallbacks=[],
    )
    return handler


def get_broadcast_handler() -> ConversationHandler:
    """Returns ConversationHandler for broadcast command (all users)"""
    handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", start_broadcast)],
        states={
            BROADCAST_INPUT: [
                MessageHandler(
                    filters.Chat(chat_id=ADMIN_CHAT_ID)
                    & filters.TEXT
                    & ~filters.COMMAND,
                    handle_broadcast_input,
                ),
                CallbackQueryHandler(cancel_broadcast, pattern="^cancel_broadcast$"),
            ],
        },
        fallbacks=[],
    )
    return handler


def get_broadcast_with_bookings_handler() -> ConversationHandler:
    """Returns ConversationHandler for broadcast_with_bookings command"""
    handler = ConversationHandler(
        entry_points=[
            CommandHandler("broadcast_with_bookings", start_broadcast_with_bookings)
        ],
        states={
            BROADCAST_INPUT: [
                MessageHandler(
                    filters.Chat(chat_id=ADMIN_CHAT_ID)
                    & filters.TEXT
                    & ~filters.COMMAND,
                    handle_broadcast_input,
                ),
                CallbackQueryHandler(cancel_broadcast, pattern="^cancel_broadcast$"),
            ],
        },
        fallbacks=[],
    )
    return handler


def get_broadcast_without_bookings_handler() -> ConversationHandler:
    """Returns ConversationHandler for broadcast_without_bookings command"""
    handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                "broadcast_without_bookings", start_broadcast_without_bookings
            )
        ],
        states={
            BROADCAST_INPUT: [
                MessageHandler(
                    filters.Chat(chat_id=ADMIN_CHAT_ID)
                    & filters.TEXT
                    & ~filters.COMMAND,
                    handle_broadcast_input,
                ),
                CallbackQueryHandler(cancel_broadcast, pattern="^cancel_broadcast$"),
            ],
        },
        fallbacks=[],
    )
    return handler


async def change_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask admin to enter new password via text input"""
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
        return END

    # Store current password in context
    context.user_data["old_password"] = settings_service.password

    keyboard = [
        [InlineKeyboardButton("Отмена", callback_data="cancel_password_change")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"📝 <b>Изменение пароля от ключницы</b>\n\n"
        f"Текущий пароль: <b>{settings_service.password}</b>\n\n"
        f"Введите новый 4-значный пароль цифрами (например: 1235):"
    )

    await update.message.reply_text(
        text=message, reply_markup=reply_markup, parse_mode="HTML"
    )
    return SET_PASSWORD


async def handle_password_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle password input from admin - called for text input in SET_PASSWORD state"""
    chat_id = update.effective_chat.id

    # Only respond to admin chat
    if chat_id != ADMIN_CHAT_ID:
        return END

    password_text = update.message.text.strip()

    # Validate input - must be exactly 4 digits
    if not password_text.isdigit():
        await update.message.reply_text(
            "❌ Пароль должен содержать только цифры. Попробуйте еще раз:"
        )
        return SET_PASSWORD

    if len(password_text) != 4:
        await update.message.reply_text(
            "❌ Пароль должен содержать ровно 4 цифры. Попробуйте еще раз:"
        )
        return SET_PASSWORD

    # Update password
    old_password = context.user_data.get("old_password", settings_service.password)
    settings_service.password = password_text

    await update.message.reply_text(
        f"✅ Пароль изменен!\n\n"
        f"Старый пароль: {old_password}\n"
        f"Новый пароль: {password_text}"
    )

    # Clear context
    context.user_data.pop("old_password", None)

    return END


async def cancel_password_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel password change"""
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("❌ Изменение пароля отменено.")

    # Clear context
    context.user_data.pop("old_password", None)

    return END


async def get_booking_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
    else:
        bookings = get_future_bookings()

        if not bookings:
            await update.message.reply_text("🔍 Не найдено бронирований.")
            return END

        for booking in bookings:
            user = database_service.get_user_by_id(booking.user_id)
            message = "⛔ Отменен\n" if booking.is_canceled else ""
            message += (
                f"Пользователь: {user.contact}\n"
                f"Дата начала: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
                f"Дата завершения: {booking.end_date.strftime('%d.%m.%Y %H:%M')}\n"
                f"Тариф: {tariff_helper.get_name(booking.tariff)}\n"
                f"Стоимость: {booking.price} руб.\n"
                f"Предоплата: {booking.prepayment_price} руб.\n"
            )
            await update.message.reply_text(text=message)
    return END


async def get_unpaid_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to show all unpaid bookings"""
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
        return END

    bookings = database_service.get_unpaid_bookings()

    if not bookings:
        await update.message.reply_text("🔍 Не найдено неоплаченных бронирований.")
        return END

    for booking in bookings:
        await accept_booking_payment(
            update, context, booking, booking.user.chat_id, None, None, False
        )

    return END


async def get_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to show comprehensive booking and user statistics"""
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
        return END

    # Show loading message
    loading_msg = await update.message.reply_text("⏳ Генерирую статистику...")

    try:
        # Import services
        from src.services.statistics_service import StatisticsService
        from src.helpers.statistics_helper import format_statistics_message

        # Get statistics
        stats_service = StatisticsService()
        stats = stats_service.get_complete_statistics()

        # Format message
        message = format_statistics_message(stats)

        # Delete loading message and send statistics
        await loading_msg.delete()
        await update.message.reply_text(message, parse_mode="HTML")

    except Exception as e:
        LoggerService.error(__name__, "get_statistics", e)
        await loading_msg.delete()
        await update.message.reply_text(
            "❌ Ошибка при генерации статистики. Проверьте логи."
        )

    return END


async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to start broadcast to ALL users - asks for message text"""
    return await _start_broadcast_with_filter(update, context, filter_type="all")


async def start_broadcast_with_bookings(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Admin command to start broadcast to users WITH bookings - asks for message text"""
    return await _start_broadcast_with_filter(
        update, context, filter_type="with_bookings"
    )


async def start_broadcast_without_bookings(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Admin command to start broadcast to users WITHOUT bookings - asks for message text"""
    return await _start_broadcast_with_filter(
        update, context, filter_type="without_bookings"
    )


async def _start_broadcast_with_filter(
    update: Update, context: ContextTypes.DEFAULT_TYPE, filter_type: str
):
    """
    Internal function to start broadcast with user filter.

    Args:
        filter_type: "all", "with_bookings", or "without_bookings"
    """
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
        return END

    # Get chat IDs based on filter
    if filter_type == "all":
        chat_ids = database_service.get_all_user_chat_ids()
        filter_label = "всем пользователям"
    elif filter_type == "with_bookings":
        chat_ids = database_service.get_user_chat_ids_with_bookings()
        filter_label = "пользователям С бронями"
    elif filter_type == "without_bookings":
        chat_ids = database_service.get_user_chat_ids_without_bookings()
        filter_label = "пользователям БЕЗ броней"
    else:
        await update.message.reply_text("❌ Неверный тип фильтра.")
        return END

    total_users = len(chat_ids)

    if total_users == 0:
        await update.message.reply_text(
            f"❌ В базе нет пользователей для рассылки ({filter_label})."
        )
        return END

    # Store filter info in context for later use
    context.user_data["broadcast_filter"] = filter_type
    context.user_data["broadcast_chat_ids"] = chat_ids

    # Prompt for message input
    keyboard = [[InlineKeyboardButton("Отмена", callback_data="cancel_broadcast")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"📢 <b>Рассылка сообщений</b>\n\n"
        f"🎯 Аудитория: <b>{filter_label}</b>\n"
        f"👥 Количество получателей: <b>{total_users}</b>\n"
        f"⏱ Примерное время: <b>~{total_users} секунд</b>\n\n"
        f"✏️ Введите текст сообщения для рассылки:"
    )

    await update.message.reply_text(
        text=message, reply_markup=reply_markup, parse_mode="HTML"
    )

    return BROADCAST_INPUT


async def handle_broadcast_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast message input from admin and execute broadcast"""
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_CHAT_ID:
        return END

    # Get message text
    message_text = update.message.text.strip()

    if not message_text:
        await update.message.reply_text(
            "❌ Сообщение не может быть пустым. Попробуйте еще раз:"
        )
        return BROADCAST_INPUT

    # Store in context for potential future use
    context.user_data["broadcast_message"] = message_text

    # Get chat IDs from context (stored by _start_broadcast_with_filter)
    chat_ids = context.user_data.get("broadcast_chat_ids", [])
    filter_type = context.user_data.get("broadcast_filter", "all")

    # Fallback: if no chat_ids in context, get all users
    if not chat_ids:
        chat_ids = database_service.get_all_user_chat_ids()
        filter_type = "all"

    # Get filter label for confirmation message
    if filter_type == "all":
        filter_label = "всем пользователям"
    elif filter_type == "with_bookings":
        filter_label = "пользователям С бронями"
    elif filter_type == "without_bookings":
        filter_label = "пользователям БЕЗ броней"
    else:
        filter_label = "выбранным пользователям"

    # Send confirmation and start broadcast
    await update.message.reply_text(
        f"✅ Начинаю рассылку ({filter_label})\n"
        f"👥 Количество: {len(chat_ids)} пользователей\n"
        f"📤 Это займет примерно {len(chat_ids)} секунд."
    )

    # Execute broadcast with rate limiting
    result = await execute_broadcast(context, chat_ids, message_text)

    # Send completion summary
    summary = (
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📊 Статистика:\n"
        f"• Всего пользователей: {result['total_users']}\n"
        f"• Успешно отправлено: {result['sent']}\n"
        f"• Не доставлено: {result['failed']}\n"
        f"• Время выполнения: {result['duration_seconds']:.1f} сек"
    )

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID, text=summary, parse_mode="HTML"
    )

    # Clear context
    context.user_data.pop("broadcast_message", None)
    context.user_data.pop("broadcast_filter", None)
    context.user_data.pop("broadcast_chat_ids", None)

    return END


async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel broadcast operation"""
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("❌ Рассылка отменена.")

    # Clear context
    context.user_data.pop("broadcast_message", None)
    context.user_data.pop("broadcast_filter", None)
    context.user_data.pop("broadcast_chat_ids", None)

    return END


async def execute_broadcast(
    context: ContextTypes.DEFAULT_TYPE, chat_ids: list[int], message: str
) -> dict:
    """
    Execute broadcast with rate limiting and error handling

    Rate limiting strategy:
    - 1 message per second per chat (Telegram limit)
    - ~30 messages per second globally (free tier)
    - Use 1.1 second delay to stay safe (~27 msg/sec)
    """
    import time

    start_time = time.time()
    total_users = len(chat_ids)
    sent_count = 0
    failed_count = 0

    for index, chat_id in enumerate(chat_ids):
        try:
            # CRITICAL: Rate limiting - 1 msg/sec per chat
            # Use asyncio.sleep() for non-blocking delay
            await context.bot.send_message(
                chat_id=chat_id, text=message, parse_mode="HTML"
            )
            sent_count += 1

            # Progress update every 10 users
            if (index + 1) % 10 == 0:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"📤 Прогресс: {index + 1}/{total_users} ({sent_count} отправлено, {failed_count} ошибок)",
                )

            # CRITICAL: Rate limit delay
            # 1.1 seconds = safe rate (~0.9 msg/sec per chat, ~27 msg/sec globally)
            await asyncio.sleep(1.1)

        except Exception as e:
            # Handle common errors: bot blocked, chat deleted
            failed_count += 1
            error_str = str(e)

            # Only log unexpected errors (not blocks/deletions)
            if "Forbidden" not in error_str and "Chat not found" not in error_str:
                LoggerService.error(
                    __name__, f"Broadcast error for chat {chat_id}", exception=e
                )

    duration = time.time() - start_time

    return {
        "total_users": total_users,
        "sent": sent_count,
        "failed": failed_count,
        "duration_seconds": duration,
    }


def _create_booking_keyboard(
    user_chat_id: int, booking_id: int, is_payment_by_cash: bool
) -> InlineKeyboardMarkup:
    """Create inline keyboard for booking management"""
    keyboard = [
        [
            InlineKeyboardButton(
                "Подтвердить оплату",
                callback_data=f"booking_1_chatid_{user_chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}",
            )
        ],
        [
            InlineKeyboardButton(
                "Отмена бронирования",
                callback_data=f"booking_2_chatid_{user_chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}",
            )
        ],
        [
            InlineKeyboardButton(
                "Изменить стоимость",
                callback_data=f"booking_3_chatid_{user_chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}",
            )
        ],
        [
            InlineKeyboardButton(
                "Изменить предоплату",
                callback_data=f"booking_4_chatid_{user_chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}",
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def _clear_edit_context(context: ContextTypes.DEFAULT_TYPE, prefix: str):
    """Clear editing context from user_data"""
    keys = [
        f"{prefix}_booking_id",
        f"{prefix}_user_chat_id",
        f"{prefix}_is_payment_by_cash",
        f"{prefix}_message_id",
    ]
    for key in keys:
        context.user_data.pop(key, None)


async def _edit_message(
    update: Update,
    message: str,
    reply_markup: InlineKeyboardMarkup,
    parse_mode: str = None,
):
    """Edit message text or caption depending on message type"""
    if update.callback_query.message.caption:
        await update.callback_query.edit_message_caption(
            caption=message, reply_markup=reply_markup, parse_mode=parse_mode
        )
    else:
        await update.callback_query.edit_message_text(
            text=message, reply_markup=reply_markup, parse_mode=parse_mode
        )


async def accept_booking_payment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    booking: BookingBase,
    user_chat_id: int,
    photo,
    document,
    is_payment_by_cash=False,
):
    user = database_service.get_user_by_id(booking.user_id)
    message = string_helper.generate_booking_info_message(
        booking, user, is_payment_by_cash
    )
    reply_markup = _create_booking_keyboard(
        user_chat_id, booking.id, is_payment_by_cash
    )

    if photo:
        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=photo,
            caption=message,
            reply_markup=reply_markup,
        )
    elif document:
        await context.bot.send_document(
            chat_id=ADMIN_CHAT_ID,
            document=document,
            caption=message,
            reply_markup=reply_markup,
        )
    else:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID, text=message, reply_markup=reply_markup
        )


async def edit_accept_booking_payment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    booking_id: int,
    user_chat_id: int,
    is_payment_by_cash,
):
    booking = database_service.get_booking_by_id(booking_id)
    user = database_service.get_user_by_id(booking.user_id)
    message = string_helper.generate_booking_info_message(
        booking, user, is_payment_by_cash
    )
    reply_markup = _create_booking_keyboard(
        user_chat_id, booking_id, is_payment_by_cash
    )
    await _edit_message(update, message, reply_markup)


async def accept_gift_payment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    gift: GiftBase,
    user_chat_id: int,
    photo,
    document,
):
    message = string_helper.generate_gift_info_message(gift)
    keyboard = [
        [
            InlineKeyboardButton(
                "Подтвердить оплату",
                callback_data=f"gift_1_chatid_{user_chat_id}_giftid_{gift.id}",
            )
        ],
        [
            InlineKeyboardButton(
                "Отмена", callback_data=f"gift_2_chatid_{user_chat_id}_giftid_{gift.id}"
            )
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if photo:
        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=photo,
            caption=message,
            reply_markup=reply_markup,
        )
    elif document:
        await context.bot.send_document(
            chat_id=ADMIN_CHAT_ID,
            document=document,
            caption=message,
            reply_markup=reply_markup,
        )


async def inform_cancel_booking(
    update: Update, context: ContextTypes.DEFAULT_TYPE, booking: BookingBase
):
    user = database_service.get_user_by_id(booking.user_id)
    message = (
        f"Отмена бронирования!\n"
        f"Контакт клиента: {user.contact}\n"
        f"Дата начала: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"Дата завершения: {booking.end_date.strftime('%d.%m.%Y %H:%M')}\n"
    )
    await context.bot.send_message(chat_id=INFORM_CHAT_ID, text=message)


async def inform_changing_booking_date(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    booking: BookingBase,
    old_start_date: date,
):
    user = database_service.get_user_by_id(booking.user_id)
    message = (
        f"Отмена бронирования!\n"
        f"Контакт клиента: {user.contact}\n"
        f"Дата: {old_start_date.strftime('%d.%m.%Y')}\n"
    )
    await context.bot.send_message(chat_id=INFORM_CHAT_ID, text=message)

    message = (
        f"Перенос даты бронирования!\n"
        f"Старая дата начала: {old_start_date.strftime('%d.%m.%Y')}\n\n"
        f"{string_helper.generate_booking_info_message(booking, user)}"
    )
    await context.bot.send_message(chat_id=INFORM_CHAT_ID, text=message)


async def booking_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = string_helper.parse_booking_callback_data(query.data)
    chat_id = data["user_chat_id"]
    booking_id = data["booking_id"]
    menu_index = data["menu_index"]
    is_payment_by_cash = data["is_payment_by_cash"]

    match menu_index:
        case "1":
            return await approve_booking(update, context, chat_id, booking_id)
        case "2":
            return await cancel_booking(update, context, chat_id, booking_id)
        case "3":
            return await request_price_input(
                update, context, chat_id, booking_id, is_payment_by_cash
            )
        case "4":
            return await request_prepayment_input(
                update, context, chat_id, booking_id, is_payment_by_cash
            )


async def gift_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = string_helper.parse_gift_callback_data(query.data)
    chat_id = data["user_chat_id"]
    gift_id = data["gift_id"]
    menu_index = data["menu_index"]

    match menu_index:
        case "1":
            await approve_gift(update, context, chat_id, gift_id)
        case "2":
            await cancel_gift(update, context, chat_id, gift_id)


async def request_price_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_chat_id: int,
    booking_id: int,
    is_payment_by_cash: bool = False,
):
    """Ask admin to enter new price via text input"""
    # Store context in user_data - including is_payment_by_cash and message_id
    context.user_data["price_edit_booking_id"] = booking_id
    context.user_data["price_edit_user_chat_id"] = user_chat_id
    context.user_data["price_edit_is_payment_by_cash"] = is_payment_by_cash
    context.user_data["price_edit_message_id"] = (
        update.callback_query.message.message_id
    )

    booking = database_service.get_booking_by_id(booking_id)
    keyboard = [[InlineKeyboardButton("Отмена", callback_data="cancel_price_input")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"📝 <b>Изменение стоимости бронирования</b>\n\n"
        f"Текущая стоимость: <b>{booking.price} руб.</b>\n\n"
        f"Введите новую стоимость цифрами (например: 370):"
    )

    await _edit_message(update, message, reply_markup, parse_mode="HTML")
    return ENTER_PRICE


async def _update_booking_message(
    context: ContextTypes.DEFAULT_TYPE,
    booking_id: int,
    user_chat_id: int,
    is_payment_by_cash: bool,
    message_id: int,
):
    """Helper function to update booking message with new data"""
    booking = database_service.get_booking_by_id(booking_id)
    user = database_service.get_user_by_id(booking.user_id)

    message_text = string_helper.generate_booking_info_message(
        booking, user, is_payment_by_cash
    )
    reply_markup = _create_booking_keyboard(
        user_chat_id, booking_id, is_payment_by_cash
    )

    # Try to edit message text first, fall back to caption if needed
    try:
        await context.bot.edit_message_text(
            chat_id=ADMIN_CHAT_ID,
            message_id=message_id,
            text=message_text,
            reply_markup=reply_markup,
        )
    except Exception:
        try:
            await context.bot.edit_message_caption(
                chat_id=ADMIN_CHAT_ID,
                message_id=message_id,
                caption=message_text,
                reply_markup=reply_markup,
            )
        except Exception as e:
            LoggerService.error(__name__, f"Failed to update booking message: {e}")


async def handle_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle price input from admin"""
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return END

    booking_id = context.user_data.get("price_edit_booking_id")
    if not booking_id:
        return END

    price_text = update.message.text.strip()

    # Validate input
    try:
        new_price = float(price_text)
        if new_price <= 0:
            await update.message.reply_text(
                "❌ Стоимость должна быть положительным числом."
            )
            return ENTER_PRICE
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат. Введите число (например: 370):"
        )
        return ENTER_PRICE

    # Update booking
    database_service.update_booking(booking_id, price=new_price)
    await update.message.reply_text(f"✅ Стоимость изменена на {new_price} руб.")

    # Update original message
    await _update_booking_message(
        context,
        booking_id,
        context.user_data.get("price_edit_user_chat_id"),
        context.user_data.get("price_edit_is_payment_by_cash"),
        context.user_data.get("price_edit_message_id"),
    )

    # Clear context
    _clear_edit_context(context, "price_edit")
    return END


async def cancel_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel price input and return to booking menu"""
    await update.callback_query.answer()

    booking_id = context.user_data.get("price_edit_booking_id")
    user_chat_id = context.user_data.get("price_edit_user_chat_id")
    is_payment_by_cash = context.user_data.get("price_edit_is_payment_by_cash")

    if booking_id:
        booking = database_service.get_booking_by_id(booking_id)
        await accept_booking_payment(
            update, context, booking, user_chat_id, None, None, is_payment_by_cash
        )

    # Clear context
    _clear_edit_context(context, "price_edit")
    return END


async def request_prepayment_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_chat_id: int,
    booking_id: int,
    is_payment_by_cash: bool = False,
):
    """Ask admin to enter new prepayment via text input"""
    # Store context in user_data - including is_payment_by_cash and message_id
    context.user_data["prepay_edit_booking_id"] = booking_id
    context.user_data["prepay_edit_user_chat_id"] = user_chat_id
    context.user_data["prepay_edit_is_payment_by_cash"] = is_payment_by_cash
    context.user_data["prepay_edit_message_id"] = (
        update.callback_query.message.message_id
    )

    booking = database_service.get_booking_by_id(booking_id)
    keyboard = [
        [InlineKeyboardButton("Отмена", callback_data="cancel_prepayment_input")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"📝 <b>Изменение предоплаты</b>\n\n"
        f"Текущая предоплата: <b>{booking.prepayment_price} руб.</b>\n\n"
        f"Введите новую сумму предоплаты цифрами (например: 150):"
    )

    await _edit_message(update, message, reply_markup, parse_mode="HTML")
    return ENTER_PREPAYMENT


async def handle_prepayment_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle prepayment input from admin"""
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return END

    booking_id = context.user_data.get("prepay_edit_booking_id")
    if not booking_id:
        return END

    prepayment_text = update.message.text.strip()

    # Validate input
    try:
        new_prepayment = float(prepayment_text)
        if new_prepayment < 0:
            await update.message.reply_text(
                "❌ Предоплата не может быть отрицательной."
            )
            return ENTER_PREPAYMENT
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат. Введите число (например: 150):"
        )
        return ENTER_PREPAYMENT

    # Update booking
    database_service.update_booking(booking_id, prepayment=new_prepayment)
    await update.message.reply_text(f"✅ Предоплата изменена на {new_prepayment} руб.")

    # Update original message
    await _update_booking_message(
        context,
        booking_id,
        context.user_data.get("prepay_edit_user_chat_id"),
        context.user_data.get("prepay_edit_is_payment_by_cash"),
        context.user_data.get("prepay_edit_message_id"),
    )

    # Clear context
    _clear_edit_context(context, "prepay_edit")
    return END


async def cancel_prepayment_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel prepayment input and return to booking menu"""
    await update.callback_query.answer()

    booking_id = context.user_data.get("prepay_edit_booking_id")
    user_chat_id = context.user_data.get("prepay_edit_user_chat_id")
    is_payment_by_cash = context.user_data.get("prepay_edit_is_payment_by_cash")

    if booking_id:
        booking = database_service.get_booking_by_id(booking_id)
        await accept_booking_payment(
            update, context, booking, user_chat_id, None, None, is_payment_by_cash
        )

    # Clear context
    _clear_edit_context(context, "prepay_edit")
    return END


async def approve_booking(
    update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, booking_id: int
):
    (booking, user) = await prepare_approve_process(update, context, booking_id)
    await check_and_send_booking(context, booking)
    # Prepare confirmation message
    confirmation_text = (
        "🎉 <b>Отличные новости!</b> 🎉\n"
        "✅ <b>Ваше бронирование подтверждено администратором.</b>\n"
        "📩 За 1 день до заезда вы получите сообщение с деталями бронирования и инструкцией по заселению.\n"
        f"Общая стоимость бронирования: {booking.price} руб.\n"
        f"Предоплата: {booking.prepayment_price} руб.\n"
    )

    # Add transfer time information if transfer is requested
    if booking.transfer_address:
        # Transfer time is 30 minutes before check-in time
        transfer_time = booking.start_date - timedelta(minutes=30)
        confirmation_text += f"🚗 <b>Трансфер:</b> {booking.transfer_address}\n"
        confirmation_text += (
            f"🕐 <b>Время трансфера:</b> {transfer_time.strftime('%d.%m.%Y %H:%M')}\n"
        )

    await context.bot.send_message(
        chat_id=chat_id,
        text=confirmation_text,
        parse_mode="HTML",
    )

    text = f"Подтверждено ✅\n\n{string_helper.generate_booking_info_message(booking, user)}"
    message = update.callback_query.message
    if message.caption:
        await message.edit_caption(text)
    else:
        await message.edit_text(text)

    return END


async def cancel_booking(
    update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, booking_id: int
):
    booking = database_service.update_booking(booking_id, is_canceled=True)
    await context.bot.send_message(
        chat_id=chat_id,
        text="⚠️ <b>Внимание!</b> ⚠️\n"
        "❌ <b>Ваше бронирование отменено.</b>\n"
        "📞 Администратор свяжется с вами для уточнения деталей.",
        parse_mode="HTML",
    )
    user = database_service.get_user_by_id(booking.user_id)

    text = f"Отмена.\n\n {string_helper.generate_booking_info_message(booking, user)}"
    message = update.callback_query.message
    if message.caption:
        await message.edit_caption(text)
    else:
        await message.edit_text(text)
    return END


async def approve_gift(
    update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, gift_id: int
):
    gift = database_service.update_gift(gift_id, is_paymented=True)
    await context.bot.send_message(chat_id=chat_id, text=f"{gift.code}")

    await context.bot.send_message(
        chat_id=chat_id,
        text="🎉 <b>Отличные новости!</b> 🎉\n"
        "✅ <b>Ваш подарочный сертификат подтвержден администратором.</b>\n"
        "📩 <b>В течение нескольких часов мы отправим вам электронный сертификат.</b>\n"
        "🔑 <b>Мы также отправили код сертификата — укажите его при бронировании.</b>",
        parse_mode="HTML",
    )
    await update.callback_query.edit_message_caption(
        f"Подтверждено \n\n{string_helper.generate_gift_info_message(gift)}"
    )
    return END


async def cancel_gift(
    update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, gift_id: int
):
    gift = database_service.get_gift_by_id(gift_id)
    await context.bot.send_message(
        chat_id=chat_id,
        text="⚠️ <b>Внимание!</b> ⚠️\n"
        "❌ <b>Ваша покупка подарочного сертификата была отменена.</b>\n"
        "📞 Администратор свяжется с вами для уточнения деталей.\n",
        parse_mode="HTML",
    )
    await update.callback_query.edit_message_caption(
        f"Отмена.\n\n {string_helper.generate_gift_info_message(gift)}"
    )
    return END


def get_future_bookings() -> Sequence[BookingBase]:
    today = date.today()
    max_date_booking = today + relativedelta(months=PERIOD_IN_MONTHS)
    booking_list = database_service.get_booking_by_period(today, max_date_booking, True)
    return booking_list


async def prepare_approve_process(
    update: Update, context: ContextTypes.DEFAULT_TYPE, booking_id: int
):
    booking = database_service.get_booking_by_id(booking_id)
    user = database_service.get_user_by_id(booking.user_id)
    calendar_event_id = calendar_service.add_event(booking, user)
    price = booking.price
    booking = database_service.update_booking(
        booking_id,
        price=price,
        is_prepaymented=True,
        calendar_event_id=calendar_event_id,
    )
    await inform_message(update, context, booking, user)
    return (booking, user)


def check_gift(booking: BookingBase, user: UserBase):
    if not booking.gift_id:
        return

    gift = database_service.update_gift(booking.gift_id, is_done=True, user_id=user.id)
    return gift


async def inform_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    booking: BookingBase,
    user: UserBase,
):
    message = string_helper.generate_booking_info_message(booking, user)
    await context.bot.send_message(chat_id=INFORM_CHAT_ID, text=message)


async def send_booking_details(
    context: ContextTypes.DEFAULT_TYPE, booking: BookingBase
):
    try:
        # Отправка маршрута
        await context.bot.send_message(
            chat_id=booking.user.chat_id,
            text="Мы отобразили путь по которому лучше всего доехать до The Secret House.\n"
            "Через 500 метров после ж/д переезда по левую сторону будет оранжевый магазин. После магазина нужно повернуть налево. Это Вам ориентир нужного поворота, далее навигатор Вас привезет правильно.\n"
            "Когда будете ехать вдоль леса, то Вам нужно будет повернуть на садовое товарищество 'Юбилейное-68' (будет вывеска).\n"
            "ст. Юбилейное-68, ул. Сосновая, д. 2\n\n"
            "Маршрут в Yandex map:\n"
            "https://yandex.com.ge/maps/157/minsk/?l=stv%2Csta&ll=27.297381%2C53.932145&mode=routes&rtext=53.939763%2C27.333107~53.938194%2C27.324665~53.932431%2C27.315410~53.930789%2C27.299320~53.934190%2C27.300387&rtt=auto&ruri=~~~~ymapsbm1%3A%2F%2Fgeo%3Fdata%3DCgo0Mzk0MjMwMTgwErMB0JHQtdC70LDRgNGD0YHRjCwg0JzRltC90YHQutGWINGA0LDRkdC9LCDQltC00LDQvdC-0LLRltGG0LrRliDRgdC10LvRjNGB0LDQstC10YIsINGB0LDQtNCw0LLQvtC00YfQsNC1INGC0LDQstCw0YDRi9GB0YLQstCwINCu0LHRltC70LXQudC90LDQtS02OCwg0KHQsNGB0L3QvtCy0LDRjyDQstGD0LvRltGG0LAsIDIiCg0sZ9pBFZ28V0I%2C&z=16.06 \n\n"
            "Маршрут Google map:\n"
            "https://maps.app.goo.gl/Hsf9Xw69N8tqHyqt5",
        )

        # Отправка контактов администратора
        await context.bot.send_message(
            chat_id=booking.user.chat_id,
            text="Если Вам нужна будет какая-то помощь или будут вопросы как добраться до дома, то Вы можете связаться с администратором.\n\n"
            f"{ADMINISTRATION_CONTACT}",
        )

        # Отправка фото с инструкциями
        photo = file_service.get_image("key.jpg")
        await context.bot.send_photo(
            chat_id=booking.user.chat_id,
            caption="Мы предоставляем самостоятельное заселение.\n"
            f"1. Слева отображена ключница, которая располагается за территорией дома. В которой лежат ключи от ворот и дома. Пароль: {settings_service.password}\n"
            "2. Справа отображен ящик, который располагается на территории дома. В ящик нужно положить подписанный договор и оплату за проживание, если вы платите наличкой.\n\n"
            "Попрошу это сделать в первые 30 мин. Вашего пребывания в The Secret House. Администратор заберет договор и деньги."
            "Договор и ручка будут лежать в дома на острове на кухне. Вложите деньги и договор с розовый конверт.\n\n"
            "Информация для оплаты (Альфа-Банк):\n"
            f"по номеру телефона через Альфа-Банк {BANK_PHONE_NUMBER}. Обращаем внимание, что предоплату не нужно переводить на счёт мобильного оператора Лайф.\n"
            "или\n"
            f"по номеру карты {BANK_CARD_NUMBER}",
            photo=photo,
        )

        # Отправка инструкций по сауне (если есть)
        if booking.has_sauna:
            await context.bot.send_message(
                chat_id=booking.user.chat_id,
                text="Инструкция по включению сауны:\n"
                "1. Подойдите к входной двери.\n"
                "2. По правую руку находился электрический счетчик.\n"
                "3. Все рубильники подписаны. Переключите рубильник с надписей «Сауна».\n"
                "4. Через 1 час сауна нагреется.\n"
                "5. После использования выключите рубильник.\n",
            )

        LoggerService.info(
            __name__,
            "All booking details sent successfully",
            kwargs={
                "chat_id": booking.user.chat_id,
                "booking_id": booking.id,
                "action": "send_booking_details_complete",
            },
        )

    except TelegramError as e:
        LoggerService.error(
            __name__,
            "Failed to send booking details to user",
            exception=e,
            kwargs={
                "chat_id": booking.user.chat_id,
                "booking_id": booking.id,
                "action": "send_booking_details",
            },
        )
        raise


async def send_feedback(context: ContextTypes.DEFAULT_TYPE, booking: BookingBase):
    """Modified to trigger feedback conversation instead of sending Google Forms link"""
    try:
        # Create inline button to start feedback conversation
        keyboard = [
            [
                InlineKeyboardButton(
                    "📝 Оставить отзыв", callback_data=f"START_FEEDBACK_{booking.id}"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = await context.bot.send_message(
            chat_id=booking.user.chat_id,
            text="🏡 <b>The Secret House благодарит вас за выбор нашего дома для аренды!</b> 💫\n\n"
            "Мы хотели бы узнать, как Вам понравилось наше обслуживание. "
            "Будем благодарны, если вы оставите отзыв.\n\n"
            "После получения фидбека мы дарим Вам <b>10% скидки</b> для следующей поездки.",
            parse_mode="HTML",
            reply_markup=reply_markup,
        )

        LoggerService.info(
            __name__,
            "Feedback request sent successfully",
            kwargs={
                "chat_id": booking.user.chat_id,
                "booking_id": booking.id,
                "message_id": message.message_id,
                "action": "send_feedback",
            },
        )

    except Exception as e:
        LoggerService.error(
            __name__,
            "Failed to send feedback request to user",
            exception=e,
            kwargs={
                "chat_id": booking.user.chat_id,
                "booking_id": booking.id,
                "action": "send_feedback",
            },
        )
        raise


async def check_and_send_booking(context, booking):
    now = datetime.now()
    job_run_time = time(8, 0)

    condition_1 = (
        booking.start_date.date() == now.date()
        or booking.start_date.date() == now.date() + timedelta(days=1)
    )
    condition_2 = (
        booking.start_date.date() == now.date()
        or booking.start_date.date() - timedelta(days=1) == now.date()
    ) and booking.start_date.time() < job_run_time

    if condition_1 or condition_2:
        await send_booking_details(context, booking)
