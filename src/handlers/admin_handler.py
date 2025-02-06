from datetime import date
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.calculation_rate_service import CalculationRateService
from db.models.subscription import SubscriptionBase
from db.models.gift import GiftBase
from matplotlib.dates import relativedelta
from src.constants import END
from src.services.calendar_service import CalendarService
from db.models.user import UserBase
from db.models.booking import BookingBase
from src.services.database_service import DatabaseService
from src.config.config import ADMIN_CHAT_ID, PERIOD_IN_MONTHS, INFORM_CHAT_ID
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CallbackQueryHandler)
from src.helpers import string_helper, string_helper, subscription_helper, tariff_helper
import re

database_service = DatabaseService()
calendar_service = CalendarService()
calculation_rate_service = CalculationRateService()

async def get_booking_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if str(chat_id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
    else:
        message = get_future_booking_message()
        await update.message.reply_text(message)

async def accept_booking_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, booking: BookingBase, user_chat_id: int, photo):
    user = database_service.get_user_by_id(booking.user_id)
    message = string_helper.generate_booking_info_message(booking, user)
    keyboard = [
        [InlineKeyboardButton("Подтвердить оплату", callback_data=f"booking_1_chatid_{user_chat_id}_booking_id_{booking.id}")],
        [InlineKeyboardButton("Отмена бронирования", callback_data=f"booking_2_chatid_{user_chat_id}_booking_id_{booking.id}")],
        [InlineKeyboardButton("Скидка 5%", callback_data=f"booking_3_chatid_{user_chat_id}_booking_id_{booking.id}")],
        [InlineKeyboardButton("Скидка 10%", callback_data=f"booking_4_chatid_{user_chat_id}_booking_id_{booking.id}")],
        [InlineKeyboardButton("Скидка 15%", callback_data=f"booking_5_chatid_{user_chat_id}_booking_id_{booking.id}")],
        [InlineKeyboardButton("Скидка 20%", callback_data=f"booking_6_chatid_{user_chat_id}_booking_id_{booking.id}")],
        [InlineKeyboardButton("Скидка 30%", callback_data=f"booking_7_chatid_{user_chat_id}_booking_id_{booking.id}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo, caption=message, reply_markup=reply_markup)

async def accept_gift_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, gift: GiftBase, user_chat_id: int, photo):
    message = string_helper.generate_gift_info_message(gift)
    keyboard = [
        [InlineKeyboardButton("Подтвердить оплату", callback_data=f"gift_1_chatid_{user_chat_id}_booking_id_{gift.id}")],
        [InlineKeyboardButton("Отмена подарочного сертификата", callback_data=f"gift_2_chatid_{user_chat_id}_booking_id_{gift.id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo, caption=message, reply_markup=reply_markup)

async def accept_subscription_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, subscription: SubscriptionBase, user_chat_id: int, photo):
    user = database_service.get_user_by_id(subscription.user_id)
    message = string_helper.generate_subscription_info_message(subscription, user)
    keyboard = [
        [InlineKeyboardButton("Подтвердить оплату", callback_data=f"subscription_1_chatid_{user_chat_id}_booking_id_{subscription.id}")],
        [InlineKeyboardButton("Отмена абонемента", callback_data=f"subscription_2_chatid_{user_chat_id}_booking_id_{subscription.id}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo, caption=message, reply_markup=reply_markup)

async def inform_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE, booking: BookingBase):
    user = database_service.get_user_by_id(booking.user_id)
    message = (
        f"Отмена бронирования!\n"
        f"Контакт клиента: {user.contact}\n"
        f"Дата начала: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"Дата завершения: {booking.end_date.strftime('%d.%m.%Y %H:%M')}\n")
    await context.bot.send_message(chat_id=INFORM_CHAT_ID, text=message)

async def inform_changing_booking_date(update: Update, context: ContextTypes.DEFAULT_TYPE, booking: BookingBase, old_start_date: date):
    user = database_service.get_user_by_id(booking.user_id)
    message = (
        f"Перенос даты бронирования бронирования!\n"
        f"Контакт клиента: {user.contact}\n"
        f"Старая дата начала: {old_start_date.strftime('%d.%m.%Y')}\n"
        f"Дата начала: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"Дата завершения: {booking.end_date.strftime('%d.%m.%Y %H:%M')}\n")
    await context.bot.send_message(chat_id=INFORM_CHAT_ID, text=message)

async def booking_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = string_helper.parse_booking_callback_data(query.data)
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

async def gift_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = string_helper.parse_gift_callback_data(query.data)
    chat_id = data["user_chat_id"] 
    gift_id = data["gift_id"]
    menu_index = data["menu_index"]

    match menu_index:
        case "1":
            await approve_gift(update, context, chat_id, gift_id)
        case "2":
            await cancel_gift(update, context, chat_id, gift_id)

async def subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = string_helper.parse_subscription_callback_data(query.data)
    chat_id = data["user_chat_id"] 
    subscription_id = data["subscription_id"]
    menu_index = data["menu_index"]

    match menu_index:
        case "1":
            await approve_subscription(update, context, chat_id, subscription_id)
        case "2":
            await cancel_subscription(update, context, chat_id, subscription_id)
    
async def approve_booking(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, booking_id: int):
    (booking, user) = await prepare_approve_process(update, context, booking_id)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=chat_id, 
        text="Восхитительно!\n"
            "Ваше бронирование подтверждено администратором.\n"
            "За 1 день до Вашего бронирования Вам приедет сообщение с деталями бронирования и инструкцией по заселению.\n",
        reply_markup=reply_markup)
    await update.callback_query.edit_message_caption(f"Подтверждено \n\n{string_helper.generate_booking_info_message(booking, user)}")

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
    await update.callback_query.edit_message_caption(f"Отмена.\n\n {string_helper.generate_booking_info_message(booking, user)}")

async def approve_gift(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, gift_id: int):
    gift = database_service.update_gift(gift_id, is_paymented=True)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    await context.bot.send_message(
        chat_id=chat_id, 
        text=f"{gift.code}",
        reply_markup=reply_markup)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=chat_id, 
        text="Восхитительно!\n"
            "Покупка подарочного сертификата подтверждена администратором.\n"
            "В течении нескольких часов мы вышлим электроннай подарочный сертификат.\n"
            "Мы отправили Вам код подарочного сертификата. При бронировании введите его.",
        reply_markup=reply_markup)
    await update.callback_query.edit_message_caption(f"Подтверждено \n\n{string_helper.generate_gift_info_message(gift)}")

async def cancel_gift(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, gift_id: int):
    gift = database_service.get_gift_by_id(gift_id)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=chat_id, 
        text="Внимание!\n"
            "Ваше покупка подарочного сертификата была отменена.\n"
            "С Вами свяжется администратор, чтобы обсудить детали.\n",
        reply_markup=reply_markup)
    await update.callback_query.edit_message_caption(f"Отмена.\n\n {string_helper.generate_gift_info_message(gift)}")

async def approve_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, subscription_id: int):
    subscription = database_service.update_subscription(subscription_id, is_paymented=True)
    user = database_service.get_user_by_id(subscription.user_id)
    await context.bot.send_message(
        chat_id=chat_id, 
        text=f"{subscription.code}",
        reply_markup=reply_markup)

    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=chat_id, 
        text="Восхитительно!\n"
            "Покупка абонемента подтверждена администратором.\n"
            "Мы отправили Вам код абонемента. При бронировании введите его.",
        reply_markup=reply_markup)
    await update.callback_query.edit_message_caption(f"Подтверждено \n\n{string_helper.generate_subscription_info_message(subscription, user)}")

async def cancel_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, subscription_id: int):
    subscription = database_service.get_subscription_by_id(subscription_id)
    user = database_service.get_user_by_id(subscription.user_id)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=chat_id, 
        text="Внимание!\n"
            "Ваше покупка абонемента была отменена.\n"
            "С Вами свяжется администратор, чтобы обсудить детали.\n",
        reply_markup=reply_markup)
    await update.callback_query.edit_message_caption(f"Отмена.\n\n {string_helper.generate_subscription_info_message(subscription, user)}")


async def set_sale_booking(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, booking_id: int, sale_percentage: int):
    (booking, user) = await prepare_approve_process(update, context, booking_id, sale_percentage)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=chat_id, 
        text="Восхитительно!\n"
            "Ваше бронирование подтверждено администратором.\n"
            f"Новая цена {booking.price}.\n"
            "За 1 день до Вашего бронирования Вам приедет сообщение с деталями бронирования и инструкцией по заселению.\n",
            reply_markup=reply_markup)
    await update.callback_query.edit_message_caption(f"Подтверждено \n\n Скидка: {sale_percentage}% \n\n{string_helper.generate_booking_info_message(booking, user)}")

async def inform_message(update: Update, context: ContextTypes.DEFAULT_TYPE, booking: BookingBase, user: UserBase):
    message = string_helper.generate_booking_info_message(booking, user)
    await context.bot.send_message(chat_id=INFORM_CHAT_ID, text=message)

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

async def prepare_approve_process(update: Update, context: ContextTypes.DEFAULT_TYPE, booking_id: int, sale_percentage: int = None):
    booking = database_service.get_booking_by_id(booking_id)
    user = database_service.get_user_by_id(booking.user_id)
    calendar_event_id = calendar_service.add_event(booking, user)
    if sale_percentage:
        price = calculation_rate_service.calculate_discounted_price(booking.price, sale_percentage)
    else:
        price = booking.price
    booking = database_service.update_booking(booking_id, price=price, is_prepaymented=True, calendar_event_id=calendar_event_id)
    check_subscription(booking)
    check_gift(booking, user)
    await inform_message(update, context, booking, user)
    return (booking, user)

def check_subscription(booking: BookingBase):
    if not booking.subscription_id:
        return
    
    subscription = database_service.get_subscription_by_id(booking.subscription_id)
    if not subscription:
        # TODO log
        return

    subscription.number_of_visits += 1
    is_done = True if subscription.number_of_visits == subscription.subscription_type.value else False
    database_service.update_subscription(subscription.id, is_done=is_done, number_of_visits=subscription.number_of_visits)

def check_gift(booking: BookingBase, user: UserBase):
    if not booking.gift_id:
        return
    
    gift = database_service.get_gift_by_id(booking.gift_id)
    database_service.update_gift(gift.id, is_done=True, user_id=user.id)

