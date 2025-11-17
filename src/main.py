import os
import time
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.logger_service import LoggerService
import logging
from flask import Flask
from telegram import BotCommand, BotCommandScopeChatAdministrators, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from telegram.error import BadRequest
from src.handlers import menu_handler, admin_handler, feedback_handler
from src.config.config import TELEGRAM_TOKEN, ADMIN_CHAT_ID
from src.services import job_service
from src.services.callback_recovery_service import CallbackRecoveryService

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
app = Flask(__name__)


async def set_commands(application: Application):
    user_commands = [BotCommand("start", "Открыть 'Главное меню'")]
    admin_commands = user_commands + [
        BotCommand("booking_list", "Бронирования"),
        BotCommand("change_password", "Изменить пароль"),
        BotCommand("unpaid_bookings", "Неоплаченные бронирования"),
        BotCommand("broadcast", "Рассылка всем"),
        BotCommand("broadcast_with_bookings", "Рассылка c бронями"),
        BotCommand("broadcast_without_bookings", "Рассылка БЕЗ броней"),
        BotCommand("statistics", "Статистика"),
        BotCommand("create_promocode", "➕ Создать промокод"),
        BotCommand("list_promocodes", "📋 Список промокодов"),
    ]

    await application.bot.set_my_commands(user_commands)
    await application.bot.set_my_commands(
        admin_commands, scope=BotCommandScopeChatAdministrators(chat_id=ADMIN_CHAT_ID)
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enhanced error handler with callback query recovery"""

    # Check if it's a callback query expiration error
    if isinstance(context.error, BadRequest):
        error_msg = str(context.error).lower()
        if "query is too old" in error_msg or "query id is invalid" in error_msg:
            LoggerService.info(
                __name__,
                "Callback query expired - attempting recovery",
                update,
                kwargs={"error": str(context.error)}
            )

            # Attempt recovery if update is valid
            if isinstance(update, Update) and update.callback_query:
                recovery_service = CallbackRecoveryService()
                try:
                    await recovery_service.handle_stale_callback(update, context)
                    return  # Recovery successful, don't log as error
                except Exception as recovery_error:
                    LoggerService.error(
                        __name__,
                        "Recovery from stale callback failed",
                        exception=recovery_error,
                        update=update
                    )

    # Log all other errors normally
    LoggerService.error(
        __name__, f"Update {update} caused error {context.error}", update
    )


if __name__ == "__main__":
    application = (
        Application.builder().token(TELEGRAM_TOKEN).post_init(set_commands).build()
    )

    # Register handlers
    application.add_handler(menu_handler.get_handler())
    application.add_error_handler(error_handler)
    application.add_handler(admin_handler.get_password_handler())
    application.add_handler(admin_handler.get_purchase_handler())
    application.add_handler(admin_handler.get_create_promocode_handler())
    application.add_handler(admin_handler.get_broadcast_handler())
    application.add_handler(admin_handler.get_broadcast_with_bookings_handler())
    application.add_handler(admin_handler.get_broadcast_without_bookings_handler())
    application.add_handler(feedback_handler.get_handler())

    application.add_handler(CommandHandler("start", menu_handler.show_menu))
    application.add_handler(
        CommandHandler("booking_list", admin_handler.get_booking_list)
    )
    application.add_handler(
        CommandHandler("unpaid_bookings", admin_handler.get_unpaid_bookings)
    )
    application.add_handler(CommandHandler("statistics", admin_handler.get_statistics))
    application.add_handler(
        CommandHandler("list_promocodes", admin_handler.list_promocodes)
    )
    application.add_handler(
        CallbackQueryHandler(
            admin_handler.handle_delete_promocode_callback,
            pattern="^delete_promo_\d+$",
        )
    )

    job = job_service.JobService()
    job.set_application(application)

    os.environ["TZ"] = "Europe/Minsk"
    time.tzset()

    application.run_polling(allowed_updates=Update.ALL_TYPES)
