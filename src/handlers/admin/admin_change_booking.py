import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.helpers import string_helper
from src.services.logger_service import LoggerService
from src.services.database_service import DatabaseService
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters)
from src.handlers import admin_handler
from src.constants import (
    CHANGE_BOOKING_ADMIN, 
    END,
    CHANGE_PREPAYMENT_PRICE, 
    SET_ADMIN_COMMENT, 
    CHANGE_PRICE,
    SET_USER,
    BACK,
    UPDATE_BOOKING)

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(generate_edit_menu, pattern=f"^{str(CHANGE_BOOKING_ADMIN)}_bookingid_$")],
        states={
            CHANGE_BOOKING_ADMIN: [CallbackQueryHandler(select_edit_menu)],
            CHANGE_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_price)],
            CHANGE_PREPAYMENT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_prepayment_price)],
            SET_ADMIN_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_admin_comment)],
            BACK: [CallbackQueryHandler(booking_info, pattern=f"^{str(BACK)}$")]
        },
        fallbacks=[],
        map_to_parent={
            END: END,
        })
    return handler

async def generate_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, f"Generate tariff", update)
    keyboard = [
        [InlineKeyboardButton(
            f"Изменить стоимость бронирования",
            callback_data=CHANGE_PRICE)], 
        [InlineKeyboardButton(
            f"Изменить стоимость предоплаты",
            callback_data=CHANGE_PREPAYMENT_PRICE)],
        [InlineKeyboardButton(
            f"Добавить комментарий от администратора",
            callback_data=SET_ADMIN_COMMENT)],
        [InlineKeyboardButton(
            f"Назад к бронированию", 
            callback_data=BACK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="<b>Выберите свойство,которое хотите изменить</b>",
        parse_mode='HTML',
        reply_markup=reply_markup)
    return CHANGE_BOOKING_ADMIN

async def select_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, f"Select tariff", update)
    await update.callback_query.answer()
    data = update.callback_query.data
    if data == CHANGE_PRICE:
        await update.callback_query.edit_message_text(text="Введите новую стоимость бронирования. Пример 370.")
        return CHANGE_PRICE
    elif data == CHANGE_PREPAYMENT_PRICE:
        await update.callback_query.edit_message_text(text="Введите новую цену предоплаты. Пример 370.")
        return CHANGE_PREPAYMENT_PRICE
    elif data == SET_ADMIN_COMMENT:
        await update.callback_query.edit_message_text(text="Введите комментарий от администратора.")
        return SET_ADMIN_COMMENT

async def change_prepayment_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, "Change prepayment price triggered", update)
    await update.message.reply_text("Change prepayment price functionality is not yet implemented.")
    return await generate_edit_menu(update, context)

async def set_admin_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, "Set admin comment triggered", update)
    await update.message.reply_text("Set admin comment functionality is not yet implemented.")
    return await generate_edit_menu(update, context)

async def change_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, "Change price triggered", update)
    await update.callback_query.answer("Change price functionality is not yet implemented.")
    return await generate_edit_menu(update, context)

async def booking_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton('Изменить бронирование', callback_data=CHANGE_BOOKING_ADMIN)],
        [InlineKeyboardButton('Обновить бронь в чатах', callback_data=UPDATE_BOOKING)],]

    # message = (
    #     f"Пользователь: {user.contact}\n"
    #     f"Дата начала: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
    #     f"Дата завершения: {booking.end_date.strftime('%d.%m.%Y %H:%M')}\n"
    #     f"Тариф: {tariff_helper.get_name(booking.tariff)}\n"
    #     f"Стоимость: {booking.price} руб.\n"
    #     f"Предоплата: {booking.prepayment_price} руб.\n") 
    await update.message.reply_text(
        text="lolol", 
        reply_markup=InlineKeyboardMarkup(keyboard))
