#!/usr/bin/env python
"""
Telegram Bot Entry Point
Refactored to use Backend API for all operations.
"""
import os
import time
import sys
import asyncio
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import BotCommand, BotCommandScopeChatAdministrators, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from telegram.error import BadRequest

# Bot configuration
from telegram_bot.config import config

# Backend API Client
from telegram_bot.client.backend_api import BackendAPIClient, APIError

# Redis persistence (for conversation state)
from telegram_bot.services.redis.redis_persistence import RedisPersistence

# Import all refactored handlers
from telegram_bot.handlers import (
    menu_handler,
    admin_handler,
    booking_handler,
    booking_details_handler,
    available_dates_handler,
    cancel_booking_handler,
    change_booking_date_handler,
    feedback_handler,
    gift_certificate_handler,
    price_handler,
    promocode_handler,
    question_handler,
    user_booking,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO if config.DEBUG else logging.WARNING
)
logger = logging.getLogger(__name__)


async def check_backend_health():
    """Check if backend API is accessible on startup"""
    api_client = BackendAPIClient()

    try:
        health = await api_client.health_check()
        logger.info(f"✅ Backend API is healthy: {health}")
        logger.info(f"📡 Connected to: {config.BACKEND_API_URL}")
        return True
    except Exception as e:
        logger.error(f"⚠️  Backend API not accessible: {e}")
        logger.error(f"📡 Attempted to connect to: {config.BACKEND_API_URL}")
        logger.error("Bot will continue, but features may not work!")
        return False


async def set_commands(application: Application):
    """Set bot commands for user and admin"""
    user_commands = [BotCommand("start", "Открыть 'Главное меню'")]

    admin_commands = user_commands + [
        BotCommand("booking_list", "Управление бронированиями"),
        BotCommand("change_password", "Изменить пароль"),
        BotCommand("broadcast", "Рассылка всем"),
        BotCommand("broadcast_with_bookings", "Рассылка c бронями"),
        BotCommand("broadcast_without_bookings", "Рассылка БЕЗ броней"),
        BotCommand("statistics", "Статистика"),
        BotCommand("create_promocode", "Создать промокод"),
        BotCommand("list_promocodes", "Список промокодов"),
        BotCommand("users_without_chat_id", "Пользователи без chat_id"),
    ]

    await application.bot.set_my_commands(user_commands)
    await application.bot.set_my_commands(
        admin_commands,
        scope=BotCommandScopeChatAdministrators(chat_id=config.ADMIN_CHAT_ID)
    )

    logger.info("✅ Bot commands configured")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enhanced error handler with API error handling"""

    # Handle expired callback queries
    if isinstance(context.error, BadRequest):
        error_msg = str(context.error).lower()
        if "query is too old" in error_msg or "query id is invalid" in error_msg:
            logger.info("Callback query expired - user should retry")

            if isinstance(update, Update) and update.callback_query:
                try:
                    await update.callback_query.answer(
                        "Эта кнопка устарела. Пожалуйста, начните заново с /start",
                        show_alert=True
                    )
                except Exception:
                    pass
            return

    # Handle API errors
    if isinstance(context.error, APIError):
        logger.error(f"API Error: {context.error}")
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Извините, произошла ошибка при обращении к серверу. "
                "Пожалуйста, попробуйте позже."
            )
        return

    # Log all other errors
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🤖 Starting Secret House Telegram Bot")
    logger.info("=" * 60)
    logger.info(f"📡 Backend API: {config.BACKEND_API_URL}")
    logger.info(f"👤 Admin Chat ID: {config.ADMIN_CHAT_ID}")
    logger.info(f"🔧 Debug Mode: {config.DEBUG}")
    logger.info(f"💾 Redis: {config.REDIS_URL}:{config.REDIS_PORT}")

    # Check backend health before starting
    backend_healthy = asyncio.run(check_backend_health())

    if not backend_healthy:
        logger.warning("⚠️  Backend is not accessible! Bot may not function correctly.")
        logger.warning("   Make sure backend is running at: " + config.BACKEND_API_URL)

        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            logger.info("Exiting...")
            sys.exit(1)

    # Initialize Redis persistence for conversation states
    try:
        persistence = RedisPersistence()
        logger.info("✅ Redis persistence initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Redis: {e}")
        logger.error("Bot will run without conversation persistence")
        persistence = None

    # Build application
    builder = Application.builder().token(config.TELEGRAM_TOKEN).post_init(set_commands)

    if persistence:
        builder = builder.persistence(persistence)

    application = builder.build()

    logger.info("✅ Application initialized")

    # Register error handler
    application.add_error_handler(error_handler)

    # Register all conversation handlers (order matters!)
    logger.info("📝 Registering handlers...")

    # Admin handlers
    application.add_handler(admin_handler.get_password_handler())
    application.add_handler(admin_handler.get_broadcast_handler())
    application.add_handler(admin_handler.get_broadcast_with_bookings_handler())
    application.add_handler(admin_handler.get_broadcast_without_bookings_handler())
    application.add_handler(admin_handler.get_create_promocode_handler())
    application.add_handler(admin_handler.get_purchase_handler())

    # Booking management
    application.add_handler(booking_details_handler.get_handler())
    application.add_handler(booking_handler.get_handler())
    application.add_handler(change_booking_date_handler.get_handler())
    application.add_handler(cancel_booking_handler.get_handler())

    # User interaction handlers
    application.add_handler(feedback_handler.get_handler())
    application.add_handler(question_handler.get_handler())
    application.add_handler(gift_certificate_handler.get_handler())
    application.add_handler(promocode_handler.get_create_promocode_handler())
    application.add_handler(user_booking.get_handler())
    application.add_handler(available_dates_handler.get_handler())
    application.add_handler(price_handler.get_handler())

    # Menu handler (should be last for conversation handlers)
    application.add_handler(menu_handler.get_handler())

    # Command handlers
    application.add_handler(CommandHandler("start", menu_handler.show_menu))
    application.add_handler(CommandHandler("booking_list", admin_handler.get_booking_list))
    application.add_handler(CommandHandler("change_password", admin_handler.request_old_password))
    application.add_handler(CommandHandler("broadcast", admin_handler.start_broadcast))
    application.add_handler(CommandHandler("broadcast_with_bookings", admin_handler.start_broadcast_with_bookings))
    application.add_handler(CommandHandler("broadcast_without_bookings", admin_handler.start_broadcast_without_bookings))
    application.add_handler(CommandHandler("create_promocode", admin_handler.start_create_promocode))
    application.add_handler(CommandHandler("list_promocodes", admin_handler.list_promocodes))
    application.add_handler(CommandHandler("users_without_chat_id", admin_handler.get_users_without_chat_id))

    # Callback query handlers
    application.add_handler(CallbackQueryHandler(admin_handler.back_to_booking_list, pattern="^MBL$"))
    application.add_handler(CallbackQueryHandler(admin_handler.handle_delete_promocode_callback, pattern="^delete_promo_"))

    logger.info("✅ All handlers registered successfully")

    # Set timezone
    os.environ["TZ"] = "Europe/Minsk"
    time.tzset()

    logger.info("=" * 60)
    logger.info("🚀 Bot is starting... Press Ctrl+C to stop")
    logger.info("=" * 60)

    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)
