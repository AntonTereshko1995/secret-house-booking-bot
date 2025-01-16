import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CallbackQueryHandler, CallbackContext)
from src.handlers import menu_handler
from src.helpers import string_helper
from src.constants import END, MENU, STOPPING, CANCEL_BOOKING, CHECK_USER_NAME, START_DATE, CANCEL_RESULT_MESSAGE

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(enter_user_name, pattern=f"^{str(CANCEL_BOOKING)}$")],
        states={ 
            # ENTER_USER_NAME: [CallbackQueryHandler(check_user_name)],
            CHECK_USER_NAME: [CallbackQueryHandler(check_user_name)],
            START_DATE: [CallbackQueryHandler(enter_start_date)], 
            CANCEL_RESULT_MESSAGE: [CallbackQueryHandler(result_message)], 
            },
        fallbacks=[CallbackQueryHandler(back_navigation, pattern=f"^{str(END)}$")],
        map_to_parent={
            # Return to top level menu
            END: MENU,
            # End conversation altogether
            STOPPING: END,
        })
    return handler

async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler.show_menu(update, context)
    return END

async def enter_user_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=str(END))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Напишите Ваш <b>Telegram</b>.\n"
        "Формат ввода @user_name (обязательно начинайте ввод с @).\n"
        "Формат ввода номера телефона +375251111111 (обязательно начинайте ввод с +375).\n",
        reply_markup=reply_markup)
    return CHECK_USER_NAME

async def check_user_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    
    if update.message and update.message.text:
        user_input = update.message.text
        is_valid = string_helper.is_valid_user_name(user_input)
        if is_valid:
            return START_DATE
        else:
            await update.callback_query.message.reply_text("1 Ошибка: введите Ваш контакт повторно.")
    else:
        await update.callback_query.message.reply_text("1 Ошибка: введите Ваш контакт повторно.")

    # await update.callback_query.edit_message_text(
    #     text="Напишите Ваш <b>Telegram</b>.\n"
    #     "Формат ввода @user_name (обязательно начинайте ввод с @).\n"
    #     "Формат ввода номера телефона +375251111111 (обязательно начинайте ввод с +375).\n",
    #     reply_markup=reply_markup)
    return CHECK_USER_NAME

async def enter_start_date(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")

async def result_message(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")