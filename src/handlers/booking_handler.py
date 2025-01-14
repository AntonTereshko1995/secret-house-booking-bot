import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler)

USER_NAME, TARIFF, PHOTOSHOOT, SECRET_ROOM, SAUNA, PAY, SELECT_BEDROOM, START_DATE, FINISH_DATE, NUMBER_OF_PEOPLE, COMMENT, SALE, END = map(chr, range(0, 13))

def get_handler() -> ConversationHandler:
    menu_handler = ConversationHandler(
        entry_points=[CommandHandler('start', handle)],
        states={
            MENU: [CallbackQueryHandler(select_menu)],
            # CAR_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_type)],
            # CAR_COLOR: [CallbackQueryHandler(car_color)],
            # CAR_MILEAGE_DECISION: [CallbackQueryHandler(car_mileage_decision)],
            # CAR_MILEAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_mileage)],
            # PHOTO: [
            #     MessageHandler(filters.PHOTO, photo),
            #     CommandHandler('skip', skip_photo)
            # ],
            # SUMMARY: [MessageHandler(filters.ALL, summary)]
        },
        fallbacks=[CommandHandler('cancel', handle)])
    return menu_handler
    
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