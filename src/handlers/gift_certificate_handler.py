import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters)
from src.handlers import menu_handler
from src.helpers import string_helper, tariff_helper
from src.models.enum.tariff import Tariff
from src.constants import (
    BACK, 
    END,
    MENU, 
    STOPPING, 
    GIFT_CERTIFICATE, 
    VALIDATE_USER, 
    SELECT_TARIFF, 
    INCLUDE_SECRET_ROOM, 
    INCLUDE_SAUNA, 
    PAY,
    CONFIRM_PAY,
    CONFIRM)

user_contact = ""
tariff = Tariff
is_sauna_included = False
is_secret_room_included = False

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(enter_user_contact, pattern=f"^{str(GIFT_CERTIFICATE)}$")],
        states={
            VALIDATE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_user_contact)],
            SELECT_TARIFF: [CallbackQueryHandler(select_tariff)],
            INCLUDE_SECRET_ROOM: [CallbackQueryHandler(include_secret_room)],
            INCLUDE_SAUNA: [CallbackQueryHandler(include_sauna)],
            CONFIRM_PAY: [CallbackQueryHandler(confirm_pay)],
            PAY: [CallbackQueryHandler(pay)],
            CONFIRM: [CallbackQueryHandler(confirm_booking, pattern=f"^{str(CONFIRM)}$")],
            BACK: [CallbackQueryHandler(back_navigation, pattern=f"^{str(BACK)}$")],
        },
        fallbacks=[CallbackQueryHandler(back_navigation, pattern=f"^{str(END)}$")],
        map_to_parent={
            END: MENU,
            STOPPING: END,
        })
    return handler

async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler.show_menu(update, context)
    return END

async def enter_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=str(END))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Напишите Ваш <b>Telegram</b>.\n"
        "Формат ввода @user_name (обязательно начинайте ввод с @).\n"
        "Формат ввода номера телефона +375251111111 (обязательно начинайте ввод с +375).\n",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return VALIDATE_USER

async def check_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user_input = update.message.text
        is_valid = string_helper.is_valid_user_contact(user_input)
        if is_valid:
            global user_contact
            user_contact = user_input

            keyboard = [
                [InlineKeyboardButton(tariff_helper.get_name(Tariff.INCOGNITA), callback_data=f"{Tariff.INCOGNITA.value}")],
                [InlineKeyboardButton(tariff_helper.get_name(Tariff.DAY), callback_data=f"{Tariff.DAY.value}")],
                [InlineKeyboardButton(tariff_helper.get_name(Tariff.HOURS_12), callback_data=f"{Tariff.HOURS_12.value}")],
                [InlineKeyboardButton(tariff_helper.get_name(Tariff.WORKER), callback_data=f"{Tariff.WORKER.value}")],
                [InlineKeyboardButton("Назад в меню", callback_data=str(END))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                text="Выберете тариф для сертификата.\n",
                reply_markup=reply_markup)
            return SELECT_TARIFF
        else:
            await update.message.reply_text("Ошибка: имя пользователя в Telegram или номер телефона введены не коректно.\n"
                                            "Повторите ввод еще раз.")
    else:
        await update.message.reply_text("Ошибка: Пустая строка.\n"
                                        "Повторите ввод еще раз.")

    return VALIDATE_USER

async def select_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = update.callback_query.data
    if (data == str(END)):
        return await back_navigation(update, context)

    global tariff
    tariff = tariff_helper.get_by_str(data)
    if tariff == Tariff.DAY:
        return await confirm_pay(update)
    elif tariff == Tariff.INCOGNITA:
        return await confirm_pay(update)
    elif tariff == Tariff.HOURS_12:
        return await secret_room_message(update)
    elif tariff == Tariff.WORKER:
        return await secret_room_message(update)

async def include_secret_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = update.callback_query.data
    if (data == str(END)):
        return await back_navigation(update, context)

    global is_secret_room_included
    is_secret_room_included = bool(data)

    return await sauna_message(update)

async def include_sauna(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = update.callback_query.data
    if (data == str(END)):
        return await back_navigation(update, context)

    global is_sauna_included
    is_sauna_included = bool(update.callback_query.data)
    return await confirm_pay(update)

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    if (update.callback_query.data == str(END)):
        return await back_navigation(update, context)
    
    keyboard = [
        [InlineKeyboardButton("Подтвердить оплату.", callback_data=str(CONFIRM))],
        [InlineKeyboardButton("Отмена", callback_data=str(END))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    price = 123

    await update.callback_query.edit_message_text(
    text=f"Общая сумма оплаты {price} BYN.\n"
        "\n"
        "Информация для оплаты (Альфа-Банк):\n"
        "по номеру телефона +375257908378\n"
        "или\n"
        "по номеру карты 4373 5000 0654 0553 ANTON TERESHKO\n"
        "\n"
        "После оплаты нажмите на кнопку 'Подтвердить оплату'.\n"
        "Как только мы получим средства, то свяжемся с Вами и вышлем Вам электронный подарочный сертификат.\n",
    reply_markup=reply_markup)
    return CONFIRM

async def confirm_pay(update: Update):
    keyboard = [
        [InlineKeyboardButton("Перейти к оплате.", callback_data=str(PAY))],
        [InlineKeyboardButton("Назад в меню", callback_data=str(END))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    price = 123

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
    text=f"Общая сумма оплаты {price} BYN.\n"
        "В стоимость входит: НУЖЕН СПИСОК.\n"
        "\n"
        "Подтверждаете покупку сертификата?\n",
    reply_markup=reply_markup)
    return PAY

async def secret_room_message(update: Update):
    await update.callback_query.answer()
    
    keyboard = [
        [InlineKeyboardButton("Да", callback_data=str(True))],
        [InlineKeyboardButton("Нет", callback_data=str(False))],
        [InlineKeyboardButton("Назад в меню", callback_data=str(END))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text="Планируете ли Вы пользоваться 'Секретной комнатой'?\n"
            f"Стоимость СУММА для тарифа '{tariff_helper.get_tariff_name(tariff)}'.",
    reply_markup=reply_markup)
    return INCLUDE_SECRET_ROOM

async def sauna_message(update: Update):
    keyboard = [
        [InlineKeyboardButton("Да", callback_data=str(True))],
        [InlineKeyboardButton("Нет", callback_data=str(False))],
        [InlineKeyboardButton("Назад в меню", callback_data=str(END))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
    text="Планируете ли Вы пользоваться сауной?\n"
        f"Стоимость СУММА для тарифа '{tariff_helper.get_name(tariff)}'.",
    reply_markup=reply_markup)
    return INCLUDE_SAUNA

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=str(END))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Спасибо Вам за доверие к The Secret House.\n"
            "Скоро мы свяжемся с Вами.\n",
        reply_markup=reply_markup)
    return MENU

def extract_data(text):
    return int(text.split("_")[1])