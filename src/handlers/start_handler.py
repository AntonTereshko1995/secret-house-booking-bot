import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler)
from src.handlers import booking_handler, change_booking_date_handler, cancel_booking_handler, question_handler, price_handler, gift_certificate_handler, available_dates_handler 

BOOKING, CANCEL_BOOKING, CHANGE_BOOKING_DATE, AVAILABLE_DATES, QUESTIONS, PRICE, GIFT_CERTIFICATE = map(chr, range(7))
MENU = 1
BACK = 11

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CommandHandler('start', show_menu)],
        states={ 
            MENU: [CallbackQueryHandler(select_menu)],
            BACK: [CallbackQueryHandler(finish_message, pattern='^back_to_menu$')] 
            },
        fallbacks=[CommandHandler('cancel', show_menu)])
    return handler

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
# async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [
        [InlineKeyboardButton("Забронировать", callback_data=str(BOOKING))],
        [InlineKeyboardButton("Отменить бронирование", callback_data=str(CANCEL_BOOKING))],
        [InlineKeyboardButton("Перенести бронирование", callback_data=str(CHANGE_BOOKING_DATE))],
        [InlineKeyboardButton("Свободные даты", callback_data=str(AVAILABLE_DATES))],
        [InlineKeyboardButton("Стоимость аренды", callback_data=str(PRICE))],
        [InlineKeyboardButton("Подарочный сертификат", callback_data=str(GIFT_CERTIFICATE))],
        [InlineKeyboardButton("Задать нам вопрос", callback_data=str(QUESTIONS))],
        [InlineKeyboardButton("Связаться с администратором", url='https://t.me/the_secret_house')],
        [InlineKeyboardButton("Назад", callback_data="back_to_menu")]]

    await update.message.reply_text(
        'Добро пожаловать в <b>The Secret House!</b>\n'
        'Вы находитесь в основное меню.\n'
        'Выберете для Вас интересующий пункт.',
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(reply_keyboard))
    # return MENU

async def select_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer(text="Ответ отправлен!", show_alert=True)
    menu = update.callback_query.data

    if menu == str(BOOKING):
        handler = booking_handler.get_handler()
    elif menu == str(CANCEL_BOOKING):
        handler = cancel_booking_handler.get_handler()
    elif menu == str(CHANGE_BOOKING_DATE):
        handler = change_booking_date_handler.get_handler()
    elif menu == str(AVAILABLE_DATES):
        handler = available_dates_handler.get_handler()
    elif menu == str(PRICE):
        handler = price_handler.get_handler()
    elif menu == str(GIFT_CERTIFICATE):
        handler = gift_certificate_handler.get_handler()
    elif menu == str(QUESTIONS):
        handler = question_handler.get_handler()
    
    await handler.entry_points[0].callback(update, context)
    return ConversationHandler.END

async def finish_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer(text="Ответ отправлен!", show_alert=True)
    return ConversationHandler.END
    