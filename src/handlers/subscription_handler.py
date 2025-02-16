import sys
import os

from src.services.logger_service import LoggerService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.database_service import DatabaseService
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters)
from src.config.config import BANK_PHONE_NUMBER, BANK_CARD_NUMBER
from src.handlers import admin_handler, menu_handler
from src.helpers import string_helper, subscription_helper
from src.models.enum.subscription_type import SubscriptionType
from src.models.rental_price import RentalPrice
from src.services.calculation_rate_service import CalculationRateService
from src.constants import (
    BACK, 
    END,
    MENU, 
    STOPPING, 
    SET_USER,
    VALIDATE_USER, 
    SUBSCRIPTION,
    SUBSCRIPTION_TYPE,
    PAY,
    CONFIRM_PAY,
    CONFIRM,
    PHOTO_UPLOAD)

user_contact: str
subscription_type: SubscriptionType
rate_service = CalculationRateService()
database_service = DatabaseService()
rental_rate: RentalPrice
price: int

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(generate_subscription_menu, pattern=f"^{str(SUBSCRIPTION)}$")],
        states={
            SET_USER: [CallbackQueryHandler(enter_user_contact)],
            VALIDATE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_user_contact)],
            SUBSCRIPTION_TYPE: [CallbackQueryHandler(select_subscription_type)],
            CONFIRM_PAY: [CallbackQueryHandler(confirm_pay)],
            PAY: [CallbackQueryHandler(pay)],
            CONFIRM: [CallbackQueryHandler(confirm_booking, pattern=f"^{CONFIRM}$")],
            BACK: [CallbackQueryHandler(back_navigation, pattern=f"^{BACK}$")],
            PHOTO_UPLOAD: [
                MessageHandler(filters.PHOTO, handle_photo),
                CallbackQueryHandler(back_navigation, pattern=f"^{BACK}$")],
        },
        fallbacks=[CallbackQueryHandler(back_navigation, pattern=f"^{END}$")],
        map_to_parent={
            END: MENU,
            STOPPING: END,
        })
    return handler

async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler.show_menu(update, context)
    LoggerService.info(__name__, "Back to menu", update)
    return END

async def enter_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, "Enter user contact", update)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="📲 Укажите ваш <b>Telegram</b> или номер телефона:\n\n"
            "🔹 <b>Telegram:</b> @username (начинайте с @)\n"
            "🔹 <b>Телефон:</b> +375XXXXXXXXX (обязательно с +375)\n"
            "❗️ Пожалуйста, вводите данные строго в указанном формате.",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return VALIDATE_USER

async def generate_subscription_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, "Generate subscription menu", update)
    reset_variables()
    keyboard = [
        [InlineKeyboardButton(
            f"{subscription_helper.get_name(SubscriptionType.VISITS_3)}. Сумма {rate_service.get_price(subscription_type = SubscriptionType.VISITS_3)} руб", 
            callback_data=f"{SubscriptionType.VISITS_3.value}")],
        [InlineKeyboardButton(
            f"{subscription_helper.get_name(SubscriptionType.VISITS_5)}. Сумма {rate_service.get_price(subscription_type = SubscriptionType.VISITS_5)} руб", 
            callback_data=f"{SubscriptionType.VISITS_5.value}")],
        [InlineKeyboardButton(
            f"{subscription_helper.get_name(SubscriptionType.VISITS_8)}. Сумма {rate_service.get_price(subscription_type = SubscriptionType.VISITS_8)} руб", 
            callback_data=f"{SubscriptionType.VISITS_8.value}")],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="📌 <b>Выберите удобный абонемент</b>.\n\n"
            "Каждый абонемент включает:\n"
            "🏠 Аренду на <b>12 часов</b>\n"
            "🛏 <b>2 спальные комнаты</b>\n"
            "🔞 <b>Секретную комнату</b>",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return SUBSCRIPTION_TYPE

async def check_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user_input = update.message.text
        is_valid = string_helper.is_valid_user_contact(user_input)
        if is_valid:
            global user_contact
            user_contact = user_input
            return await confirm_pay(update, context)
        else:
            LoggerService.warning(__name__, "User name is invalid", update)
            await update.message.reply_text(
                "❌ <b>Ошибка!</b>\n"
                "Имя пользователя в Telegram или номер телефона введены некорректно.\n\n"
                "🔄 Пожалуйста, попробуйте еще раз.",
                parse_mode='HTML',)

    return VALIDATE_USER

async def select_subscription_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = update.callback_query.data
    if (data == str(END)):
        return await back_navigation(update, context)

    global subscription_type, rental_rate
    subscription_type = subscription_helper.get_by_str(data)
    LoggerService.info(__name__, f"select subscription type", update, kwargs={'subscription_type': subscription_type})
    rental_rate = rate_service.get_subscription(subscription_type)

    return await enter_user_contact(update, context)

async def confirm_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, f"confirm pay", update)
    keyboard = [
        [InlineKeyboardButton("Перейти к оплате.", callback_data=PAY)],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    global price
    price = rate_service.calculate_price(rental_rate, False, True, True)
    categories = rate_service.get_price_categories(rental_rate, False, True, True)

    await update.message.reply_text(
        text=f"💰 <b>Общая сумма оплаты:</b> {price} руб.\n\n"
            f"📌 <b>В стоимость входит:</b> {categories}.\n\n"
            "✅ <b>Подтверждаете покупку абонемента?</b>",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return PAY

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    if (update.callback_query.data == str(END)):
        return await back_navigation(update, context)
    
    keyboard = [[InlineKeyboardButton("Отмена", callback_data=BACK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    price = rental_rate.price
    LoggerService.info(__name__, f"pay", update, kwargs={'price': price})

    await update.callback_query.edit_message_text(
        text=f"💰 <b>Общая сумма оплаты:</b> {price} руб.\n\n"
            "📌 <b>Информация для оплаты (Альфа-Банк):</b>\n"
            f"📱 По номеру телефона: <b>{BANK_PHONE_NUMBER}</b>\n"
            "или\n"
            f"💳 По номеру карты: <b>{BANK_CARD_NUMBER}</b>\n\n"
            "⚠️ <b>После оплаты отправьте скриншот с чеком об оплате.</b>\n"
            "К сожалению, только так мы можем подтвердить, что именно Вы отправили предоплату.\n\n"
            "✅ Как только мы получим средства, администратор свяжется с вами и отправит электронный код.\n"
            "🔑 Код можно ввести в разделе <b>«Забронировать»</b> – бронирования будут списываться автоматически.\n\n"
            "🔒 <b>Держите код в тайне!</b>",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return PHOTO_UPLOAD

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, f"confirm booking", update)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="🙏 <b>Спасибо за доверие к The Secret House!</b>\n\n"
            "📩 Ваша заявка получена.\n"
            "🔍 Администратор проверит оплату и свяжется с вами в ближайшее время.\n\n"
            "⏳ Пожалуйста, ожидайте подтверждения.",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return MENU

def save_subscription_information():
    code = string_helper.get_generated_code()
    subscription = database_service.add_subscription(user_contact, subscription_type, price, code)
    return subscription

def reset_variables():
    global user_contact, subscription_type, rental_rate, price
    user_contact = None
    subscription_type = None
    rental_rate = None
    price = None

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global photo
    photo = update.message.photo[-1].file_id
    chat_id = update.message.chat.id
    subscription = save_subscription_information()
    LoggerService.info(__name__, f"handle photo", update)
    await admin_handler.accept_subscription_payment(update, context, subscription, chat_id, photo)
    return await confirm_booking(update, context)