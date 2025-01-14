from telegram import InlineKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram import (InlineKeyboardButton, ReplyKeyboardMarkup, Update, KeyboardButton)
from telegram.ext import (ContextTypes)

from src.main import CAR_COLOR

# async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE)  -> None:
#     reply_keyboard = [
#         [InlineKeyboardButton("LOL")]]

#     await update.message.reply_text(
#         'LOL в <b>The Secret House!</b>\n'
#         'Вы находитесь в основное меню.\n'
#         'Выберете для Вас интересующий пункт.',
#         parse_mode='HTML',
#         reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the user's car type."""
    # user = update.message.from_user
    # context.user_data['car_type'] = update.message.text
    # cars = {"Sedan": "🚗", "SUV": "🚙", "Sports": "🏎️", "Electric": "⚡"}
    # # logger.info('Car type of %s: %s', user.first_name, update.message.text)
    # await update.message.reply_text(
    #     f'<b>You selected {update.message.text} car {cars[update.message.text]}.\n'
    #     f'What color your car is?</b>',
    #     parse_mode='HTML',
    #     reply_markup=ReplyKeyboardRemove(),
    # )

    # Define inline buttons for car color selection
    keyboard = [
        [InlineKeyboardButton('Red', callback_data='Red')],
        [InlineKeyboardButton('Blue', callback_data='Blue')],
        [InlineKeyboardButton('Black', callback_data='Black')],
        [InlineKeyboardButton('White', callback_data='White')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('<b>Please choose:</b>', parse_mode='HTML', reply_markup=reply_markup)

    return CAR_COLOR