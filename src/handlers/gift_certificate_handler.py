import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.handlers import start_handler
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (CallbackContext, ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler)

USER_NAME, TARIFF, SECRET_ROOM, SAUNA, PAY, END = map(chr, range(0, 6))

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CommandHandler('gift_certificate', enter_user)],
        states={
            USER_NAME: [CallbackQueryHandler(enter_user)],
            TARIFF: [CallbackQueryHandler(select_tariff)],
            SECRET_ROOM: [CallbackQueryHandler(choose_secret_room)],
            SAUNA: [CallbackQueryHandler(choose_sauna)],
            PAY: [CallbackQueryHandler(pay)],
            END: [CallbackQueryHandler(finish_message)],
            # CAR_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_type)],
            # CAR_COLOR: [CallbackQueryHandler(car_color)],
            # CAR_MILEAGE_DECISION: [CallbackQueryHandler(car_mileage_decision)],
            # CAR_MILEAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_mileage)],
            # PHOTO: [
            #     MessageHandler(filters.PHOTO, photo),
            #     CommandHandler('skip', skip_photo)
            # ],
            # SUMMARY: [MessageHandler(filters.ALL, summary)]
        },
        fallbacks=[CommandHandler('cancel', start_handler.show_menu)])
    return handler

async def enter_user(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")

async def select_tariff(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")

async def choose_secret_room(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")

async def choose_sauna(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")  

async def pay(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")

async def finish_message(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")