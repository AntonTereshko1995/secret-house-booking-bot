import sys
import os
import logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db import database
from telegram import BotCommand, BotCommandScopeChatAdministrators, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from src.handlers import menu_handler, admin_handler
from src.services.logger_service import LoggerService
from src.config.config import TELEGRAM_TOKEN, ADMIN_CHAT_ID
from src.services import job_service
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

async def set_commands(application: Application):
    user_commands = [
        BotCommand("start", "Меню"),
        # BotCommand("prices", "Посмотреть тарифы"),
    ]
    admin_commands = user_commands + [
        BotCommand("booking_list", "Бронирования"),
        BotCommand("change_password", "Изменить пароль"),
    ]
    
    await application.bot.set_my_commands(user_commands)
    await application.bot.set_my_commands(admin_commands, scope=BotCommandScopeChatAdministrators(chat_id=ADMIN_CHAT_ID))

def main() -> None:
    database.create_db_and_tables()
    application = Application.builder().token(TELEGRAM_TOKEN).post_init(set_commands).build()
    application.add_handler(menu_handler.get_handler())
    application.add_handler(CommandHandler("start", menu_handler.show_menu))

    # Admin
    application.add_handler(CommandHandler("booking_list", admin_handler.get_booking_list))
    application.add_handler(CallbackQueryHandler(admin_handler.booking_callback, pattern=r"^booking_\d+_chatid_(\d+)_bookingid_(\d+)_cash_(True|False)$"))
    application.add_handler(CallbackQueryHandler(admin_handler.gift_callback, pattern=r"^gift_\d+_chatid_(\d+)_giftid_(\d+)$"))
    application.add_handler(CallbackQueryHandler(admin_handler.subscription_callback, pattern=r"^subscription_\d+_chatid_(\d+)_subscriptionid_(\d+)$"))

    job = job_service.JobService()
    job.set_application(application)
    LoggerService.init_logger()

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()