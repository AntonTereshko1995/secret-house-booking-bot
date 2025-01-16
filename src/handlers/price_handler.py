import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CallbackQueryHandler, CallbackContext)
from src.handlers import menu_handler
from src.services import file_service
from src.constants import END, MENU, PRICE, STOPPING

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(send_prices, pattern=f"^{str(PRICE)}$")],
        states={ },
        fallbacks=[CallbackQueryHandler(end_price_menu, pattern=f"^{str(END)}$")],
        map_to_parent={
            # Return to top level menu
            END: MENU,
            # End conversation altogether
            STOPPING: END,
        },)
    return handler

async def send_prices(update: Update, context: CallbackContext):
    price_images = file_service.get_price_media()
    await context.bot.send_media_group(chat_id=update.effective_chat.id, media=price_images)

    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=str(END))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        text="Мы отобразили все доступные тарифы в The Secret House.",
        reply_markup=reply_markup)
    return MENU

async def end_price_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler.show_menu(update, context)
    return END