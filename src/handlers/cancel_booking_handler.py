import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters)
from src.handlers import menu_handler
from src.helpers import string_helper, date_time_helper
from src.constants import BACK, END, MENU, STOPPING, CANCEL_BOOKING, VALIDATE_USER, SET_BOOKING_DATE

user_contact = ''
start_booking_date = datetime.date.min

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(enter_user_contact, pattern=f"^{str(CANCEL_BOOKING)}$")],
        states={ 
            VALIDATE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_user_contact)],
            SET_BOOKING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_booking_date)], 
            BACK: [CallbackQueryHandler(back_navigation, pattern=f"^{str(BACK)}$")], 
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

async def enter_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=str(END))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "Напишите Ваш <b>Telegram</b>.\n Формат ввода @user_name (обязательно начинайте ввод с @).\n Формат ввода номера телефона +375251111111 (обязательно начинайте ввод с +375).\n"

    if (update.callback_query != None):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup)
    else:
        await update.message.edit_text(
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup)
    return VALIDATE_USER

async def check_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user_input = update.message.text
        is_valid = string_helper.is_valid_user_name(user_input)
        if is_valid:
            user_contact = user_input

            keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=str(END))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                text="Введите дату заезда Вашего бронирования.\n"
                    "Формат даты: 01.04.2025",
                reply_markup=reply_markup)

            return SET_BOOKING_DATE
        else:
            await update.message.reply_text("Ошибка: имя пользователя в Telegram или номер телефона введены не коректно.\n"
                                            "Повторите ввод еще раз.")
    else:
        await update.message.reply_text("Ошибка: Пустая строка.\n"
                                        "Повторите ввод еще раз.")

    return VALIDATE_USER

async def enter_booking_date(update: Update, context: CallbackContext):
    if update.message and update.message.text:
        date_input = update.message.text
        date = date_time_helper.parse_date(date_input)
        if date != None:
            user_contact = date_input
            keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=str(END))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Бронирование успешно отменено.", reply_markup=reply_markup)
            return BACK
        else:
            await update.message.reply_text("Ошибка: Дата введена не корректно.\n"
                                            "Повторите ввод еще раз.")
    else:
        await update.message.reply_text("Ошибка: Пустая строка.\n"
                                        "Повторите ввод еще раз.")
    return SET_BOOKING_DATE