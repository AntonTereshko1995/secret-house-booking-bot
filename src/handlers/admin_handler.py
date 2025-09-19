from datetime import date, datetime, time, timedelta
import sys
import os
from typing import Sequence
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.navigation_service import NavigatonService
from src.services.settings_service import SettingsService
from src.services.file_service import FileService
from src.services.calculation_rate_service import CalculationRateService
from db.models.subscription import SubscriptionBase
from db.models.gift import GiftBase
from matplotlib.dates import relativedelta
from src.constants import CONFIRM, EDIT_BOOKING_PURCHASE, END, BACK, SET_PASSWORD
from src.services.calendar_service import CalendarService
from db.models.user import UserBase
from db.models.booking import BookingBase
from src.services.database_service import DatabaseService
from src.config.config import ADMIN_CHAT_ID, PERIOD_IN_MONTHS, INFORM_CHAT_ID, PREPAYMENT, BANK_CARD_NUMBER, BANK_PHONE_NUMBER, ADMINISTRATION_CONTACT
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters)
from src.helpers import string_helper, string_helper, tariff_helper

database_service = DatabaseService()
calendar_service = CalendarService()
calculation_rate_service = CalculationRateService()
file_service = FileService()
settings_service = SettingsService()
navigation_service = NavigatonService()
writing_password = ''
new_price: str = ''
new_prepayment_price: str = ''

def get_purchase_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(booking_callback, pattern=r"^booking_\d+_chatid_(\d+)_bookingid_(\d+)_cash_(True|False)$"),
            CallbackQueryHandler(gift_callback, pattern=r"^gift_\d+_chatid_(\d+)_giftid_(\d+)$"),
            CallbackQueryHandler(subscription_callback, pattern=r"^subscription_\d+_chatid_(\d+)_subscriptionid_(\d+)$"),
        ],
        states={ 
            EDIT_BOOKING_PURCHASE: [
                CallbackQueryHandler(change_price, pattern=f"^price_(\d|{CONFIRM}|{BACK})_chatid_(\d+)_bookingid_(\d+)_cash_(True|False)$"),
                CallbackQueryHandler(change_prepayment_price, pattern=f"^prepayment_(\d|{CONFIRM}|{BACK})_chatid_(\d+)_bookingid_(\d+)_cash_(True|False)$")],
        },
        fallbacks=[
            CallbackQueryHandler(booking_callback, pattern=r"^booking_\d+_chatid_(\d+)_bookingid_(\d+)_cash_(True|False)$"),
            CallbackQueryHandler(gift_callback, pattern=r"^gift_\d+_chatid_(\d+)_giftid_(\d+)$"),
            CallbackQueryHandler(subscription_callback, pattern=r"^subscription_\d+_chatid_(\d+)_subscriptionid_(\d+)$")
        ])
    return handler

def get_password_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CommandHandler('change_password', change_password)],
        states={ 
            SET_PASSWORD: [CallbackQueryHandler(enter_house_password, pattern=r"^password_\d$")],
            },
        fallbacks=[])
    return handler

async def change_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if str(chat_id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
        return END
    
    keyboard = [
        [InlineKeyboardButton('1', callback_data="password_1"), InlineKeyboardButton('2', callback_data="password_2"), InlineKeyboardButton('3', callback_data="password_3")],
        [InlineKeyboardButton('4', callback_data="password_4"), InlineKeyboardButton('5', callback_data="password_5"), InlineKeyboardButton('6', callback_data="password_6")],
        [InlineKeyboardButton('7', callback_data="password_7"), InlineKeyboardButton('8', callback_data="password_8"), InlineKeyboardButton('9', callback_data="password_9")],
        [InlineKeyboardButton('Очистить', callback_data="password_clear"), InlineKeyboardButton('0', callback_data="password_0"), InlineKeyboardButton('Отмена', callback_data=f"password_{str(END)}")]]

    message = (f"Введите новый пароль и 4 цифр. Например 1235.\n" 
            f"Старый пароль: {settings_service.password}.\n" 
            f"Новый пароль: {writing_password}")
    if update.message:
        await update.message.reply_text(
            text=message, 
            reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard))
    return SET_PASSWORD

async def enter_house_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global writing_password
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        writing_password = ''
        return END
    elif data == "clear":
        writing_password = ''
        await change_password(update, context)
        return SET_PASSWORD
    
    writing_password += data
    if len(writing_password) == 4:
        settings_service.password = writing_password
        await update.callback_query.edit_message_text(text=f"Пароль изменен на {writing_password}.")
        writing_password = ''
        return END
    else:
        await change_password(update, context)
        return SET_PASSWORD

async def get_booking_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if str(chat_id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
    else:
        bookings = get_future_bookings()
        lol = list(filter(lambda i: i.price > 400, bookings))

        if not bookings:
            await update.message.reply_text("🔍 Не найдено бронирований.")
            return END

        for booking in bookings:
            user = database_service.get_user_by_id(booking.user_id)
            message = f"⛔ Отменен\n" if booking.is_canceled else ""
            message += (
                f"Пользователь: {user.contact}\n"
                f"Дата начала: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
                f"Дата завершения: {booking.end_date.strftime('%d.%m.%Y %H:%M')}\n"
                f"Тариф: {tariff_helper.get_name(booking.tariff)}\n"
                f"Стоимость: {booking.price} руб.\n"
                f"Предоплата: {booking.prepayment_price} руб.\n") 
            await update.message.reply_text(
                text=message)
    return END

async def accept_booking_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, booking: BookingBase, user_chat_id: int, photo, document, is_payment_by_cash = False):
    user = database_service.get_user_by_id(booking.user_id)
    count_booking = database_service.get_done_booking_count(booking.user_id)
    message = string_helper.generate_booking_info_message(booking, user, is_payment_by_cash, count_of_booking=count_booking)
    keyboard = [
        [InlineKeyboardButton("Подтвердить оплату", callback_data=f"booking_1_chatid_{user_chat_id}_bookingid_{booking.id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Отмена бронирования", callback_data=f"booking_2_chatid_{user_chat_id}_bookingid_{booking.id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Изменить стоимость", callback_data=f"booking_3_chatid_{user_chat_id}_bookingid_{booking.id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Изменить предоплату", callback_data=f"booking_4_chatid_{user_chat_id}_bookingid_{booking.id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Скидка 5%", callback_data=f"booking_5_chatid_{user_chat_id}_bookingid_{booking.id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Скидка 10%", callback_data=f"booking_6_chatid_{user_chat_id}_bookingid_{booking.id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Скидка 15%", callback_data=f"booking_7_chatid_{user_chat_id}_bookingid_{booking.id}_cash_{is_payment_by_cash}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if photo:
        await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo, caption=message, reply_markup=reply_markup)
    elif document:
        await context.bot.send_document(chat_id=ADMIN_CHAT_ID, document=document, caption=message, reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message, reply_markup=reply_markup)

async def edit_accept_booking_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, booking_id: int, user_chat_id: int, is_payment_by_cash):
    booking = database_service.get_booking_by_id(booking_id)
    user = database_service.get_user_by_id(booking.user_id)
    count_booking = database_service.get_done_booking_count(booking.user_id)
    message = string_helper.generate_booking_info_message(booking, user, is_payment_by_cash, count_of_booking=count_booking)
    keyboard = [
        [InlineKeyboardButton("Подтвердить оплату", callback_data=f"booking_1_chatid_{user_chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Отмена бронирования", callback_data=f"booking_2_chatid_{user_chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Изменить стоимость", callback_data=f"booking_3_chatid_{user_chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Изменить предоплату", callback_data=f"booking_4_chatid_{user_chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Скидка 5%", callback_data=f"booking_5_chatid_{user_chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Скидка 10%", callback_data=f"booking_6_chatid_{user_chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Скидка 15%", callback_data=f"booking_7_chatid_{user_chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_caption(caption=message, reply_markup=reply_markup)

async def accept_gift_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, gift: GiftBase, user_chat_id: int, photo, document):
    message = string_helper.generate_gift_info_message(gift)
    keyboard = [
        [InlineKeyboardButton("Подтвердить оплату", callback_data=f"gift_1_chatid_{user_chat_id}_giftid_{gift.id}")],
        [InlineKeyboardButton("Отмена", callback_data=f"gift_2_chatid_{user_chat_id}_giftid_{gift.id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if photo:
        await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo, caption=message, reply_markup=reply_markup)
    elif document:
        await context.bot.send_document(chat_id=ADMIN_CHAT_ID, document=document, caption=message, reply_markup=reply_markup)

async def accept_subscription_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, subscription: SubscriptionBase, user_chat_id: int, photo, document):
    user = database_service.get_user_by_id(subscription.user_id)
    message = string_helper.generate_subscription_info_message(subscription, user)
    keyboard = [
        [InlineKeyboardButton("Подтвердить оплату", callback_data=f"subscription_1_chatid_{user_chat_id}_subscriptionid_{subscription.id}")],
        [InlineKeyboardButton("Отмена", callback_data=f"subscription_2_chatid_{user_chat_id}_subscriptionid_{subscription.id}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if photo:
        await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo, caption=message, reply_markup=reply_markup)
    elif document:
        await context.bot.send_document(chat_id=ADMIN_CHAT_ID, document=document, caption=message, reply_markup=reply_markup)

async def inform_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE, booking: BookingBase):
    user = database_service.get_user_by_id(booking.user_id)
    message = (
        f"Отмена бронирования!\n"
        f"Контакт клиента: {user.contact}\n"
        f"Дата начала: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"Дата завершения: {booking.end_date.strftime('%d.%m.%Y %H:%M')}\n")
    await context.bot.send_message(chat_id=INFORM_CHAT_ID, text=message)

async def inform_changing_booking_date(update: Update, context: ContextTypes.DEFAULT_TYPE, booking: BookingBase, old_start_date: date):
    await inform_cancel_booking(update, context, booking)

    user = database_service.get_user_by_id(booking.user_id)
    message = (
        f"Перенос даты бронирования!\n"
        f"Старая дата начала: {old_start_date.strftime('%d.%m.%Y')}\n\n"
        f"{string_helper.generate_booking_info_message(booking, user)}")
    await context.bot.send_message(chat_id=INFORM_CHAT_ID, text=message)

async def booking_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = string_helper.parse_booking_callback_data(query.data)
    chat_id = data["user_chat_id"] 
    booking_id = data["booking_id"]
    menu_index = data["menu_index"]
    is_payment_by_cash = data["is_payment_by_cash"]

    match menu_index:
        case "1":
            return await approve_booking(update, context, chat_id, booking_id, is_payment_by_cash)
        case "2":
            return await cancel_booking(update, context, chat_id, booking_id)
        case "3":
            return await change_price_message(update, context, chat_id, booking_id, is_payment_by_cash)
        case "4":
            return await change_prepayment_price_message(update, context, chat_id, booking_id, is_payment_by_cash)
        case "5":
            return await set_sale_booking(update, context, chat_id, booking_id, 5, is_payment_by_cash)
        case "6":
            return await set_sale_booking(update, context, chat_id, booking_id, 10, is_payment_by_cash)
        case "7":
            return await set_sale_booking(update, context, chat_id, booking_id, 15, is_payment_by_cash)

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
    
async def approve_booking(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, booking_id: int, is_payment_by_cash: bool):
    (booking, user) = await prepare_approve_process(update, context, booking_id, is_payment_by_cash=is_payment_by_cash)
    await check_and_send_booking(context, booking)
    await context.bot.send_message(
        chat_id=chat_id, 
        text="🎉 <b>Отличные новости!</b> 🎉\n"
            "✅ <b>Ваше бронирование подтверждено администратором.</b>\n"
            "📩 За 1 день до заезда вы получите сообщение с деталями бронирования и инструкцией по заселению.\n"
            f"Общая стоимость бронирования: {booking.price} руб.\n"
            f"Предоплата: {booking.prepayment_price} руб.\n",
        parse_mode='HTML')
    
    text = f"Подтверждено ✅\n\n{string_helper.generate_booking_info_message(booking, user)}"
    message = update.callback_query.message
    if message.caption:
        await message.edit_caption(text)
    else:
        await message.edit_text(text)
        
    return END

async def cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, booking_id: int):
    booking = database_service.update_booking(booking_id, is_canceled=True)
    await context.bot.send_message(
        chat_id=chat_id, 
        text="⚠️ <b>Внимание!</b> ⚠️\n"
            "❌ <b>Ваше бронирование отменено.</b>\n"
            "📞 Администратор свяжется с вами для уточнения деталей.",
        parse_mode='HTML')
    user = database_service.get_user_by_id(booking.user_id)

    text = f"Отмена.\n\n {string_helper.generate_booking_info_message(booking, user)}"
    message = update.callback_query.message
    if message.caption:
        await message.edit_caption(text)
    else:
        await message.edit_text(text)
    return END

async def approve_gift(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, gift_id: int):
    gift = database_service.update_gift(gift_id, is_paymented=True)
    await context.bot.send_message(
        chat_id=chat_id, 
        text=f"{gift.code}")

    await context.bot.send_message(
        chat_id=chat_id, 
        text="🎉 <b>Отличные новости!</b> 🎉\n"
            "✅ <b>Ваш подарочный сертификат подтвержден администратором.</b>\n"
            "📩 <b>В течение нескольких часов мы отправим вам электронный сертификат.</b>\n"
            "🔑 <b>Мы также отправили код сертификата — укажите его при бронировании.</b>",
        parse_mode='HTML')
    await update.callback_query.edit_message_caption(f"Подтверждено \n\n{string_helper.generate_gift_info_message(gift)}")
    return END

async def cancel_gift(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, gift_id: int):
    gift = database_service.get_gift_by_id(gift_id)
    await context.bot.send_message(
        chat_id=chat_id, 
        text="⚠️ <b>Внимание!</b> ⚠️\n"
            "❌ <b>Ваша покупка подарочного сертификата была отменена.</b>\n"
            "📞 Администратор свяжется с вами для уточнения деталей.\n",
        parse_mode='HTML')
    await update.callback_query.edit_message_caption(f"Отмена.\n\n {string_helper.generate_gift_info_message(gift)}")
    return END

async def approve_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, subscription_id: int):
    subscription = database_service.update_subscription(subscription_id, is_paymented=True)
    user = database_service.get_user_by_id(subscription.user_id)
    await context.bot.send_message(
        chat_id=chat_id, 
        text=f"{subscription.code}")

    await context.bot.send_message(
        chat_id=chat_id, 
        text="🎉 <b>Отличные новости!</b> 🎉\n"
            "✅ <b>Покупка абонемента подтверждена администратором.</b>\n"
            "📩 Мы отправили вам код абонемента — укажите его при бронировании.\n",
        parse_mode='HTML')
    await update.callback_query.edit_message_caption(f"Подтверждено \n\n{string_helper.generate_subscription_info_message(subscription, user)}")
    return END

async def cancel_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, subscription_id: int):
    subscription = database_service.get_subscription_by_id(subscription_id)
    user = database_service.get_user_by_id(subscription.user_id)
    await context.bot.send_message(
        chat_id=chat_id, 
        text="⚠️ <b>Внимание!</b> ⚠️\n"
            "❌ <b>Ваша покупка абонемента была отменена.</b>\n"
            "📞 Администратор свяжется с вами для уточнения деталей.\n",
        parse_mode='HTML')
    await update.callback_query.edit_message_caption(f"Отмена.\n\n {string_helper.generate_subscription_info_message(subscription, user)}")
    return END

async def set_sale_booking(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, booking_id: int, sale_percentage: int, is_payment_by_cash: bool):
    (booking, user) = await prepare_approve_process(update, context, booking_id, sale_percentage, is_payment_by_cash=is_payment_by_cash)
    if booking.start_date.date() == date.today():
        await send_booking_details(context, booking)
        
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=chat_id, 
        text="🎉 <b>Отличные новости!</b> 🎉\n"
            "✅ <b>Ваше бронирование подтверждено администратором.</b>\n"
            f"💰 <b>Новая цена:</b> {booking.price}\n"
            "📩 За 1 день до заезда вы получите сообщение с деталями бронирования и инструкцией по заселению.",
        parse_mode='HTML',  
        reply_markup=reply_markup)
    await update.callback_query.edit_message_caption(f"Подтверждено \n\n Скидка: {sale_percentage}% \n\n{string_helper.generate_booking_info_message(booking, user)}")
    return END

def get_future_bookings() -> Sequence[BookingBase]:
    today = date.today()
    max_date_booking = today + relativedelta(months=PERIOD_IN_MONTHS)
    booking_list = database_service.get_booking_by_period(today, max_date_booking, True)
    return booking_list

async def prepare_approve_process(update: Update, context: ContextTypes.DEFAULT_TYPE, booking_id: int, sale_percentage: int = None, is_payment_by_cash: bool = None):
    booking = database_service.get_booking_by_id(booking_id)
    user = database_service.get_user_by_id(booking.user_id)
    calendar_event_id = calendar_service.add_event(booking, user)
    if sale_percentage:
        price = calculation_rate_service.calculate_discounted_price(booking.price, sale_percentage)
    else:
        price = booking.price
    booking = database_service.update_booking(booking_id, price=price, is_prepaymented=True, calendar_event_id=calendar_event_id)
    subscription = check_subscription(booking)
    gift = check_gift(booking, user)
    await inform_message(update, context, booking, user, gift, subscription)
    return (booking, user)

def check_subscription(booking: BookingBase):
    if not booking.subscription_id:
        return
    
    subscription = database_service.get_subscription_by_id(booking.subscription_id)
    subscription.number_of_visits += 1
    is_done = True if subscription.number_of_visits == subscription.subscription_type.value else False
    subscription = database_service.update_subscription(subscription.id, is_done=is_done, number_of_visits=subscription.number_of_visits)

def check_gift(booking: BookingBase, user: UserBase):
    if not booking.gift_id:
        return
    
    gift = database_service.update_gift(booking.gift_id, is_done=True, user_id=user.id)
    return gift

async def inform_message(update: Update, context: ContextTypes.DEFAULT_TYPE, booking: BookingBase, user: UserBase, gift: GiftBase, subscription: SubscriptionBase, is_payment_by_cash: bool = None):
    message = (
        f"Пользователь: {user.contact}\n"
        f"Дата начала: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"Дата завершения: {booking.end_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"Тариф: {tariff_helper.get_name(booking.tariff)}\n")
    
    if gift:
        message += (
            f"Стоимость: {booking.price + gift.price} руб.\n"
            f"Предоплата: {gift.price} руб.\n"
            f"Оплата наличкой: {string_helper.bool_to_str(is_payment_by_cash)}\n"
            f"Подарочный сертификат: Да\n")
    elif subscription:
        message += (
            f"Стоимость: {booking.price} руб.\n"
            f"Предоплата: {subscription.price} руб.\n"
            f"Оплата наличкой: {string_helper.bool_to_str(is_payment_by_cash)}\n"
            f"Абонемент кол. визитов: {subscription.number_of_visits}/{subscription.subscription_type.value}\n")
    else:
        message += (
            f"Стоимость: {booking.price} руб.\n"
            f"Предоплата: {booking.prepayment_price} руб.\n")

    message += (
        f"Фотосессия: {string_helper.bool_to_str(booking.has_photoshoot)}\n"
        f"Сауна: {string_helper.bool_to_str(booking.has_sauna)}\n"
        f"Белая спальня: {string_helper.bool_to_str(booking.has_white_bedroom)}\n"
        f"Зеленая спальня: {string_helper.bool_to_str(booking.has_green_bedroom)}\n"
        f"Секретная комната: {string_helper.bool_to_str(booking.has_secret_room)}\n"
        f"Количество гостей: {booking.number_of_guests}\n"
        f"Комментарий: {booking.comment if booking.comment else ''}\n")

    await context.bot.send_message(chat_id=INFORM_CHAT_ID, text=message)

async def send_booking_details(context: ContextTypes.DEFAULT_TYPE, booking: BookingBase):
    await context.bot.send_message(
        chat_id=booking.chat_id, 
        text="Мы отобразили путь по которому лучше всего доехать до The Secret House.\n"
            "Через 500 метров после ж/д переезда по левую сторону будет оранжевый магазин. После магазина нужно повернуть налево. Это Вам ориентир нужного поворота, далее навигатор Вас привезет правильно.\n"
            "Когда будете ехать вдоль леса, то Вам нужно будет повернуть на садовое товарищество 'Юбилейное-68' (будет вывеска).\n" 
            "ст. Юбилейное-68, ул. Сосновая, д. 2\n\n"
            "Маршрут в Yandex map:\n"
            "https://yandex.com.ge/maps/157/minsk/?l=stv%2Csta&ll=27.297381%2C53.932145&mode=routes&rtext=53.939763%2C27.333107~53.938194%2C27.324665~53.932431%2C27.315410~53.930789%2C27.299320~53.934190%2C27.300387&rtt=auto&ruri=~~~~ymapsbm1%3A%2F%2Fgeo%3Fdata%3DCgo0Mzk0MjMwMTgwErMB0JHQtdC70LDRgNGD0YHRjCwg0JzRltC90YHQutGWINGA0LDRkdC9LCDQltC00LDQvdC-0LLRltGG0LrRliDRgdC10LvRjNGB0LDQstC10YIsINGB0LDQtNCw0LLQvtC00YfQsNC1INGC0LDQstCw0YDRi9GB0YLQstCwINCu0LHRltC70LXQudC90LDQtS02OCwg0KHQsNGB0L3QvtCy0LDRjyDQstGD0LvRltGG0LAsIDIiCg0sZ9pBFZ28V0I%2C&z=16.06 \n\n"
            "Маршрут Google map:\n"
            "https://maps.app.goo.gl/Hsf9Xw69N8tqHyqt5")
    await context.bot.send_message(
        chat_id=booking.chat_id, 
        text="Если Вам нужна будет какая-то помощь или будут вопросы как добраться до дома, то Вы можете связаться с администратором.\n\n"
            f"{ADMINISTRATION_CONTACT}")
    photo = file_service.get_image("key.jpg")
    await context.bot.send_photo(
        chat_id=booking.chat_id, 
        caption="Мы предоставляем самостоятельное заселение.\n"
            f"1. Слева отображена ключница, которая располагается за территорией дома. В которой лежат ключи от ворот и дома. Пароль: {settings_service.password}\n"
            "2. Справа отображен ящик, который располагается на территории дома. В ящик нужно положить подписанный договор и оплату за проживание, если вы платите наличкой.\n\n"
            "Попрошу это сделать в первые 30 мин. Вашего пребывания в The Secret House. Администратор заберет договор и деньги."
            "Договор и ручка будут лежать в дома на острове на кухне. Вложите деньги и договор с розовый конверт.\n\n"
            "Информация для оплаты (Альфа-Банк):\n"
            f"по номеру телефона {BANK_PHONE_NUMBER}\n"
            "или\n"
            f"по номеру карты {BANK_CARD_NUMBER}",
        photo=photo)
    
    if booking.has_sauna:
        await context.bot.send_message(
            chat_id=booking.chat_id, 
            text="Инструкция по включению сауны:\n"
                "1. Подойдите к входной двери.\n"
                "2. По правую руку находился электрический счетчик.\n"
                "3. Все рубильники подписаны. Переключите рубильник с надписей «Сауна».\n"
                "4. Через 1 час сауна нагреется."
                "5. После использования выключите рубильник.\n")

async def send_feedback(context: ContextTypes.DEFAULT_TYPE, booking: BookingBase):
    await context.bot.send_message(
        chat_id=booking.chat_id, 
        text="🏡 The Secret House благодарит вас за выбор нашего дома для аренды! 💫 \n"
            "Мы хотели бы узнать, как Вам понравилось наше обслуживание. Будем благодарны, если вы оставите анономный отзыв по ссылке ниже.\n"
            "Ссылка:\n"
            "https://docs.google.com/forms/d/1FIDlSsLZLWfKOnhAZ8pPKiPEzLcwl5COI7rEIVGgFEM/edit?ts=66719dd9 \n\n"
            "После получения фидбека мы дарим Вам 10% скидки для следующей поездки.")
    
async def check_and_send_booking(context, booking):
    now = datetime.now()
    job_run_time = time(8, 0)

    condition_1 = booking.start_date.date() == now.date() and now.time() > job_run_time
    condition_2 = (booking.start_date.date() == now.date() or booking.start_date.date() - timedelta(days=1) == now.date())  and booking.start_date.time() < job_run_time

    if condition_1 or condition_2:
        await send_booking_details(context, booking)

async def change_prepayment_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    chat_id = update.effective_chat.id
    if str(chat_id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
        return END
    
    data = string_helper.parse_change_price_callback_data(update.callback_query.data, f"^prepayment_(\d|{CONFIRM}|{BACK})_chatid_(\d+)_bookingid_(\d+)_cash_(True|False)$")
    prepayment_data = data["price"]
    chat_id = data["user_chat_id"] 
    booking_id = data["booking_id"]
    is_payment_by_cash = data["is_payment_by_cash"]

    global new_prepayment_price
    if prepayment_data == BACK:
        new_prepayment_price = ''
        await edit_accept_booking_payment(update, context, booking_id, chat_id, is_payment_by_cash)
        return
    elif prepayment_data == CONFIRM:
        database_service.update_booking(booking_id, prepayment=float(new_prepayment_price))
        await edit_accept_booking_payment(update, context, booking_id, chat_id, is_payment_by_cash)
        new_prepayment_price = ''
        return
    
    if prepayment_data.isdigit():
        new_prepayment_price += prepayment_data
    
    return await change_prepayment_price_message(update, context, chat_id, booking_id, is_payment_by_cash)

async def change_prepayment_price_message(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int = None, booking_id: int = None, is_payment_by_cash: bool = None):
    keyboard = [
        [InlineKeyboardButton('1', callback_data=f"prepayment_1_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}"), InlineKeyboardButton('2', callback_data=f"prepayment_2_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}"), InlineKeyboardButton('3', callback_data=f"prepayment_3_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton('4', callback_data=f"prepayment_4_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}"), InlineKeyboardButton('5', callback_data=f"prepayment_5_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}"), InlineKeyboardButton('6', callback_data=f"prepayment_6_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton('7', callback_data=f"prepayment_7_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}"), InlineKeyboardButton('8', callback_data=f"prepayment_8_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}"), InlineKeyboardButton('9', callback_data=f"prepayment_9_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton('Подтвердить', callback_data=f"prepayment_{CONFIRM}_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}"), InlineKeyboardButton('0', callback_data=f"prepayment_0_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}"), InlineKeyboardButton('Отмена', callback_data=f"prepayment_{BACK}_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}")]]

    message = (f"Введите новуй цену для предоплаты. Например 370.\n"
                f"Вы ввели: {new_prepayment_price}\n")
    if update.message:
        await update.message.reply_text(
            text=message, 
            reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.edit_message_caption(
            caption=message, 
            reply_markup=InlineKeyboardMarkup(keyboard))
    return EDIT_BOOKING_PURCHASE

async def change_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    chat_id = update.effective_chat.id
    if str(chat_id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
        return END

    data = string_helper.parse_change_price_callback_data(update.callback_query.data, f"^price_(\d|{CONFIRM}|{BACK})_chatid_(\d+)_bookingid_(\d+)_cash_(True|False)$")
    price_data = data["price"]
    chat_id = data["user_chat_id"] 
    booking_id = data["booking_id"]
    is_payment_by_cash = data["is_payment_by_cash"]

    global new_price
    if price_data == BACK:
        new_price = ''
        await edit_accept_booking_payment(update, context, booking_id, chat_id, is_payment_by_cash)
        return
    elif price_data == CONFIRM:
        database_service.update_booking(booking_id, price=float(new_price))
        await edit_accept_booking_payment(update, context, booking_id, chat_id, is_payment_by_cash)
        new_price = ''
        return
    
    if price_data.isdigit():
        new_price += price_data

    return await change_price_message(update, context, chat_id, booking_id, is_payment_by_cash)
    
async def change_price_message(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int = None, booking_id: int = None, is_payment_by_cash: bool = None):
    keyboard = [
        [InlineKeyboardButton('1', callback_data=f"price_1_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}"), InlineKeyboardButton('2', callback_data=f"price_2_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}"), InlineKeyboardButton('3', callback_data=f"price_3_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton('4', callback_data=f"price_4_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}"), InlineKeyboardButton('5', callback_data=f"price_5_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}"), InlineKeyboardButton('6', callback_data=f"price_6_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton('7', callback_data=f"price_7_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}"), InlineKeyboardButton('8', callback_data=f"price_8_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}"), InlineKeyboardButton('9', callback_data=f"price_9_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton('Подтвердить', callback_data=f"price_{CONFIRM}_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}"), InlineKeyboardButton('0', callback_data=f"price_0_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}"), InlineKeyboardButton('Отмена', callback_data=f"price_{BACK}_chatid_{chat_id}_bookingid_{booking_id}_cash_{is_payment_by_cash}")]]

    message = (f"Введите новуй цену для бронирования. Например 370.\n"
                f"Вы ввели: {new_price}\n")
    if update.message:
        await update.message.reply_text(
            text=message, 
            reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.edit_message_caption(
            caption=message, 
            reply_markup=InlineKeyboardMarkup(keyboard))
    return EDIT_BOOKING_PURCHASE