import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (InlineKeyboardButton, ReplyKeyboardMarkup, Update, KeyboardButton)
from telegram.ext import (ContextTypes)
from src.constants import Handler
from src.handlers import booking_handler

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [
        [InlineKeyboardButton(Handler.BOOKING, callback_data="booking")],
        [InlineKeyboardButton(Handler.AVAILABLE_DATES)],
        [InlineKeyboardButton(Handler.PRICE)],
        [InlineKeyboardButton(Handler.CANCEL_BOOKING)],
        [InlineKeyboardButton(Handler.CHANGE_BOOKING_DATE)],
        [InlineKeyboardButton(Handler.GIFT_CERTIFICATE)],
        [InlineKeyboardButton(Handler.QUESTION)],
        [InlineKeyboardButton(Handler.CONTACT)]]

    await update.message.reply_text(
        'Добро пожаловать в <b>The Secret House!</b>\n'
        'Вы находитесь в основное меню.\n'
        'Выберете для Вас интересующий пункт.',
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))