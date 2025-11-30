from datetime import date, datetime, time, timedelta
import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from telegram_bot.client.backend_api import BackendAPIClient, APIError
from telegram_bot.services.logger_service import LoggerService
from telegram_bot.decorators.callback_error_handler import safe_callback_query
from telegram_bot.services.navigation_service import NavigationService
from telegram_bot.services.settings_service import SettingsService
from telegram_bot.services.file_service import FileService
from telegram_bot.services.calculation_rate_service import CalculationRateService
from matplotlib.dates import relativedelta
from telegram_bot.constants import (
    END,
    SET_PASSWORD,
    ENTER_PRICE,
    ENTER_PREPAYMENT,
    BROADCAST_INPUT,
    CREATE_PROMO_NAME,
    CREATE_PROMO_DATE_FROM,
    CREATE_PROMO_DATE_TO,
    CREATE_PROMO_DISCOUNT,
    CREATE_PROMO_TARIFF,
)
from telegram_bot.services.calendar_service import CalendarService
from backend.models.enum.tariff import Tariff
import logging

logger = logging.getLogger(__name__)
from telegram_bot.config.config import (
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
from telegram_bot.helpers import string_helper, tariff_helper

calendar_service = CalendarService()
calculation_rate_service = CalculationRateService()
file_service = FileService()
settings_service = SettingsService()
navigation_service = NavigationService()


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


@safe_callback_query()
async def cancel_password_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel password change"""
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("❌ Изменение пароля отменено.")

    # Clear context
    context.user_data.pop("old_password", None)

    return END


async def _get_booking_list_data():
    """Get booking list data (bookings, keyboard, message) - shared logic"""
    # Get future bookings
    future_bookings = await get_future_bookings()

    # Get unpaid bookings (waiting for admin confirmation)
    api_client = BackendAPIClient()
    try:
        unpaid_bookings = await api_client.get_unpaid_bookings()
    except APIError as e:
        logger.error(f"Failed to get unpaid bookings: {e}")
        unpaid_bookings = []
    
    # Combine and deduplicate by booking ID
    all_bookings_dict = {}
    for booking in future_bookings:
        all_bookings_dict[booking.id] = booking
    for booking in unpaid_bookings:
        all_bookings_dict[booking.id] = booking
    
    bookings = list(all_bookings_dict.values())
    
    # Sort by start_date
    bookings.sort(key=lambda b: b.start_date)

    if not bookings:
        return None, None, None

    # Telegram limit: max 100 buttons
    bookings = bookings[:100]

    # Create inline keyboard (max 8 buttons per row, 1 per row for readability)
    keyboard = []
    for booking in bookings:
        label = string_helper.format_booking_button_label(booking)
        api_client = BackendAPIClient()
    try:
        user = await api_client.get_user_by_id(booking["user_id"] if isinstance(booking, dict) else booking.user_id)
    except APIError as e:
        logger.error(f"Failed to get user: {e}")
        user = None
        # Add user contact to button for context
        # Handle case when user is None
        user_contact = user.contact if user and user.contact else "N/A"
        # Add emoji for canceled bookings
        cancel_emoji = "❌ " if booking.is_canceled else ""
        # Add emoji for unpaid bookings (waiting for confirmation)
        unpaid_emoji = "⏳ " if not booking.is_prepaymented and not booking.is_canceled else ""
        button_text = f"{cancel_emoji}{unpaid_emoji}{label} - {user_contact}"
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"MBD_{booking.id}")
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"📋 <b>Управление бронированиями</b>\n\n"
        f"Всего активных броней: {len(bookings)}\n"
        f"⏳ - ожидают подтверждения\n"
        f"❌ - отменены\n"
        f"Выберите бронирование для просмотра и управления:"
    )

    return bookings, reply_markup, message


async def get_booking_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to show all future bookings and unpaid bookings as inline buttons"""
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
        return END

    bookings, reply_markup, message = await _get_booking_list_data()

    if not bookings:
        await update.message.reply_text("🔍 Не найдено активных бронирований.")
        return END

    await update.message.reply_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    LoggerService.info(__name__, "Admin opened booking management list", update)
    return END


@safe_callback_query()
async def back_to_booking_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to booking list from detail view"""
    await update.callback_query.answer()

    bookings, reply_markup, message = await _get_booking_list_data()

    if not bookings:
        await update.callback_query.edit_message_text("🔍 Не найдено активных бронирований.")
        return END

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
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
        from telegram_bot.services.statistics_service import StatisticsService
        from telegram_bot.helpers.statistics_helper import format_statistics_message

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
        api_client_chat = BackendAPIClient()
        try:
            users = await api_client_chat.get_all_users()
            chat_ids = [u["chat_id"] for u in users if u.get("chat_id")]
        except APIError as e:
            logger.error(f"Failed to get user chat IDs: {e}")
            chat_ids = []
        filter_label = "всем пользователям"
    elif filter_type == "with_bookings":
        api_client_with = BackendAPIClient()
        try:
            chat_ids = await api_client_with.get_user_chat_ids_with_bookings()
        except APIError as e:
            logger.error(f"Failed to get user chat IDs with bookings: {e}")
            chat_ids = []
        filter_label = "пользователям С бронями"
    elif filter_type == "without_bookings":
        api_client_without = BackendAPIClient()
        try:
            chat_ids = await api_client_without.get_user_chat_ids_without_bookings()
        except APIError as e:
            logger.error(f"Failed to get user chat IDs without bookings: {e}")
            chat_ids = []
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
        api_client_chat = BackendAPIClient()
        try:
            users = await api_client_chat.get_all_users()
            chat_ids = [u["chat_id"] for u in users if u.get("chat_id")]
        except APIError as e:
            logger.error(f"Failed to get user chat IDs: {e}")
            chat_ids = []
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


@safe_callback_query()
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
    api_client = BackendAPIClient()
    try:
        user = await api_client.get_user_by_id(booking["user_id"] if isinstance(booking, dict) else booking.user_id)
    except APIError as e:
        logger.error(f"Failed to get user: {e}")
        user = None
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
    api_client = BackendAPIClient()
    try:
        booking = await api_client.get_booking(booking_id)
    except APIError as e:
        logger.error(f"Failed to get booking: {e}")
        booking = None
    api_client = BackendAPIClient()
    try:
        user = await api_client.get_user_by_id(booking["user_id"] if isinstance(booking, dict) else booking.user_id)
    except APIError as e:
        logger.error(f"Failed to get user: {e}")
        user = None
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
    api_client = BackendAPIClient()
    try:
        user = await api_client.get_user_by_id(booking["user_id"] if isinstance(booking, dict) else booking.user_id)
    except APIError as e:
        logger.error(f"Failed to get user: {e}")
        user = None
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
    api_client = BackendAPIClient()
    try:
        user = await api_client.get_user_by_id(booking["user_id"] if isinstance(booking, dict) else booking.user_id)
    except APIError as e:
        logger.error(f"Failed to get user: {e}")
        user = None
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

    api_client = BackendAPIClient()
    try:
        booking = await api_client.get_booking(booking_id)
    except APIError as e:
        logger.error(f"Failed to get booking: {e}")
        booking = None
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
    api_client = BackendAPIClient()
    try:
        booking = await api_client.get_booking(booking_id)
    except APIError as e:
        logger.error(f"Failed to get booking: {e}")
        booking = None
    api_client = BackendAPIClient()
    try:
        user = await api_client.get_user_by_id(booking["user_id"] if isinstance(booking, dict) else booking.user_id)
    except APIError as e:
        logger.error(f"Failed to get user: {e}")
        user = None

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
    api_client = BackendAPIClient()
    try:
        await api_client.update_booking(booking_id, {"price": new_price})
    except APIError as e:
        logger.error(f"Failed to update booking price: {e}")
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


@safe_callback_query()
async def cancel_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel price input and return to booking menu"""
    await update.callback_query.answer()

    booking_id = context.user_data.get("price_edit_booking_id")
    user_chat_id = context.user_data.get("price_edit_user_chat_id")
    is_payment_by_cash = context.user_data.get("price_edit_is_payment_by_cash")

    if booking_id:
        api_client = BackendAPIClient()
    try:
        booking = await api_client.get_booking(booking_id)
    except APIError as e:
        logger.error(f"Failed to get booking: {e}")
        booking = None
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

    api_client = BackendAPIClient()
    try:
        booking = await api_client.get_booking(booking_id)
    except APIError as e:
        logger.error(f"Failed to get booking: {e}")
        booking = None
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
    api_client = BackendAPIClient()
    try:
        await api_client.update_booking(booking_id, {"prepayment": new_prepayment})
    except APIError as e:
        logger.error(f"Failed to update booking prepayment: {e}")
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


@safe_callback_query()
async def cancel_prepayment_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel prepayment input and return to booking menu"""
    await update.callback_query.answer()

    booking_id = context.user_data.get("prepay_edit_booking_id")
    user_chat_id = context.user_data.get("prepay_edit_user_chat_id")
    is_payment_by_cash = context.user_data.get("prepay_edit_is_payment_by_cash")

    if booking_id:
        api_client = BackendAPIClient()
    try:
        booking = await api_client.get_booking(booking_id)
    except APIError as e:
        logger.error(f"Failed to get booking: {e}")
        booking = None
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
    api_client = BackendAPIClient()
    try:
        booking = await api_client.cancel_booking(booking_id)
    except APIError as e:
        logger.error(f"Failed to cancel booking: {e}")
        booking = None
    await context.bot.send_message(
        chat_id=chat_id,
        text="⚠️ <b>Внимание!</b> ⚠️\n"
        "❌ <b>Ваше бронирование отменено.</b>\n"
        "📞 Администратор свяжется с вами для уточнения деталей.",
        parse_mode="HTML",
    )
    api_client = BackendAPIClient()
    try:
        user = await api_client.get_user_by_id(booking["user_id"] if isinstance(booking, dict) else booking.user_id)
    except APIError as e:
        logger.error(f"Failed to get user: {e}")
        user = None

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
    api_client = BackendAPIClient()
    try:
        gift = await api_client.update_gift(gift_id, {"is_paymented": True, "is_done": True})
        await context.bot.send_message(chat_id=chat_id, text=f"{gift['code']}")
    except APIError as e:
        logger.error(f"Failed to update gift: {e}")
        return END

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
    api_client = BackendAPIClient()
    try:
        gift = await api_client.get_gift_by_id(gift_id)
    except APIError as e:
        logger.error(f"Failed to get gift: {e}")
        return END
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


async def get_future_bookings():
    today = date.today()
    max_date_booking = today + relativedelta(months=PERIOD_IN_MONTHS)
    api_client = BackendAPIClient()
    try:
        booking_list = await api_client.get_bookings_by_date_range(
            today.isoformat(), max_date_booking.isoformat(), is_paid=True
        )
        return booking_list
    except APIError as e:
        logger.error(f"Failed to get future bookings: {e}")
        return []


async def prepare_approve_process(
    update: Update, context: ContextTypes.DEFAULT_TYPE, booking_id: int
):
    api_client = BackendAPIClient()
    try:
        booking = await api_client.get_booking(booking_id)
    except APIError as e:
        logger.error(f"Failed to get booking: {e}")
        booking = None
    api_client = BackendAPIClient()
    try:
        user = await api_client.get_user_by_id(booking["user_id"] if isinstance(booking, dict) else booking.user_id)
    except APIError as e:
        logger.error(f"Failed to get user: {e}")
        user = None
    calendar_event_id = calendar_service.add_event(booking, user)
    price = booking["price"] if isinstance(booking, dict) else booking.price
    api_client_update = BackendAPIClient()
    try:
        booking = await api_client_update.update_booking(
            booking_id,
            {
                "price": price,
                "is_prepaymented": True,
                "calendar_event_id": calendar_event_id,
            }
        )
    except APIError as e:
        logger.error(f"Failed to update booking: {e}")
        return
    await inform_message(update, context, booking, user)
    return (booking, user)


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
    # Проверка наличия chat_id у пользователя
    if not booking.user or not booking.user.chat_id:
        LoggerService.warning(
            __name__,
            "Cannot send booking details: user or chat_id is missing",
            kwargs={
                "booking_id": booking.id,
                "user_id": booking.user_id if booking.user else None,
                "has_user": booking.user is not None,
                "chat_id": booking.user.chat_id if booking.user else None,
                "action": "send_booking_details_skipped",
            },
        )
        return

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


# ============== PROMOCODE CREATION HANDLERS ==============


async def create_promocode_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start promo code creation flow (admin only)"""
    chat_id = update.effective_chat.id

    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
        return END

    context.user_data["creating_promocode"] = {}

    keyboard = [[InlineKeyboardButton("Отмена", callback_data="cancel_promo_create")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "📝 <b>Создание промокода</b>\n\n"
        "Шаг 1 из 5: Введите название промокода\n"
        "(только латинские буквы, цифры и дефис, макс. 50 символов)\n\n"
        "Пример: SUMMER2024"
    )

    await update.message.reply_text(
        text=message, reply_markup=reply_markup, parse_mode="HTML"
    )

    LoggerService.info(__name__, "Promocode creation started", update)
    return CREATE_PROMO_NAME


async def handle_promo_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle promo code name input"""
    if not update.message or not update.message.text:
        return CREATE_PROMO_NAME

    promo_name = update.message.text.strip().upper()

    # Validate format
    import re

    if not re.match(r"^[A-Z0-9\-]{1,50}$", promo_name):
        await update.message.reply_text(
            "❌ Неверный формат! Используйте только латинские буквы, цифры и дефис (макс. 50 символов).\n\n"
            "Попробуйте снова:",
            parse_mode="HTML",
        )
        return CREATE_PROMO_NAME

    # Check if already exists
    api_client = BackendAPIClient()
    try:
        existing = await api_client.get_promocode_by_name(promo_name)
    except APIError as e:
        logger.error(f"Failed to check promocode: {e}")
        existing = None
    if existing:
        await update.message.reply_text(
            f"❌ Промокод <b>{promo_name}</b> уже существует!\n\n"
            "Введите другое название:",
            parse_mode="HTML",
        )
        return CREATE_PROMO_NAME

    context.user_data["creating_promocode"]["name"] = promo_name

    keyboard = [[InlineKeyboardButton("Отмена", callback_data="cancel_promo_create")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"✅ Название: <b>{promo_name}</b>\n\n"
        "Шаг 2 из 5: Введите дату начала действия\n"
        "Формат: ДД.ММ.ГГГГ\n\n"
        f"Пример: {date.today().strftime('%d.%m.%Y')}"
    )

    await update.message.reply_text(
        text=message, reply_markup=reply_markup, parse_mode="HTML"
    )

    LoggerService.info(
        __name__, "Promo name set", update, kwargs={"promo_name": promo_name}
    )
    return CREATE_PROMO_DATE_FROM


async def handle_promo_date_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle start date input"""
    if not update.message or not update.message.text:
        return CREATE_PROMO_DATE_FROM

    date_str = update.message.text.strip()

    # Parse date
    try:
        date_from = datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат даты!\n\n"
            "Используйте формат ДД.ММ.ГГГГ, например: 01.12.2024\n\n"
            "Попробуйте снова:",
            parse_mode="HTML",
        )
        return CREATE_PROMO_DATE_FROM

    # Validate date is not in the past
    if date_from < date.today():
        await update.message.reply_text(
            "❌ Дата начала не может быть в прошлом!\n\n"
            "Введите дату сегодня или в будущем:",
            parse_mode="HTML",
        )
        return CREATE_PROMO_DATE_FROM

    context.user_data["creating_promocode"]["date_from"] = date_from

    keyboard = [[InlineKeyboardButton("Отмена", callback_data="cancel_promo_create")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"✅ Дата начала: <b>{date_from.strftime('%d.%m.%Y')}</b>\n\n"
        "Шаг 3 из 5: Введите дату окончания действия\n"
        "Формат: ДД.ММ.ГГГГ\n\n"
        f"Пример: {date.today().strftime('%d.%m.%Y')}"
    )

    await update.message.reply_text(
        text=message, reply_markup=reply_markup, parse_mode="HTML"
    )

    LoggerService.info(
        __name__, "Promo date_from set", update, kwargs={"date_from": date_from}
    )
    return CREATE_PROMO_DATE_TO


async def handle_promo_date_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle end date input"""
    if not update.message or not update.message.text:
        return CREATE_PROMO_DATE_TO

    date_str = update.message.text.strip()

    # Parse date
    try:
        date_to = datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат даты!\n\n"
            "Используйте формат ДД.ММ.ГГГГ, например: 31.12.2024\n\n"
            "Попробуйте снова:",
            parse_mode="HTML",
        )
        return CREATE_PROMO_DATE_TO

    date_from = context.user_data["creating_promocode"]["date_from"]

    # Validate date_to >= date_from
    if date_to < date_from:
        await update.message.reply_text(
            f"❌ Дата окончания не может быть раньше даты начала "
            f"(<b>{date_from.strftime('%d.%m.%Y')}</b>)!\n\n"
            "Введите дату окончания:",
            parse_mode="HTML",
        )
        return CREATE_PROMO_DATE_TO

    context.user_data["creating_promocode"]["date_to"] = date_to

    keyboard = [[InlineKeyboardButton("Отмена", callback_data="cancel_promo_create")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"✅ Дата окончания: <b>{date_to.strftime('%d.%m.%Y')}</b>\n\n"
        "Шаг 4 из 5: Введите размер скидки в процентах\n"
        "Пример: 10 (для скидки 10%)\n\n"
        "Диапазон: 1-100"
    )

    await update.message.reply_text(
        text=message, reply_markup=reply_markup, parse_mode="HTML"
    )

    LoggerService.info(
        __name__, "Promo date_to set", update, kwargs={"date_to": date_to}
    )
    return CREATE_PROMO_DISCOUNT


async def handle_promo_discount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle discount percentage input"""
    if not update.message or not update.message.text:
        return CREATE_PROMO_DISCOUNT

    discount_str = update.message.text.strip()

    # Parse discount
    try:
        discount = float(discount_str)
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат!\n\n"
            "Введите число от 1 до 100, например: 15\n\n"
            "Попробуйте снова:",
            parse_mode="HTML",
        )
        return CREATE_PROMO_DISCOUNT

    # Validate range
    if not (1 <= discount <= 100):
        await update.message.reply_text(
            "❌ Скидка должна быть от 1% до 100%!\n\nВведите корректное значение:",
            parse_mode="HTML",
        )
        return CREATE_PROMO_DISCOUNT

    context.user_data["creating_promocode"]["discount"] = discount

    # Show tariff selection
    keyboard = []
    keyboard.append(
        [InlineKeyboardButton("✅ ВСЕ ТАРИФЫ", callback_data="promo_tariff_ALL")]
    )

    # Add individual tariffs
    for tariff in Tariff:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"📋 {tariff.name}", callback_data=f"promo_tariff_{tariff.value}"
                )
            ]
        )

    keyboard.append(
        [InlineKeyboardButton("Отмена", callback_data="cancel_promo_create")]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"✅ Скидка: <b>{discount}%</b>\n\n"
        "Шаг 5 из 5: Выберите тарифы, к которым применим промокод\n\n"
        "Нажмите <b>ВСЕ ТАРИФЫ</b> для применения ко всем тарифам,\n"
        "или выберите конкретный тариф:"
    )

    await update.message.reply_text(
        text=message, reply_markup=reply_markup, parse_mode="HTML"
    )

    LoggerService.info(
        __name__, "Promo discount set", update, kwargs={"discount": discount}
    )
    return CREATE_PROMO_TARIFF


async def handle_promo_tariff_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle tariff selection"""
    await update.callback_query.answer()

    data = update.callback_query.data

    if data == "cancel_promo_create":
        return await cancel_promo_creation(update, context)

    # Parse tariff selection
    tariff_selection = data.replace("promo_tariff_", "")

    promo_data = context.user_data["creating_promocode"]

    # Determine applicable tariffs
    if tariff_selection == "ALL":
        applicable_tariffs = None  # None = all tariffs
        tariff_text = "ВСЕ ТАРИФЫ"
    else:
        applicable_tariffs = [int(tariff_selection)]
        tariff_name = Tariff(int(tariff_selection)).name
        tariff_text = tariff_name

    # Create promocode in database
    try:
        api_client = BackendAPIClient()
        promocode = await api_client.create_promocode({
            "name": promo_data["name"],
            "date_from": promo_data["date_from"].isoformat(),
            "date_to": promo_data["date_to"].isoformat(),
            "discount_percentage": promo_data["discount"],
            "applicable_tariffs": applicable_tariffs,
        })

        from datetime import datetime
        date_from = datetime.fromisoformat(promocode["date_from"])
        date_to = datetime.fromisoformat(promocode["date_to"])

        message = (
            "✅ <b>Промокод успешно создан!</b>\n\n"
            f"📝 <b>Название:</b> {promocode['name']}\n"
            f"📅 <b>Период:</b> {date_from.strftime('%d.%m.%Y')} - {date_to.strftime('%d.%m.%Y')}\n"
            f"💰 <b>Скидка:</b> {promocode['discount_percentage']}%\n"
            f"🎯 <b>Тарифы:</b> {tariff_text}\n"
        )

        await update.callback_query.edit_message_text(text=message, parse_mode="HTML")

        LoggerService.info(
            __name__,
            "Promocode created successfully",
            update,
            kwargs={"promocode_id": promocode["id"], "name": promocode["name"]},
        )

    except Exception as e:
        await update.callback_query.edit_message_text(
            text=f"❌ Ошибка при создании промокода: {str(e)}", parse_mode="HTML"
        )
        LoggerService.error(__name__, "Error creating promocode", e)

    # Clear context
    context.user_data.pop("creating_promocode", None)

    return END


@safe_callback_query()
async def cancel_promo_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel promocode creation"""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="❌ Создание промокода отменено.", parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text="❌ Создание промокода отменено.", parse_mode="HTML"
        )

    context.user_data.pop("creating_promocode", None)
    LoggerService.info(__name__, "Promocode creation cancelled", update)

    return END


def get_create_promocode_handler() -> ConversationHandler:
    """Returns ConversationHandler for /create_promocode command"""
    handler = ConversationHandler(
        entry_points=[CommandHandler("create_promocode", create_promocode_start)],
        states={
            CREATE_PROMO_NAME: [
                MessageHandler(
                    filters.Chat(chat_id=ADMIN_CHAT_ID)
                    & filters.TEXT
                    & ~filters.COMMAND,
                    handle_promo_name,
                ),
                CallbackQueryHandler(
                    cancel_promo_creation, pattern="^cancel_promo_create$"
                ),
            ],
            CREATE_PROMO_DATE_FROM: [
                MessageHandler(
                    filters.Chat(chat_id=ADMIN_CHAT_ID)
                    & filters.TEXT
                    & ~filters.COMMAND,
                    handle_promo_date_from,
                ),
                CallbackQueryHandler(
                    cancel_promo_creation, pattern="^cancel_promo_create$"
                ),
            ],
            CREATE_PROMO_DATE_TO: [
                MessageHandler(
                    filters.Chat(chat_id=ADMIN_CHAT_ID)
                    & filters.TEXT
                    & ~filters.COMMAND,
                    handle_promo_date_to,
                ),
                CallbackQueryHandler(
                    cancel_promo_creation, pattern="^cancel_promo_create$"
                ),
            ],
            CREATE_PROMO_DISCOUNT: [
                MessageHandler(
                    filters.Chat(chat_id=ADMIN_CHAT_ID)
                    & filters.TEXT
                    & ~filters.COMMAND,
                    handle_promo_discount,
                ),
                CallbackQueryHandler(
                    cancel_promo_creation, pattern="^cancel_promo_create$"
                ),
            ],
            CREATE_PROMO_TARIFF: [
                CallbackQueryHandler(
                    handle_promo_tariff_selection,
                    pattern="^promo_tariff_.+$",
                ),
                CallbackQueryHandler(
                    cancel_promo_creation, pattern="^cancel_promo_create$"
                ),
            ],
        },
        fallbacks=[],
    )
    return handler


async def list_promocodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all active promocodes with delete buttons (admin only)"""
    chat_id = update.effective_chat.id

    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
        return

    try:
        api_client = BackendAPIClient()
        promocodes = await api_client.list_active_promocodes()

        if not promocodes:
            await update.message.reply_text(
                "📋 <b>Активные промокоды</b>\n\n"
                "Промокодов нет.\n\n"
                "Используйте /create_promocode для создания.",
                parse_mode="HTML",
            )
            return

        message_lines = ["📋 <b>Активные промокоды:</b>\n"]
        keyboard = []

        for promo in promocodes:
            # Format tariffs display
            if promo.get("applicable_tariffs"):
                import json

                tariff_ids = json.loads(promo["applicable_tariffs"])
                from telegram_bot.models.enum.tariff import Tariff

                tariff_names = [Tariff(t_id).name for t_id in tariff_ids]
                tariffs_text = ", ".join(tariff_names)
            else:
                tariffs_text = "ВСЕ ТАРИФЫ"

            from datetime import datetime
            date_from = datetime.fromisoformat(promo["date_from"])
            date_to = datetime.fromisoformat(promo["date_to"])

            message_lines.append(
                f"\n🎟️ <b>{promo['name']}</b>\n"
                f"   💰 Скидка: {promo['discount_percentage']}%\n"
                f"   📅 Период: {date_from.strftime('%d.%m.%Y')} - {date_to.strftime('%d.%m.%Y')}\n"
                f"   🎯 Тарифы: {tariffs_text}"
            )

            # Add delete button for each promocode
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"🗑 Удалить {promo['name']}",
                        callback_data=f"delete_promo_{promo['id']}",
                    )
                ]
            )

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "\n".join(message_lines), parse_mode="HTML", reply_markup=reply_markup
        )

        LoggerService.info(__name__, "Listed promocodes", update)

    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка при получении списка промокодов: {str(e)}", parse_mode="HTML"
        )
        LoggerService.error(__name__, "Error listing promocodes", e)


async def handle_delete_promocode_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle promocode deletion via callback button"""
    query = update.callback_query
    await query.answer()

    # Extract promocode ID from callback_data
    callback_data = query.data
    try:
        promocode_id = int(callback_data.replace("delete_promo_", ""))
    except ValueError:
        await query.edit_message_text(
            "❌ Ошибка: неверный ID промокода", parse_mode="HTML"
        )
        return

    try:
        # Deactivate promocode
        api_client = BackendAPIClient()
        success = await api_client.deactivate_promocode(promocode_id)

        if success:
            await query.edit_message_text(
                f"✅ Промокод с ID <b>{promocode_id}</b> успешно деактивирован!\n\n"
                f"Используйте /list_promocodes для просмотра оставшихся промокодов.",
                parse_mode="HTML",
            )
            LoggerService.info(
                __name__,
                "Promocode deactivated via button",
                update,
                kwargs={"promocode_id": promocode_id},
            )
        else:
            await query.edit_message_text(
                f"❌ Промокод с ID <b>{promocode_id}</b> не найден или уже деактивирован.",
                parse_mode="HTML",
            )

    except Exception as e:
        await query.edit_message_text(
            f"❌ Ошибка при деактивации промокода: {str(e)}", parse_mode="HTML"
        )
        LoggerService.error(__name__, "Error deactivating promocode", e)


async def get_users_without_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """TEST: Admin command to show all users without chat_id"""
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
        return END

    # Send loading message
    loading_msg = await update.message.reply_text("⏳ Загрузка данных...")

    try:
        # Get statistics
        api_client = BackendAPIClient()
        users_without_chat_id = await api_client.get_users_without_chat_id()
        total_users = await api_client.get_total_users_count()
        users_with_chat_id = total_users - len(users_without_chat_id)

        # Delete loading message
        await loading_msg.delete()

        # Send summary first
        summary = (
            f"📊 <b>Статистика пользователей:</b>\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"✅ С chat_id: {users_with_chat_id}\n"
            f"❌ Без chat_id: {len(users_without_chat_id)}\n"
        )
        await update.message.reply_text(summary, parse_mode="HTML")

    except Exception as e:
        # Try to delete loading message if it still exists
        try:
            await loading_msg.delete()
        except:
            pass

        error_msg = str(e).replace('<', '&lt;').replace('>', '&gt;')
        await update.message.reply_text(
            f"❌ Ошибка при получении списка пользователей: {error_msg}"
        )
        LoggerService.error(__name__, "Error listing users without chat_id", e)

    return END
