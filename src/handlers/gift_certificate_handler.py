import sys
import os

from src.services.database_service import DatabaseService
from src.services.logger_service import LoggerService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.models.rental_price import RentalPrice
from src.config.config import BANK_PHONE_NUMBER, BANK_CARD_NUMBER
from src.services.calculation_rate_service import CalculationRateService
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters)
from src.handlers import admin_handler, menu_handler
from src.helpers import string_helper, tariff_helper
from src.models.enum.tariff import Tariff
from src.constants import (
    BACK, 
    END,
    MENU, 
    STOPPING, 
    GIFT_CERTIFICATE, 
    SET_USER,
    VALIDATE_USER, 
    SELECT_TARIFF, 
    ADDITIONAL_BEDROOM,
    INCLUDE_SECRET_ROOM, 
    INCLUDE_SAUNA, 
    PAY,
    CONFIRM_PAY,
    CONFIRM,
    PHOTO_UPLOAD)

user_contact: str
tariff: Tariff
is_sauna_included: bool
is_secret_room_included: bool
is_additional_bedroom_included: bool
rate_service = CalculationRateService()
database_service = DatabaseService()
rental_rate: RentalPrice
price: int

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(generate_tariff_menu, pattern=f"^{str(GIFT_CERTIFICATE)}$")],
        states={
            SET_USER: [CallbackQueryHandler(enter_user_contact)],
            VALIDATE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_user_contact)],
            SELECT_TARIFF: [CallbackQueryHandler(select_tariff)],
            INCLUDE_SECRET_ROOM: [CallbackQueryHandler(include_secret_room)],
            INCLUDE_SAUNA: [CallbackQueryHandler(include_sauna)],
            ADDITIONAL_BEDROOM: [CallbackQueryHandler(select_additional_bedroom)],
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
    LoggerService.info(f"gift_certificate_handler: Back to menu", update)
    await menu_handler.show_menu(update, context)
    return END

async def enter_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(f"gift_certificate_handler: enter user contact", update)
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

async def generate_tariff_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(f"gift_certificate_handler: generate tariff menu", update)
    reset_variables()
    keyboard = [
        [InlineKeyboardButton(
            f"{tariff_helper.get_name(Tariff.INCOGNITA_DAY)}. Сумма {rate_service.get_price(Tariff.INCOGNITA_DAY)} руб", 
            callback_data=f"{Tariff.INCOGNITA_DAY.value}")],
        [InlineKeyboardButton(
            f"{tariff_helper.get_name(Tariff.INCOGNITA_HOURS)}. Сумма {rate_service.get_price(Tariff.INCOGNITA_HOURS)} руб",
            callback_data=f"{Tariff.INCOGNITA_HOURS.value}")],
        [InlineKeyboardButton(
            f"{tariff_helper.get_name(Tariff.DAY)}. Сумма {rate_service.get_price(Tariff.DAY)} руб",
            callback_data=f"{Tariff.DAY.value}")],
        [InlineKeyboardButton(
            f"{tariff_helper.get_name(Tariff.HOURS_12)}. Сумма от {rate_service.get_price(Tariff.HOURS_12)} руб",
            callback_data=f"{Tariff.HOURS_12.value}")],
        [InlineKeyboardButton(
            f"{tariff_helper.get_name(Tariff.WORKER)}. Сумма от {rate_service.get_price(Tariff.WORKER)} руб",
            callback_data=f"{Tariff.WORKER.value}")],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="🎟 <b>Выберите тариф для сертификата.</b>",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return SELECT_TARIFF    

async def check_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user_input = update.message.text
        is_valid = string_helper.is_valid_user_contact(user_input)
        if is_valid:
            global user_contact
            user_contact = user_input
            return await confirm_pay(update, context)
        else:
            LoggerService.warning(f"gift_certificate_handler: user name is invalid", update)
            await update.message.reply_text(
                "❌ <b>Ошибка!</b>\n"
                "Имя пользователя в Telegram или номер телефона введены некорректно.\n\n"
                "🔄 Пожалуйста, попробуйте еще раз.",
                parse_mode='HTML'   
            )
    return VALIDATE_USER

async def select_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = update.callback_query.data
    if (data == str(END)):
        return await back_navigation(update, context)

    global tariff, rental_rate
    tariff = tariff_helper.get_by_str(data)
    rental_rate = rate_service.get_tariff(tariff)
    LoggerService.warning(f"gift_certificate_handler: select tariff: {tariff}", update)

    if tariff == Tariff.DAY or tariff == Tariff.INCOGNITA_HOURS or tariff == Tariff.INCOGNITA_DAY:
        global is_sauna_included, is_secret_room_included, is_additional_bedroom_included
        is_sauna_included = True
        is_secret_room_included = True
        is_additional_bedroom_included = True
        return await enter_user_contact(update, context)
    elif tariff == Tariff.HOURS_12 or tariff == Tariff.WORKER:
        return await additional_bedroom_message(update, context)

async def select_additional_bedroom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    if (update.callback_query.data == str(END)):
        return await back_navigation(update, context)

    global is_additional_bedroom_included
    is_additional_bedroom_included = eval(update.callback_query.data)
    LoggerService.warning(f"gift_certificate_handler: select additional bedroom: {is_additional_bedroom_included}", update)
    return await secret_room_message(update, context)

async def include_secret_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = update.callback_query.data
    if (data == str(END)):
        return await back_navigation(update, context)

    global is_secret_room_included
    is_secret_room_included = eval(data)
    LoggerService.warning(f"gift_certificate_handler: include secret room: {is_secret_room_included}", update)
    return await sauna_message(update, context)

async def include_sauna(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = update.callback_query.data
    if (data == str(END)):
        return await back_navigation(update, context)

    global is_sauna_included
    is_sauna_included = eval(update.callback_query.data)
    LoggerService.warning(f"gift_certificate_handler: include sauna: {is_sauna_included}", update)
    return await enter_user_contact(update, context)

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    if (update.callback_query.data == str(END)):
        return await back_navigation(update, context)
    
    LoggerService.warning(f"gift_certificate_handler: pay", update)
    keyboard = [[InlineKeyboardButton("Отмена", callback_data=BACK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        text=f"💰 <b>Общая сумма оплаты:</b> {price} руб.\n\n"
            "📌 <b>Информация для оплаты (Альфа-Банк):</b>\n"
            f"📱 По номеру телефона: <b>{BANK_PHONE_NUMBER}</b>\n"
            "или\n"
            f"💳 По номеру карты: <b>{BANK_CARD_NUMBER}</b>\n\n"
            "❗️ <b>После оплаты отправьте скриншот с чеком об оплате.</b>\n"
            "К сожалению, только так мы можем подтвердить, что именно вы отправили предоплату.\n"
            "🙏 Спасибо за понимание.\n\n"
            "✅ Как только мы получим оплату, администратор свяжется с вами и отправит ваш <b>электронный подарочный сертификат</b>.",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return PHOTO_UPLOAD

async def confirm_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Перейти к оплате.", callback_data=PAY)],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    global price
    price = rate_service.calculate_price(rental_rate, is_sauna_included, is_secret_room_included, is_additional_bedroom_included)
    categories = rate_service.get_price_categories(rental_rate, is_sauna_included, is_secret_room_included, is_additional_bedroom_included)
    LoggerService.warning(f"gift_certificate_handler: confirm pay: {price}", update)
    await update.message.reply_text(
        text=f"💰 <b>Общая сумма оплаты:</b> {price} руб.\n"
            f"📌 <b>В стоимость входит:</b> {categories}.\n\n"
            "✅ <b>Подтверждаете покупку сертификата?</b>",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return PAY

async def secret_room_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    
    keyboard = [
        [InlineKeyboardButton("Да", callback_data=str(True))],
        [InlineKeyboardButton("Нет", callback_data=str(False))],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text="🔞 <b>Планируете ли вы пользоваться 'Секретной комнатой'?</b>\n\n"
            f"💰 <b>Стоимость:</b> {rental_rate.secret_room_price} руб. \n"
            f"📌 <b>Для тарифа:</b> {tariff_helper.get_name(tariff)}",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return INCLUDE_SECRET_ROOM

async def sauna_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Да", callback_data=str(True))],
        [InlineKeyboardButton("Нет", callback_data=str(False))],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
    text="🧖‍♂️ <b>Планируете ли вы пользоваться сауной?</b>\n\n"
        f"💰 <b>Стоимость:</b> {rental_rate.sauna_price} руб.\n"
        f"📌 <b>Для тарифа:</b> {tariff_helper.get_name(tariff)}",
    reply_markup=reply_markup)
    return INCLUDE_SAUNA

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def additional_bedroom_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Да", callback_data=str(True))],
        [InlineKeyboardButton("Нет", callback_data=str(False))],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="🛏 <b>Планируете ли вы пользоваться второй спальней комнатой?</b>\n\n"
            f"💰 <b>Стоимость:</b> {rental_rate.second_bedroom_price} руб.\n"
            f"📌 <b>Для тарифа:</b> {tariff_helper.get_name(tariff)}",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return ADDITIONAL_BEDROOM

def save_gift_information():
    code = string_helper.get_generated_code()
    gift = database_service.add_gift(user_contact, tariff, is_sauna_included, is_secret_room_included, is_additional_bedroom_included, price, code)
    return gift

def reset_variables():
    global user_contact, tariff, is_sauna_included, is_secret_room_included, is_additional_bedroom_included, rental_rate, price
    user_contact = None
    tariff = None
    is_sauna_included = None
    is_secret_room_included = None
    is_additional_bedroom_included = None
    rental_rate = None
    price = None

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global photo
    photo = update.message.photo[-1].file_id
    chat_id = update.message.chat.id
    gift = save_gift_information()
    LoggerService.warning(f"gift_certificate_handler: handle photo", update)
    await admin_handler.accept_gift_payment(update, context, gift, chat_id, photo)
    return await confirm_booking(update, context)