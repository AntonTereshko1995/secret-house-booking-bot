import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, date
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters)
from src.handlers import menu_handler
from src.helpers import string_helper, date_time_helper
from src.constants import (
    BACK, 
    END,
    MENU, 
    STOPPING, 
    CHANGE_BOOKING_DATE, 
    VALIDATE_USER, 
    SET_OLD_START_DATE, 
    SET_START_DATE, 
    SET_START_TIME, 
    SET_FINISH_DATE, 
    SET_FINISH_TIME, 
    CONFIRM)

user_contact = ''
old_booking_date = date.today()
new_booking_date = datetime.today()
finish_booking_date = datetime.today()

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(enter_user_contact, pattern=f"^{str(CHANGE_BOOKING_DATE)}$")],
        states={ 
            VALIDATE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_user_contact)],
            SET_OLD_START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_old_start_date)], 
            SET_START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_start_date)], 
            SET_START_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_start_time)], 
            SET_FINISH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_finish_date)], 
            SET_FINISH_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_finish_time)], 
            CONFIRM: [CallbackQueryHandler(confirm_booking, pattern=f"^{CONFIRM}$")], 
            BACK: [CallbackQueryHandler(back_navigation, pattern=f"^{BACK}$")],
            },
        fallbacks=[CallbackQueryHandler(back_navigation, pattern=f"^{END}$")],
        map_to_parent={
            END: MENU,
            STOPPING: END,
        })
    return handler

async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler.show_menu(update, context)
    return END

async def enter_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Напишите Ваш <b>Telegram</b>.\n"
        "Формат ввода @user_name (обязательно начинайте ввод с @).\n"
        "Формат ввода номера телефона +375251111111 (обязательно начинайте ввод с +375).\n",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return VALIDATE_USER

async def check_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user_input = update.message.text
        is_valid = string_helper.is_valid_user_contact(user_input)
        if is_valid:
            global user_contact
            user_contact = user_input

            keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                text="Введите дату заезда Вашего бронирования.\n"
                    "Формат даты: 01.04.2025",
                reply_markup=reply_markup)

            return SET_OLD_START_DATE
        else:
            await update.message.reply_text("Ошибка: имя пользователя в Telegram или номер телефона введены не коректно.\n"
                                            "Повторите ввод еще раз.")
    else:
        await update.message.reply_text("Ошибка: Пустая строка.\n"
                                        "Повторите ввод еще раз.")

    return VALIDATE_USER

async def enter_old_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        date_input = update.message.text
        date = date_time_helper.parse_date(date_input)
        if date != None:
            global old_booking_date
            old_booking_date = date

            keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                text="Нашли Ваше бронирование.\n"
                    "Введите дату на которую Вы хотите перенести бронирование.\n"
                    "Формат даты: 01.04.2025", 
                reply_markup=reply_markup)
            return SET_START_DATE
        else:
            await update.message.reply_text("Ошибка: Дата введена не корректно.\n"
                                            "Повторите ввод еще раз.")
    else:
        await update.message.reply_text("Ошибка: Пустая строка.\n"
                                        "Повторите ввод еще раз.")
    return SET_OLD_START_DATE

async def enter_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        date_input = update.message.text
        date = date_time_helper.parse_date(date_input)
        if date != None:
            global new_booking_date
            new_booking_date = date

            keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                text="Выберете часы бронирования.\n"
                    "Формат времени: от 0 до 23. Пример: 13", 
                reply_markup=reply_markup)
            return SET_START_TIME
        else:
            await update.message.reply_text("Ошибка: Время введено не корректно.\n"
                                            "Повторите ввод еще раз.")
    else:
        await update.message.reply_text("Ошибка: Пустая строка.\n"
                                        "Повторите ввод еще раз.")
    return SET_START_DATE

async def enter_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        time_input = update.message.text
        time = date_time_helper.parse_time(time_input)
        if (time != None):
            global new_booking_date
            new_booking_date = new_booking_date.replace(hour=time.hour)

            keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                text="Выберете дату завершения бронирования.\n"
                    "Формат даты: 01.04.2025", 
                reply_markup=reply_markup)
            return SET_FINISH_DATE
        else:
            await update.message.reply_text("Ошибка: Время введено не корректно.\n"
                                            "Повторите ввод еще раз.")
    else:
        await update.message.reply_text("Ошибка: Пустая строка.\n"
                                        "Повторите ввод еще раз.")
    return SET_START_TIME

async def enter_finish_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        date_input = update.message.text
        date = date_time_helper.parse_date(date_input)
        if date != None:
            global finish_booking_date
            finish_booking_date = date

            keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                text="Выберете время завершения бронирования.\n"
                    "Формат времени: от 0 до 23. Пример: 13", 
                reply_markup=reply_markup)
            return SET_FINISH_TIME
        else:
            await update.message.reply_text("Ошибка: Дата введена не корректно.\n"
                                            "Повторите ввод еще раз.")
    else:
        await update.message.reply_text("Ошибка: Пустая строка.\n"
                                        "Повторите ввод еще раз.")
    return SET_FINISH_DATE

async def enter_finish_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        time_input = update.message.text
        time = date_time_helper.parse_time(time_input)
        if (time != None):
            global finish_booking_date
            finish_booking_date = finish_booking_date.replace(hour=time.hour)

            keyboard = [
                [InlineKeyboardButton("Подтвердить", callback_data=CONFIRM)],
                [InlineKeyboardButton("Назад в меню", callback_data=END)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                text=f"Подтвердите изменение даты бронирования с {old_booking_date.strftime('%d.%m.%Y')} "
                f"на {new_booking_date.strftime('%d.%m.%Y %H:%M')} "
                f"до {finish_booking_date.strftime('%d.%m.%Y %H:%M')}.", 
                reply_markup=reply_markup)
            return CONFIRM
        else:
            await update.message.reply_text("Ошибка: Время введено не корректно.\n"
                                            "Повторите ввод еще раз.")
    else:
        await update.message.reply_text("Ошибка: Пустая строка.\n"
                                        "Повторите ввод еще раз.")
    return SET_FINISH_TIME

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=f"Бронирование успешно перенесено c {new_booking_date.strftime('%d.%m.%Y %H:%M')} до {finish_booking_date.strftime('%d.%m.%Y %H:%M')}.\n",
        reply_markup=reply_markup)
    return MENU