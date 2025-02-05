from datetime import date
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from matplotlib.dates import relativedelta
from src.constants import END
from src.services.calendar_service import CalendarService
from db.models.user import UserBase
from db.models.booking import BookingBase
from src.services.database_service import DatabaseService
from src.config.config import ADMIN_CHAT_ID, PERIOD_IN_MONTHS
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CallbackQueryHandler)
from src.helpers import string_helper, string_helper, tariff_helper
import re

database_service = DatabaseService()
calendar_service = CalendarService()

async def get_booking_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if str(chat_id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
    else:
        message = get_future_booking_message()
        await update.message.reply_text(message)

async def accept_booking_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, booking: BookingBase, user_chat_id: int, photo):
    user = database_service.get_user_by_id(booking.user_id)
    message = string_helper.generate_info_message(booking, user)
    keyboard = [
        [InlineKeyboardButton("Подтвердить оплату", callback_data=f"admin_1_chatid_{user_chat_id}_booking_id_{booking.id}")],
        [InlineKeyboardButton("Отмена бронирования", callback_data=f"admin_2_chatid_{user_chat_id}_booking_id_{booking.id}")],
        [InlineKeyboardButton("Скидка 5%", callback_data=f"admin_3_chatid_{user_chat_id}_booking_id_{booking.id}")],
        [InlineKeyboardButton("Скидка 10%", callback_data=f"admin_4_chatid_{user_chat_id}_booking_id_{booking.id}")],
        [InlineKeyboardButton("Скидка 15%", callback_data=f"admin_5_chatid_{user_chat_id}_booking_id_{booking.id}")],
        [InlineKeyboardButton("Скидка 20%", callback_data=f"admin_6_chatid_{user_chat_id}_booking_id_{booking.id}")],
        [InlineKeyboardButton("Скидка 30%", callback_data=f"admin_7_chatid_{user_chat_id}_booking_id_{booking.id}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo, caption=message, reply_markup=reply_markup)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = parse_callback_data(query.data)
    chat_id = data["user_chat_id"] 
    booking_id = data["booking_id"]
    menu_index = data["menu_index"]

    match menu_index:
        case "1":
            await approve_booking(update, context, chat_id, booking_id)
        case "2":
            await cancel_booking(update, context, chat_id, booking_id)
        case "3":
            await set_sale_booking(update, context, chat_id, booking_id, 5)
        case "4":
            await set_sale_booking(update, context, chat_id, booking_id, 10)
        case "5":
            await set_sale_booking(update, context, chat_id, booking_id, 15)
        case "6":
            await set_sale_booking(update, context, chat_id, booking_id, 20)
        case "7":
            await set_sale_booking(update, context, chat_id, booking_id, 30)
    
async def approve_booking(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, booking_id: int):
    booking = database_service.get_booking_by_id(booking_id)
    user = database_service.get_user_by_id(booking.user_id)
    calendar_event_id = calendar_service.add_event(booking, user)
    booking = database_service.update_booking(booking_id, is_prepaymented=True, calendar_event_id=calendar_event_id)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=chat_id, 
        text="Восхитительно!\n"
            "Ваше бронирование подтверждено администратором.\n"
            "За 1 день до Вашего бронирования Вам приедет сообщение с деталями бронирования и инструкцией по заселению.\n",
        reply_markup=reply_markup)
    await update.callback_query.edit_message_caption(f"Подтверждено")
    await inform_message(update, context, booking, user)

async def cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, booking_id: int):
    booking = database_service.update_booking(booking_id, is_canceled=True)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=chat_id, 
        text="Внимание!\n"
            "Ваше бронирование было отменено.\n"
            "С Вами свяжется администратор, чтобы обсудить детали бронирования.\n",
        reply_markup=reply_markup)
    user = database_service.get_user_by_id(booking.user_id)
    message = string_helper.generate_info_message(booking, user)
    await update.callback_query.edit_message_caption(f"Отмена.\n\n {message}")

async def set_sale_booking(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, booking_id: int, sale_percentage: int):
    booking = database_service.get_booking_by_id(booking_id)
    user = database_service.get_user_by_id(booking.user_id)
    calendar_event_id = calendar_service.add_event(booking, user)
    new_price = calculate_discounted_price(booking.price, sale_percentage)
    booking = database_service.update_booking(booking_id, price=new_price, is_prepaymented=True, calendar_event_id=calendar_event_id)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=chat_id, 
        text="Восхитительно!\n"
            "Ваше бронирование подтверждено администратором.\n"
            f"Новая цена {new_price}.\n"
            "За 1 день до Вашего бронирования Вам приедет сообщение с деталями бронирования и инструкцией по заселению.\n",
            reply_markup=reply_markup)
    await update.callback_query.edit_message_caption(f"Подтверждено \nНовая цена:{new_price}")
    await inform_message(update, context, booking, user)

async def inform_message(update: Update, context: ContextTypes.DEFAULT_TYPE, booking: BookingBase, user: UserBase):
    message = string_helper.generate_info_message(booking, user)
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)

def calculate_discounted_price(original_price, discount_percent):
    return original_price * (1 - discount_percent / 100)

def parse_callback_data(callback_data: str):
    pattern = r"admin_(\d+)_chatid_(\d+)_booking_id_(\d+)"
    match = re.match(pattern, callback_data)
    if match:
        menu_index = match.group(1)
        user_chat_id = match.group(2)
        booking_id = match.group(3)
        return {"user_chat_id": user_chat_id, "booking_id": booking_id, "menu_index": menu_index}
    else:
        return None

def get_future_booking_message():
    today = date.today()
    max_date_booking = today + relativedelta(months=PERIOD_IN_MONTHS)
    booking_list = database_service.get_booking_by_period(today, max_date_booking, True)
    message = ""
    for booking in booking_list:
      user = database_service.get_user_by_id(booking.user_id)
      message += (
            f"Пользователь: {user.contact}\n"
            f"Дата начала: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"Дата завершения: {booking.end_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"Тариф: {tariff_helper.get_name(booking.tariff)}\n"
            f"Стоимость: {booking.price} руб.\n"
            f"Is prepaymented: {booking.is_prepaymented}\n"
            f"Is canceled: {booking.is_canceled}\n\n") 
    return message