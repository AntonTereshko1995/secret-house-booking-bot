import sys
import os
from src.services.navigation_service import NavigatonService

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.logger_service import LoggerService
from src.services.gpt_service import GptService
from telegram.constants import ChatAction
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from src.handlers import menu_handler
from src.constants import END, MENU, QUESTIONS

gpt_service = GptService()
navigation_service = NavigatonService()


def get_handler():
    return [
        MessageHandler(filters.TEXT & ~filters.COMMAND, message),
        CallbackQueryHandler(back_navigation, pattern=f"^{END}$"),
    ]


async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await menu_handler.show_menu(update, context)
    LoggerService.info(__name__, "back to menu", update)
    return MENU


async def start_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, "start conversation", update)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="Напишите любой вопрос, который Вы бы хотели узнать про The Secret House.\n\n"
        "Вам будет отвечать искусственный интеллект ChatGPT.\n",
        reply_markup=reply_markup,
    )
    return QUESTIONS


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    LoggerService.info(__name__, "user", update, kwargs={"message": message})
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    responce = await gpt_service.generate_response(message)
    LoggerService.info(__name__, "gpt", update, kwargs={"message": responce})
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=responce, reply_markup=reply_markup)
    return QUESTIONS
