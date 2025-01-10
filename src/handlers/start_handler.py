import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, Update,
                      InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler, filters)

from src.constants import Handler

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

CAR_TYPE, CAR_COLOR, CAR_MILEAGE_DECISION, CAR_MILEAGE, PHOTO, SUMMARY = range(6)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # reply_keyboard = [['Забронировать', 
    #                    'Подарочный сертификат', 
    #                    'Свободные даты', 
    #                    'Стоимость аренды', 
    #                    'Задать нам вопрос',
    #                    'Отменить бронирование',
    #                    'Перенести бронирование',
    #                    'Связаться с администратором']]

    reply_keyboard = [
        [KeyboardButton(Handler.BOOKING)],
        [KeyboardButton(Handler.AVAILABLE_DATES)],
        [KeyboardButton(Handler.PRICE)],
        [KeyboardButton(Handler.CANCEL_BOOKING)],
        [KeyboardButton(Handler.CHANGE_BOOKING_DATE)],
        [KeyboardButton(Handler.GIFT_CERTIFICATE)],
        [KeyboardButton(Handler.QUESTION)],
        [KeyboardButton(Handler.CONTACT)]]

    await update.message.reply_text(
        'Добро пожаловать в <b>The Secret House!</b>\n'
        'Вы находитесь в основное меню.\n'
        'Выберете для Вас интересующий пункт.',
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )

    return CAR_TYPE