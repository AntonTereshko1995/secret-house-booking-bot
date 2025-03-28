import os, time
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.logger_service import LoggerService
import logging
from flask import Flask, request
from telegram import BotCommand, BotCommandScopeChatAdministrators, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from db import database
from src.handlers import menu_handler, admin_handler
from src.config.config import TELEGRAM_TOKEN, ADMIN_CHAT_ID
from src.services import job_service

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)
WEBHOOK_URL = "https://telegram-bot-535413863315.europe-west1.run.app"

async def set_commands(application: Application):
    """Sets bot commands."""
    user_commands = [BotCommand("start", "Меню")]
    admin_commands = user_commands + [BotCommand("booking_list", "Бронирования"), BotCommand("change_password", "Изменить пароль")]
    
    await application.bot.set_my_commands(user_commands)
    await application.bot.set_my_commands(admin_commands, scope=BotCommandScopeChatAdministrators(chat_id=ADMIN_CHAT_ID))

# application: Application = Application.builder().token(TELEGRAM_TOKEN).post_init(set_commands).build()

# @app.route("/health/liveness")
# def liveness_check():
#     return "OK", 200

# @app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
# def webhook():
#     try:
#         LoggerService.info(__name__, f"webhook is called")
#         update = Update.de_json(request.get_json(), application.bot)

#         asyncio.run(application.process_update(update))
#         return "OK", 200
#     except Exception as e:
#         LoggerService.error(__name__, f"❌ Error in webhook: {e}")
#         return f"Error: {e} json: {request.get_json()}  Req {request}", 500

# def set_webhook():
#     webhook_url = f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
#     application.bot.set_webhook(url=webhook_url)
#     LoggerService.info(__name__, f"✅ Webhook set to {webhook_url}")

if __name__ == "__main__":
    # asyncio.run(application.initialize())

    application = Application.builder().token(TELEGRAM_TOKEN).post_init(set_commands).build()
    
    application.add_handler(menu_handler.get_handler())
    application.add_handler(CommandHandler("start", menu_handler.show_menu))
    application.add_handler(CommandHandler("booking_list", admin_handler.get_booking_list))
    application.add_handler(admin_handler.get_password_handler())
    application.add_handler(CallbackQueryHandler(admin_handler.booking_callback, pattern=r"^booking_\d+_chatid_(\d+)_bookingid_(\d+)_cash_(True|False)$"))
    application.add_handler(CallbackQueryHandler(admin_handler.gift_callback, pattern=r"^gift_\d+_chatid_(\d+)_giftid_(\d+)$"))
    application.add_handler(CallbackQueryHandler(admin_handler.subscription_callback, pattern=r"^subscription_\d+_chatid_(\d+)_subscriptionid_(\d+)$"))

    job = job_service.JobService()
    job.set_application(application)

    # set_webhook()
    # port = int(os.environ.get("PORT", 8080))
    # app.run(host="0.0.0.0", port=port)

    os.environ['TZ'] = 'Europe/Minsk'
    time.tzset()

    application.run_polling(allowed_updates=Update.ALL_TYPES)