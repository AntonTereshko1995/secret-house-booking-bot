import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters)
from src.handlers import menu_handler
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
    CONFIRM)

user_contact: str
subscription_type: SubscriptionType
rate_service = CalculationRateService()
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
        },
        fallbacks=[CallbackQueryHandler(back_navigation, pattern=f"^{END}$")],
        map_to_parent={
            END: MENU,
            STOPPING: END,
        })
    return handler

async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler.show_menu(update, context)
    return END

async def enter_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Напишите Ваш <b>Telegram</b>.\n"
            "Формат ввода @user_name (обязательно начинайте ввод с @).\n"
            "Формат ввода номера телефона +375251111111 (обязательно начинайте ввод с +375).\n",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return VALIDATE_USER

async def generate_subscription_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        text="Выберете удобный для Вас абонемент.\n"
            "В каждый абонемент входит аренда на 12 часов, 2 спальные комнаты и секретная комната.\n",
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
            await update.message.reply_text("Ошибка: имя пользователя в Telegram или номер телефона введены не коректно.\n"
                                            "Повторите ввод еще раз.")
    else:
        await update.message.reply_text("Ошибка: Пустая строка.\n"
                                        "Повторите ввод еще раз.")

    return VALIDATE_USER

async def select_subscription_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = update.callback_query.data
    if (data == str(END)):
        return await back_navigation(update, context)

    global subscription_type, rental_rate
    subscription_type = subscription_helper.get_by_str(data)
    rental_rate = rate_service.get_subscription(subscription_type)

    return await enter_user_contact(update, context)

async def confirm_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Перейти к оплате.", callback_data=PAY)],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    global price
    price = rate_service.calculate_price(rental_rate, False, True, True)
    categories = rate_service.get_price_categories(rental_rate, False, True, True)

    await update.message.reply_text(
    text=f"Общая сумма оплаты {price} руб.\n"
        f"В стоимость входит: {categories}.\n"
        "\n"
        "Подтверждаете покупку абонемента?\n",
    reply_markup=reply_markup)
    return PAY

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    if (update.callback_query.data == str(END)):
        return await back_navigation(update, context)
    
    keyboard = [
        [InlineKeyboardButton("Подтвердить оплату.", callback_data=CONFIRM)],
        [InlineKeyboardButton("Отмена", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    price = 123

    await update.callback_query.edit_message_text(
    text=f"Общая сумма оплаты {price} руб.\n"
        "\n"
        "Информация для оплаты (Альфа-Банк):\n"
        "по номеру телефона +375257908378\n"
        "или\n"
        "по номеру карты 4373 5000 0654 0553 ANTON TERESHKO\n"
        "\n"
        "После оплаты нажмите на кнопку 'Подтвердить оплату'.\n"
        "Как только мы получим средства, то свяжемся с Вами и вышлем Вам электронный код.\n"
        "Код мы можете вводить в пункте меню 'Забронировать' и автоматически будут списываться брони.\n"
        "Держите код в тайне!\n",
    reply_markup=reply_markup)
    return CONFIRM

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Спасибо Вам за доверие к The Secret House.\n"
            "Скоро мы свяжемся с Вами.\n",
        reply_markup=reply_markup)
    return MENU