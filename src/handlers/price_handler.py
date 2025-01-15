import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, CallbackContext)
from src.handlers import start_handler
from src.services import file_service

LOL = 1

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CommandHandler('price', send_prices)],
        states={ 
            LOL: [CallbackQueryHandler(finish_message, pattern='^back_to_menu$')] 
        },
        fallbacks=[CommandHandler('cancel', start_handler.show_menu)],
        per_message=True)
    return handler

async def send_prices(update: Update, context: CallbackContext):
    price_images = file_service.get_price_media()
    await context.bot.send_media_group(chat_id=update.effective_chat.id, media=price_images)

    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=str(LOL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        text="Мы отобразили все доступные тарифы в The Secret House.",
        reply_markup=reply_markup)
    return LOL

async def finish_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Обработка callback_query
    if update.callback_query:
        await update.callback_query.answer()  # Подтверждаем callback
        await update.callback_query.message.edit_text(
            text="Привет! Я твой бот. Чем могу помочь?"
        )
    return ConversationHandler.END