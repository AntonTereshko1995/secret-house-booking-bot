import http
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.logger_service import LoggerService
import asyncio
import logging
from flask import Flask, jsonify, request
from telegram import BotCommand, BotCommandScopeChatAdministrators, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from db import database
from src.handlers import menu_handler, admin_handler
from src.config.config import TELEGRAM_TOKEN, ADMIN_CHAT_ID
from src.services import job_service

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)
WEBHOOK_URL = "https://telegram-bot-535413863315.us-central1.run.app"

application: Application = None

async def set_commands(application: Application):
    """Sets bot commands."""
    user_commands = [BotCommand("start", "Меню")]
    admin_commands = user_commands + [BotCommand("booking_list", "Бронирования"), BotCommand("change_password", "Изменить пароль")]
    
    await application.bot.set_my_commands(user_commands)
    await application.bot.set_my_commands(admin_commands, scope=BotCommandScopeChatAdministrators(chat_id=ADMIN_CHAT_ID))

@app.route("/health/liveness")
def liveness_check():
    return jsonify({"status": "ok"}), 200

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    LoggerService.info(__name__, f"webhook is called")
    global application
    update = Update.de_json(request.get_json(), application.bot)
    asyncio.run(application.process_update(update))  # ✅ Fix: Run async function properly
    return "OK", 200


@app.route("/home")
def home():
    LoggerService.info(__name__, "📩 Webhook /home received a request")
    
    try:
        request.content_type = "application/json"
        if request.content_type != "application/json":
            LoggerService.error(__name__, "❌ Unsupported Content-Type received.")
            return f"Unsupported Media Type. Media: {request.content_type}", 415

        update_data = request.get_json()
        LoggerService.info(__name__, f"📩 Webhook received update: {update_data}")

        update = Update.de_json(update_data, application.bot)
        asyncio.run(application.process_update(update))

        return "OK", 200

    except Exception as e:
        LoggerService.error(__name__, f"❌ Error in webhook: {e}")
        return f"Error: {e} json: {request.get_json()}", 500
    # LoggerService.info(__name__, f"home is called")
    # application.process_update(
    #     Update.de_json(request.get_json(force=True), application.bot))
    # return "OK", http.HTTPStatus.NO_CONTENT

def set_webhook():
    global application
    webhook_url = f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
    application.bot.set_webhook(url=webhook_url)
    LoggerService.info(__name__, f"✅ Webhook set to {webhook_url}")

if __name__ == "__main__":
    database.create_db_and_tables()

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

    set_webhook()

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
