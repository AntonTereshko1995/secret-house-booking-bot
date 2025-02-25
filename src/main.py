import sys
import os
import logging
import threading
import http.server
import socketserver
from flask import Flask, request
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db import database
from telegram import BotCommand, BotCommandScopeChatAdministrators, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from src.handlers import menu_handler, admin_handler
from src.config.config import TELEGRAM_TOKEN, ADMIN_CHAT_ID
from src.services import job_service
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)
application: Application

async def set_commands(application: Application):
    user_commands = [
        BotCommand("start", "Меню"),
    ]
    admin_commands = user_commands + [
        BotCommand("booking_list", "Бронирования"),
        BotCommand("change_password", "Изменить пароль"),
    ]
    
    await application.bot.set_my_commands(user_commands)
    await application.bot.set_my_commands(admin_commands, scope=BotCommandScopeChatAdministrators(chat_id=ADMIN_CHAT_ID))

# Webhook endpoint for Flask
@app.route('/webhook', methods=['POST'])
async def webhook():
    await application.update_queue.put(
        Update.de_json(data=await request.get_json(), bot=application.bot)
    )
    return "ok"

@app.route("/")
def main() -> None:
    database.create_db_and_tables()
    global application
    application = Application.builder().token(TELEGRAM_TOKEN).post_init(set_commands).build()
    application.add_handler(menu_handler.get_handler())
    application.add_handler(CommandHandler("start", menu_handler.show_menu))

    # Admin
    application.add_handler(CommandHandler("booking_list", admin_handler.get_booking_list))
    application.add_handler(admin_handler.get_password_handler())
    application.add_handler(CallbackQueryHandler(admin_handler.booking_callback, pattern=r"^booking_\d+_chatid_(\d+)_bookingid_(\d+)_cash_(True|False)$"))
    application.add_handler(CallbackQueryHandler(admin_handler.gift_callback, pattern=r"^gift_\d+_chatid_(\d+)_giftid_(\d+)$"))
    application.add_handler(CallbackQueryHandler(admin_handler.subscription_callback, pattern=r"^subscription_\d+_chatid_(\d+)_subscriptionid_(\d+)$"))

    job = job_service.JobService()
    job.set_application(application)
    return "Bot is running!"

    # application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    # app.run()