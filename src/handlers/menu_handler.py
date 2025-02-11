import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services import job_service
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CommandHandler)
from src.constants import AVAILABLE_DATES, BOOKING, CANCEL_BOOKING, CHANGE_BOOKING_DATE, GIFT_CERTIFICATE, MENU, PRICE, QUESTIONS, SUBSCRIPTION, USER_BOOKING
from src.handlers import booking_handler, change_booking_date_handler, cancel_booking_handler, question_handler, price_handler, gift_certificate_handler, available_dates_handler, subscription_handler, user_booking 

job = job_service.JobService()

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CommandHandler('start', show_menu)],
        states={ 
            MENU: [
                booking_handler.get_handler(),
                cancel_booking_handler.get_handler(),
                subscription_handler.get_handler(),
                change_booking_date_handler.get_handler(),
                available_dates_handler.get_handler(),
                price_handler.get_handler(),
                gift_certificate_handler.get_handler(),
                question_handler.get_handler(),
                user_booking.get_handler()],
            },
        fallbacks=[])
    return handler

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await job.init_job(update, context)
    
    buttons = [
        [InlineKeyboardButton("🔹 Забронировать дом 🏠", callback_data=str(BOOKING))],
        [InlineKeyboardButton("🔹 Купить подарочный сертификат 🎁", callback_data=str(GIFT_CERTIFICATE))],
        [InlineKeyboardButton("🔹 Оформить абонемент 🔄", callback_data=str(SUBSCRIPTION))],
        [InlineKeyboardButton("🔹 Мои бронирования 👁️‍🗨️", callback_data=str(USER_BOOKING))],
        [InlineKeyboardButton("🔹 Отменить бронирование ❌", callback_data=str(CANCEL_BOOKING))],
        [InlineKeyboardButton("🔹 Перенести бронирование 🔄", callback_data=str(CHANGE_BOOKING_DATE))],
        [InlineKeyboardButton("🔹 Проверить свободные даты 📅", callback_data=str(AVAILABLE_DATES))],
        [InlineKeyboardButton("🔹 Узнать стоимость аренды 💰", callback_data=str(PRICE))],
        [InlineKeyboardButton("🔹 Задать вопрос ❓", callback_data=str(QUESTIONS))],
        [InlineKeyboardButton("🔹 Связаться с администратором 📞", url='https://t.me/the_secret_house')]]

    text = ("<b>Добро пожаловать в The Secret House!</b>\n"
        "🏡 <b>Уют, искусство и тайны — всё для вашего идеального отдыха.</b>\n\n"
        "Выберите нужный пункт:\n\n")

    if update.message:
        await update.message.reply_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(buttons))
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(buttons))
    
    return MENU