from datetime import date
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.file_service import FileService
from src.services.calculation_rate_service import CalculationRateService
from db.models.subscription import SubscriptionBase
from db.models.gift import GiftBase
from matplotlib.dates import relativedelta
from src.constants import END
from src.services.calendar_service import CalendarService
from db.models.user import UserBase
from db.models.booking import BookingBase
from src.services.database_service import DatabaseService
from src.config.config import ADMIN_CHAT_ID, PERIOD_IN_MONTHS, INFORM_CHAT_ID, PREPAYMENT, BANK_CARD_NUMBER, BANK_PHONE_NUMBER, ADMINISTRATION_CONTACT, HOUSE_PASSWORD
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes)
from src.helpers import string_helper, string_helper, tariff_helper

database_service = DatabaseService()
calendar_service = CalendarService()
calculation_rate_service = CalculationRateService()
file_service = FileService()

async def get_booking_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if str(chat_id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
    else:
        message = get_future_booking_message()
        await update.message.reply_text(message)

async def accept_booking_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, booking: BookingBase, user_chat_id: int, photo, is_payment_by_cash = False):
    user = database_service.get_user_by_id(booking.user_id)
    message = string_helper.generate_booking_info_message(booking, user, is_payment_by_cash)
    keyboard = [
        [InlineKeyboardButton("Подтвердить оплату", callback_data=f"booking_1_chatid_{user_chat_id}_bookingid_{booking.id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Отмена бронирования", callback_data=f"booking_2_chatid_{user_chat_id}_bookingid_{booking.id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Скидка 5%", callback_data=f"booking_3_chatid_{user_chat_id}_bookingid_{booking.id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Скидка 10%", callback_data=f"booking_4_chatid_{user_chat_id}_bookingid_{booking.id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Скидка 15%", callback_data=f"booking_5_chatid_{user_chat_id}_bookingid_{booking.id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Скидка 20%", callback_data=f"booking_6_chatid_{user_chat_id}_bookingid_{booking.id}_cash_{is_payment_by_cash}")],
        [InlineKeyboardButton("Скидка 30%", callback_data=f"booking_7_chatid_{user_chat_id}_bookingid_{booking.id}_cash_{is_payment_by_cash}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if not photo:
        photo = file_service.get_image("logo.png")

    await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo, caption=message, reply_markup=reply_markup)

async def accept_gift_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, gift: GiftBase, user_chat_id: int, photo):
    message = string_helper.generate_gift_info_message(gift)
    keyboard = [
        [InlineKeyboardButton("Подтвердить оплату", callback_data=f"gift_1_chatid_{user_chat_id}_giftid_{gift.id}")],
        [InlineKeyboardButton("Отмена", callback_data=f"gift_2_chatid_{user_chat_id}_giftid_{gift.id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo, caption=message, reply_markup=reply_markup)

async def accept_subscription_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, subscription: SubscriptionBase, user_chat_id: int, photo):
    user = database_service.get_user_by_id(subscription.user_id)
    message = string_helper.generate_subscription_info_message(subscription, user)
    keyboard = [
        [InlineKeyboardButton("Подтвердить оплату", callback_data=f"subscription_1_chatid_{user_chat_id}_subscriptionid_{subscription.id}")],
        [InlineKeyboardButton("Отмена", callback_data=f"subscription_2_chatid_{user_chat_id}_subscriptionid_{subscription.id}")],
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
    is_payment_by_cash = data["is_payment_by_cash"]

    match menu_index:
        case "1":
            await approve_booking(update, context, chat_id, booking_id, is_payment_by_cash)
        case "2":
            await cancel_booking(update, context, chat_id, booking_id)
        case "3":
            await set_sale_booking(update, context, chat_id, booking_id, 5, is_payment_by_cash)
        case "4":
            await set_sale_booking(update, context, chat_id, booking_id, 10, is_payment_by_cash)
        case "5":
            await set_sale_booking(update, context, chat_id, booking_id, 15, is_payment_by_cash)
        case "6":
            await set_sale_booking(update, context, chat_id, booking_id, 20, is_payment_by_cash)
        case "7":
            await set_sale_booking(update, context, chat_id, booking_id, 30, is_payment_by_cash)

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
    if booking.start_date.date() == date.today():
        await send_booking_details(context, booking)

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
        text=f"{gift.code}")

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
        text=f"{subscription.code}")

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

async def set_sale_booking(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, booking_id: int, sale_percentage: int, is_payment_by_cash: bool):
    (booking, user) = await prepare_approve_process(update, context, booking_id, sale_percentage, is_payment_by_cash=is_payment_by_cash)
    if booking.start_date.date() == date.today():
        await send_booking_details(context, booking)
        
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
            f"Предоплата: {PREPAYMENT} руб.\n")

    message += (
        f"Фотосессия: {string_helper.bool_to_str(booking.has_photoshoot)}\n"
        f"Сауна: {string_helper.bool_to_str(booking.has_sauna)}\n"
        f"Белая спальня: {string_helper.bool_to_str(booking.has_white_bedroom)}\n"
        f"Зеленая спальня: {string_helper.bool_to_str(booking.has_green_bedroom)}\n"
        f"Секретная комната спальня: {string_helper.bool_to_str(booking.has_secret_room)}\n"
        f"Колличество гостей: {booking.number_of_guests}\n"
        f"Комментарий: {booking.comment if booking.comment else ''}\n")

    await context.bot.send_message(chat_id=INFORM_CHAT_ID, text=message)

async def send_booking_details(context: ContextTypes.DEFAULT_TYPE, booking: BookingBase):
    await context.bot.send_message(
        chat_id=booking.chat_id, 
        text="Мы отобразили путь по которому лучше всего доехать до The Secret House.\n"
            "Через 500 метров после ж/д переезда по левую сторону будет оранжевый магазин. После магазина нужно повернуть налево. Это Вам ориентир нужного поворота, далее навигатор Вас привезет правильно.\n"
            "Когда будете ехать вдоль леса, то Вам нужно будет повернуть на садовое товарищество 'Юбилейное-68' (будет вывеска).\n" 
            "ст. Юбилейное-68, ул. Сосновая, д. 2\n\n"
            "Yandex map:\n"
            "https://yandex.com.ge/maps/157/minsk/?l=stv%2Csta&ll=27.297381%2C53.932145&mode=routes&rtext=53.939763%2C27.333107~53.938194%2C27.324665~53.932431%2C27.315410~53.930789%2C27.299320~53.934190%2C27.300387&rtt=auto&ruri=~~~~ymapsbm1%3A%2F%2Fgeo%3Fdata%3DCgo0Mzk0MjMwMTgwErMB0JHQtdC70LDRgNGD0YHRjCwg0JzRltC90YHQutGWINGA0LDRkdC9LCDQltC00LDQvdC-0LLRltGG0LrRliDRgdC10LvRjNGB0LDQstC10YIsINGB0LDQtNCw0LLQvtC00YfQsNC1INGC0LDQstCw0YDRi9GB0YLQstCwINCu0LHRltC70LXQudC90LDQtS02OCwg0KHQsNGB0L3QvtCy0LDRjyDQstGD0LvRltGG0LAsIDIiCg0sZ9pBFZ28V0I%2C&z=16.06 \n\n"
            "Google map:\n"
            "https://maps.app.goo.gl/Hsf9Xw69N8tqHyqt5")
    await context.bot.send_message(
        chat_id=booking.chat_id, 
        text="Если Вам нужна будет какая-то помощь или будут вопросы как добраться до дома, то Вы можете связаться с администратором.\n\n"
            f"{ADMINISTRATION_CONTACT}")
    photo = file_service.get_image("key.jpg")
    await context.bot.send_photo(
        chat_id=booking.chat_id, 
        caption="Мы предоставляем самостоятельное заселение.\n"
            f"1. Слева отображена ключница, которая располагается за территорией дома. В которой лежат ключи от ворот и дома. Пароль: {HOUSE_PASSWORD}\n"
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
        
    # keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    # reply_markup = InlineKeyboardMarkup(keyboard)    
    # await context.bot.send_message(
    #         chat_id=user.chat_id, 
    #         text="Инструкция по включению сауны:\n"
    #             "1. Подойдите к входной двери.\n"
    #             "2. По правую руку находился электрический счетчик.\n"
    #             "3. Все рубильники подписаны. Переключите рубильник с надписей «Сауна».\n"
    #             "4. Через 1 час сауна нагреется."
    #             "5. После использования выключите рубильник.\n")

async def send_feedback(context: ContextTypes.DEFAULT_TYPE, booking: BookingBase):
    await context.bot.send_message(
        chat_id=booking.chat_id, 
        text="The Secret House благодарит Вас за то, что выбрали наш дом для аренды! \n"
            "Мы хотели бы узнать, как Вам понравилось наше обслуживание. Будем благодарны, если вы оставите анономный отзыв по ссылке ниже.\n"
            "Ссылка:\n"
            "https://docs.google.com/forms/d/1FIDlSsLZLWfKOnhAZ8pPKiPEzLcwl5COI7rEIVGgFEM/edit?ts=66719dd9 \n\n"
            "После получения фидбека мы дарим Вам 10% скидки для следующей поездки.")