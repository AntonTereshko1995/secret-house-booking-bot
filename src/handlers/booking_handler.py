import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.handlers import menu_handler
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler)

USER_NAME, TARIFF, PHOTOSHOOT, SECRET_ROOM, SAUNA, PAY, SELECT_BEDROOM, START_DATE, FINISH_DATE, NUMBER_OF_PEOPLE, COMMENT, SALE, END = map(chr, range(0, 13))

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CommandHandler('booking', enter_user)],
        states={
            USER_NAME: [CallbackQueryHandler(enter_user)],
            TARIFF: [CallbackQueryHandler(select_tariff)],
            PHOTOSHOOT: [CallbackQueryHandler(include_photoshoot)],
            SECRET_ROOM: [CallbackQueryHandler(include_secret_room)],
            SAUNA: [CallbackQueryHandler(include_sauna)],
            SELECT_BEDROOM: [CallbackQueryHandler(select_bedroom)],
            NUMBER_OF_PEOPLE: [CallbackQueryHandler(select_number_of_people)],
            START_DATE: [CallbackQueryHandler(select_start_date)],
            FINISH_DATE: [CallbackQueryHandler(select_finish_date)],
            COMMENT: [CallbackQueryHandler(add_comment)],
            SALE: [CallbackQueryHandler(select_sale)],
            PAY: [CallbackQueryHandler(pay)],
            END: [CallbackQueryHandler(finish_message)],
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
        fallbacks=[CommandHandler('cancel', menu_handler.show_menu)])
    return handler
    
async def enter_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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

    return TARIFF

async def select_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # await update.message.reply_text('<b>Please choose:</b>', parse_mode='HTML', reply_markup=reply_markup)
    return PHOTOSHOOT

async def include_photoshoot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # await update.message.reply_text('<b>Please choose:</b>', parse_mode='HTML', reply_markup=reply_markup)
    return SAUNA

async def include_sauna(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # await update.message.reply_text('<b>Please choose:</b>', parse_mode='HTML', reply_markup=reply_markup)
    return SECRET_ROOM

async def include_secret_room(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # await update.message.reply_text('<b>Please choose:</b>', parse_mode='HTML', reply_markup=reply_markup)
    return SAUNA

async def select_bedroom(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # await update.message.reply_text('<b>Please choose:</b>', parse_mode='HTML', reply_markup=reply_markup)
    return SAUNA

async def select_number_of_people(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # await update.message.reply_text('<b>Please choose:</b>', parse_mode='HTML', reply_markup=reply_markup)
    return SAUNA

async def select_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # await update.message.reply_text('<b>Please choose:</b>', parse_mode='HTML', reply_markup=reply_markup)
    return SAUNA

async def select_finish_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # await update.message.reply_text('<b>Please choose:</b>', parse_mode='HTML', reply_markup=reply_markup)
    return SAUNA

async def add_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # await update.message.reply_text('<b>Please choose:</b>', parse_mode='HTML', reply_markup=reply_markup)
    return SAUNA

async def select_sale(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # await update.message.reply_text('<b>Please choose:</b>', parse_mode='HTML', reply_markup=reply_markup)
    return SAUNA

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # await update.message.reply_text('<b>Please choose:</b>', parse_mode='HTML', reply_markup=reply_markup)
    return SAUNA

async def finish_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # await update.message.reply_text('<b>Please choose:</b>', parse_mode='HTML', reply_markup=reply_markup)
    return SAUNA