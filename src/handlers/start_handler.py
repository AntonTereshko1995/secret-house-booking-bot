import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes)
from src.constants import BOOKING, CANCEL_BOOKING, CHANGE_BOOKING_DATE, AVAILABLE_DATES, PRICE, GIFT_CERTIFICATE, QUESTIONS, MENU
from src.handlers import booking_handler, change_booking_date_handler, cancel_booking_handler, question_handler, price_handler, gift_certificate_handler, available_dates_handler 

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [
        [InlineKeyboardButton("Забронировать", callback_data=str(BOOKING))],
        [InlineKeyboardButton("Отменить бронирование", callback_data=str(CANCEL_BOOKING))],
        [InlineKeyboardButton("Перенести бронирование", callback_data=str(CHANGE_BOOKING_DATE))],
        [InlineKeyboardButton("Свободные даты", callback_data=str(AVAILABLE_DATES))],
        [InlineKeyboardButton("Стоимость аренды", callback_data=str(PRICE))],
        [InlineKeyboardButton("Подарочный сертификат", callback_data=str(GIFT_CERTIFICATE))],
        [InlineKeyboardButton("Задать нам вопрос", callback_data=str(QUESTIONS))],
        [InlineKeyboardButton("Связаться с администратором", url='https://t.me/the_secret_house')]]

    await update.message.reply_text(
        'Добро пожаловать в <b>The Secret House!</b>\n'
        'Вы находитесь в основное меню.\n'
        'Выберете для Вас интересующий пункт.',
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(reply_keyboard))
    return MENU

async def select_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    menu = update.callback_query.data

    if menu == str(BOOKING):
        await booking_handler.handle(update, context)
        return
    elif menu == str(CANCEL_BOOKING):
        await cancel_booking_handler.handle(update, context)
        return
    elif menu == str(CHANGE_BOOKING_DATE):
        await change_booking_date_handler.handle(update, context)
        return
    elif menu == str(AVAILABLE_DATES):
        await available_dates_handler.handle(update, context)
        return
    elif menu == str(PRICE):
        await price_handler.handle(update, context)
        return
    elif menu == str(GIFT_CERTIFICATE):
        await gift_certificate_handler.handle(update, context)
        return
    elif menu == str(QUESTIONS):
        await question_handler.handle(update, context)
        return