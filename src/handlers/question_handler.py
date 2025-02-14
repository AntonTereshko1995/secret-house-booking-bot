import sys
import os

from src.services.logger_service import LoggerService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.gpt_service import GptService
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters)
from src.handlers import menu_handler
from src.services.file_service import FileService
from src.constants import END, MENU, MESSAGE, STOPPING, QUESTIONS

gpt_service = GptService()

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_conversation, pattern=f"^{str(QUESTIONS)}$")],
        states={
            MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, message)],
         },
        fallbacks=[CallbackQueryHandler(back_navigation, pattern=f"^{END}$")],
        map_to_parent={
            END: MENU,
            STOPPING: END,
        })
    return handler

async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await menu_handler.show_menu(update, context)
    LoggerService.info(f"question_handler: back to menu", update)
    return END

async def start_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(f"question_handler: start conversation", update)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        text="Напишите любой вопрос, который Вы бы хотели узнать про The Secret House.\n",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return MESSAGE

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    LoggerService.info(f"question_handler: message: {message}", update)
    responce = await gpt_service.generate_response(message)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text=responce,
        reply_markup=reply_markup)

    return MESSAGE