import sys
import os
import logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db import database
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from src.handlers import menu_handler, admin_handler
from src.config.config import TELEGRAM_TOKEN
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def main() -> None:
    database.create_db_and_tables()
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(menu_handler.get_handler())

    # Admin
    application.add_handler(CommandHandler("booking_list", admin_handler.get_booking_list))
    application.add_handler(CallbackQueryHandler(admin_handler.booking_callback, pattern=r"^booking_\d+_chatid_(\d+)_booking_id_(\d+)$"))
    application.add_handler(CallbackQueryHandler(admin_handler.gift_callback, pattern=r"^gift_\d+_chatid_(\d+)_gift_id_(\d+)$"))
    application.add_handler(CallbackQueryHandler(admin_handler.subscription_callback, pattern=r"^subscription_\d+_chatid_(\d+)_subscription_id_(\d+)$"))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES) 

if __name__ == '__main__':
    main()