from telegram import Update
from telegram import (InlineKeyboardButton, ReplyKeyboardMarkup, Update, KeyboardButton)
from telegram.ext import (ContextTypes)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [
        [InlineKeyboardButton("LOL")]]

    await update.message.reply_text(
        'LOL в <b>The Secret House!</b>\n'
        'Вы находитесь в основное меню.\n'
        'Выберете для Вас интересующий пункт.',
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))