import sys
import os
from datetime import datetime, date, time, timedelta
from typing import Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram.error import TelegramError
from dateutil.relativedelta import relativedelta

from src.services.logger_service import LoggerService
from src.services.database_service import DatabaseService
from src.services.calculation_rate_service import CalculationRateService
from src.services.calendar_service import CalendarService
from src.decorators.callback_error_handler import safe_callback_query
from src.helpers import string_helper, tariff_helper, date_time_helper
from src.date_time_picker import calendar_picker, hours_picker
from src.config.config import ADMIN_CHAT_ID, INFORM_CHAT_ID, MIN_BOOKING_HOURS, PERIOD_IN_MONTHS, CLEANING_HOURS
from src.constants import (
    END,
    MANAGE_BOOKING_DETAIL,
    MANAGE_CHANGE_PRICE,
    MANAGE_CHANGE_PREPAYMENT,
    MANAGE_CHANGE_TARIFF,
    MANAGE_RESCHEDULE_DATE,
    MANAGE_RESCHEDULE_TIME,
)
from src.models.enum.tariff import Tariff
from db.models.booking import BookingBase
from db.models.user import UserBase
from src.handlers.admin_handler import (
    get_future_bookings,
    prepare_approve_process,
    check_and_send_booking,
    back_to_booking_list,
    send_feedback,
)

database_service = DatabaseService()
calculation_rate_service = CalculationRateService()
calendar_service = CalendarService()


# Task 5: Show booking detail view
@safe_callback_query()
async def show_booking_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, booking_id: Optional[int] = None) -> int:
    """Show detailed booking information with action buttons

    Args:
        update: Telegram update object
        context: Telegram context object
        booking_id: Optional booking ID. If not provided, will be parsed from callback_query.data
    """
    await update.callback_query.answer()

    if booking_id is None:
        data = string_helper.parse_manage_booking_callback(update.callback_query.data)
        booking_id = data["booking_id"]

    booking = database_service.get_booking_by_id(booking_id)
    if not booking:
        await update.callback_query.edit_message_text("❌ Бронирование не найдено.")
        return END

    user = database_service.get_user_by_id(booking.user_id)

    # Generate detailed message
    message = (
        f"📋 <b>Детали бронирования #{booking.id}</b>\n\n"
        f"{string_helper.generate_booking_info_message(booking, user)}\n"
    )

    if booking.is_canceled:
        message = "⛔ <b>ОТМЕНЕНО</b>\n\n" + message

    # Create action buttons
    keyboard = [
        [InlineKeyboardButton("🔙 Назад к списку", callback_data="MBL")],
    ]

    # Add approve button only if booking is not prepaid and not canceled
    if not booking.is_prepaymented and not booking.is_canceled:
        keyboard.append([InlineKeyboardButton("✅ Подтвердить бронь", callback_data=f"MBA_approve_{booking.id}")])

    # Add cancel button only if booking is not canceled
    if not booking.is_canceled:
        keyboard.append([InlineKeyboardButton("❌ Отменить бронь", callback_data=f"MBA_cancel_{booking.id}")])

    # Add complete button only if booking is not done and not canceled
    if not booking.is_done and not booking.is_canceled:
        keyboard.append([InlineKeyboardButton("✅ Завершить бронь", callback_data=f"MBA_complete_{booking.id}")])

    keyboard.extend([
        [InlineKeyboardButton("📅 Перенести бронь", callback_data=f"MBA_reschedule_{booking.id}")],
        [InlineKeyboardButton("💰 Изменить стоимость", callback_data=f"MBA_price_{booking.id}")],
        [InlineKeyboardButton("💳 Изменить предоплату", callback_data=f"MBA_prepay_{booking.id}")],
        [InlineKeyboardButton("🎯 Изменить тариф", callback_data=f"MBA_tariff_{booking.id}")],
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    LoggerService.info(
        __name__,
        "Admin viewing booking detail",
        update,
        **{"booking_id": booking_id}
    )

    return MANAGE_BOOKING_DETAIL


# Task 7: Cancel booking action
@safe_callback_query()
async def start_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel booking and notify customer"""
    await update.callback_query.answer()

    data = string_helper.parse_manage_booking_callback(update.callback_query.data)
    booking_id = data["booking_id"]

    booking = database_service.get_booking_by_id(booking_id)
    user = database_service.get_user_by_id(booking.user_id)

    # Mark as canceled
    booking = database_service.update_booking(booking_id, is_canceled=True)

    # Update Google Calendar event (change color to gray and add "ОТМЕНА")
    if booking.calendar_event_id:
        calendar_service.cancel_event(booking.calendar_event_id)

    # Notify customer
    await notify_customer_cancellation(context, booking, user)

    # Send notification to INFORM_CHAT_ID
    user_contact = user.contact if user and user.contact else "N/A"
    inform_message = (
        f"Отмена бронирования!\n"
        f"Контакт клиента: {user_contact}\n"
        f"Дата начала: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"Дата завершения: {booking.end_date.strftime('%d.%m.%Y %H:%M')}\n"
    )
    await context.bot.send_message(chat_id=INFORM_CHAT_ID, text=inform_message)

    # Update admin message
    user_contact = user.contact if user else "N/A"
    message = (
        f"✅ <b>Бронирование #{booking.id} отменено</b>\n\n"
        f"Клиент уведомлен: {user_contact}"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"MBD_{booking.id}")],
        [InlineKeyboardButton("📋 К списку бронирований", callback_data="MBL")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    LoggerService.info(
        __name__,
        "Admin canceled booking",
        update,
        **{"booking_id": booking_id, "user_contact": user.contact if user else None}
    )

    return MANAGE_BOOKING_DETAIL


# Task 7.5: Approve booking action
@safe_callback_query()
async def handle_approve_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Approve booking and notify customer"""
    await update.callback_query.answer()

    data = string_helper.parse_manage_booking_callback(update.callback_query.data)
    booking_id = data["booking_id"]

    booking = database_service.get_booking_by_id(booking_id)
    if not booking:
        await update.callback_query.edit_message_text("❌ Бронирование не найдено.")
        return END

    if booking.is_prepaymented:
        await update.callback_query.edit_message_text("ℹ️ Бронирование ��же подтверждено.")
        return await show_booking_detail(update, context, booking_id=booking_id)

    user = database_service.get_user_by_id(booking.user_id)

    # Prepare approve process (sets is_prepaymented=True, creates calendar event)
    (updated_booking, user) = await prepare_approve_process(update, context, booking_id)
    await check_and_send_booking(context, updated_booking)

    # Prepare confirmation message for customer
    confirmation_text = (
        "🎉 <b>Отличные новости!</b> 🎉\n"
        "✅ <b>Ваше бронирование подтверждено администратором.</b>\n"
        "📩 За 1 день до заезда вы получите сообщение с деталями бронирования и инструкцией по заселению.\n"
        f"Общая стоимость бронирования: {updated_booking.price} руб.\n"
        f"Предоплата: {updated_booking.prepayment_price} руб.\n"
    )

    # Add transfer time information if transfer is requested
    if updated_booking.transfer_address:
        # Transfer time is 30 minutes before check-in time
        transfer_time = updated_booking.start_date - timedelta(minutes=30)
        confirmation_text += f"🚗 <b>Трансфер:</b> {updated_booking.transfer_address}\n"
        confirmation_text += (
            f"🕐 <b>Время трансфера:</b> {transfer_time.strftime('%d.%m.%Y %H:%M')}\n"
        )

    # Notify customer
    if user and user.chat_id:
        try:
            await context.bot.send_message(
                chat_id=user.chat_id,
                text=confirmation_text,
                parse_mode="HTML",
            )
        except TelegramError as e:
            LoggerService.error(
                __name__,
                "Failed to notify customer of booking approval",
                exception=e,
                **{"booking_id": booking_id, "chat_id": user.chat_id if user else None}
            )

    # Update admin message
    user_contact = user.contact if user else "N/A"
    message = (
        f"✅ <b>Бронирование #{booking_id} подтверждено</b>\n\n"
        f"Клиент уведомлен: {user_contact}"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"MBD_{booking_id}")],
        [InlineKeyboardButton("📋 К списку бронирований", callback_data="MBL")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    LoggerService.info(
        __name__,
        "Admin approved booking",
        update,
        **{"booking_id": booking_id, "user_contact": user.contact if user else None}
    )

    return MANAGE_BOOKING_DETAIL


# Complete booking action
@safe_callback_query()
async def handle_complete_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Complete booking and send feedback request"""
    await update.callback_query.answer()

    data = string_helper.parse_manage_booking_callback(update.callback_query.data)
    booking_id = data["booking_id"]

    booking = database_service.get_booking_by_id(booking_id)
    if not booking:
        await update.callback_query.edit_message_text("❌ Бронирование не найдено.")
        return END

    if booking.is_done:
        await update.callback_query.edit_message_text("ℹ️ Бронирование уже завершено.")
        return await show_booking_detail(update, context, booking_id=booking_id)

    # Mark booking as done
    booking = database_service.update_booking(booking_id, is_done=True)

    # Send feedback request to customer
    try:
        await send_feedback(context, booking)
        feedback_sent = True
    except Exception as e:
        LoggerService.error(
            __name__,
            "Failed to send feedback request",
            exception=e,
            **{"booking_id": booking_id}
        )
        feedback_sent = False

    # Update admin message
    user = database_service.get_user_by_id(booking.user_id)
    user_contact = user.contact if user else "N/A"

    if feedback_sent:
        message = (
            f"✅ <b>Бронирование #{booking_id} завершено</b>\n\n"
            f"Клиенту отправлен запрос на фидбек: {user_contact}"
        )
    else:
        message = (
            f"✅ <b>Бронирование #{booking_id} завершено</b>\n\n"
            f"❌ Не удалось отправить запрос на фидбек клиенту: {user_contact}"
        )

    keyboard = [
        [InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"MBD_{booking_id}")],
        [InlineKeyboardButton("📋 К списку бронирований", callback_data="MBL")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    LoggerService.info(
        __name__,
        "Admin completed booking",
        update,
        **{"booking_id": booking_id, "feedback_sent": feedback_sent}
    )

    return MANAGE_BOOKING_DETAIL


async def notify_customer_cancellation(
    context: ContextTypes.DEFAULT_TYPE,
    booking: BookingBase,
    user: UserBase
):
    """Send cancellation notification to customer"""
    if not user or not user.chat_id:
        LoggerService.warning(
            __name__,
            "Cannot notify customer - no chat_id or user is None",
            **{"booking_id": booking.id, "user_id": user.id if user else None}
        )
        return

    try:
        message = (
            f"⚠️ <b>Внимание!</b> ⚠️\n\n"
            f"❌ <b>Ваше бронирование отменено администратором.</b>\n\n"
            f"📋 Детали:\n"
            f"Дата: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"Тариф: {tariff_helper.get_name(booking.tariff)}\n\n"
            f"📞 Администратор свяжется с вами для уточнения деталей."
        )

        await context.bot.send_message(
            chat_id=user.chat_id,
            text=message,
            parse_mode="HTML"
        )

        LoggerService.info(
            __name__,
            "Customer notified of cancellation",
            **{"booking_id": booking.id, "chat_id": user.chat_id}
        )
    except TelegramError as e:
        LoggerService.error(
            __name__,
            "Failed to notify customer of cancellation",
            exception=e,
            **{"booking_id": booking.id, "chat_id": user.chat_id}
        )


# Task 8: Change price action
@safe_callback_query()
async def start_change_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask admin to enter new price"""
    await update.callback_query.answer()

    data = string_helper.parse_manage_booking_callback(update.callback_query.data)
    booking_id = data["booking_id"]
    booking = database_service.get_booking_by_id(booking_id)
    user = database_service.get_user_by_id(booking.user_id)

    # Store context
    context.user_data["manage_booking_id"] = booking_id
    context.user_data["manage_user_chat_id"] = user.chat_id if user else None
    context.user_data["manage_old_value"] = booking.price

    keyboard = [[InlineKeyboardButton("Отмена", callback_data=f"MBB_{booking_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"📝 <b>Изменение стоимости бронирования #{booking_id}</b>\n\n"
        f"Текущая стоимость: <b>{booking.price} руб.</b>\n\n"
        f"Введите новую стоимость цифрами (например: 450):"
    )

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    return MANAGE_CHANGE_PRICE


async def handle_price_change_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle price input from admin"""
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return END

    booking_id = context.user_data.get("manage_booking_id")
    if not booking_id:
        return END

    price_text = update.message.text.strip()

    # Validate input
    try:
        new_price = float(price_text)
        if new_price <= 0:
            await update.message.reply_text("❌ Стоимость должна быть положительным числом. Попробуйте еще раз:")
            return MANAGE_CHANGE_PRICE
    except ValueError:
        await update.message.reply_text("❌ Неверный формат. Введите число (например: 450). Попробуйте еще раз:")
        return MANAGE_CHANGE_PRICE

    old_price = context.user_data.get("manage_old_value")

    # Update booking
    booking = database_service.update_booking(booking_id, price=new_price)
    user = database_service.get_user_by_id(booking.user_id)

    # Update calendar event description with new price
    if booking.calendar_event_id:
        calendar_service.update_event_info(booking.calendar_event_id, booking, user)

    # Notify customer
    await notify_customer_price_change(context, booking, user, old_price)

    # Confirm to admin
    user_contact = user.contact if user else "N/A"
    message = (
        f"✅ <b>Стоимость изменена</b>\n\n"
        f"Старая стоимость: {old_price} руб.\n"
        f"Новая стоимость: {new_price} руб.\n\n"
        f"Клиент уведомлен: {user_contact}"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"MBD_{booking_id}")],
        [InlineKeyboardButton("📋 К списку бронирований", callback_data="MBL")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    # Clear context
    context.user_data.pop("manage_booking_id", None)
    context.user_data.pop("manage_user_chat_id", None)
    context.user_data.pop("manage_old_value", None)

    LoggerService.info(
        __name__,
        "Admin changed booking price",
        update,
        **{"booking_id": booking_id, "old_price": old_price, "new_price": new_price}
    )

    return MANAGE_BOOKING_DETAIL


async def notify_customer_price_change(
    context: ContextTypes.DEFAULT_TYPE,
    booking: BookingBase,
    user: UserBase,
    old_price: float
):
    """Notify customer of price change"""
    if not user or not user.chat_id:
        LoggerService.warning(
            __name__,
            "Cannot notify customer - no chat_id or user is None",
            **{"booking_id": booking.id, "user_id": user.id if user else None}
        )
        return

    try:
        message = (
            f"📢 <b>Изменение стоимости бронирования</b>\n\n"
            f"Администратор изменил стоимость вашего бронирования:\n\n"
            f"📋 Детали:\n"
            f"Дата: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"Тариф: {tariff_helper.get_name(booking.tariff)}\n\n"
            f"💰 Старая стоимость: {old_price} руб.\n"
            f"💰 Новая стоимость: {booking.price} руб.\n\n"
            f"По всем вопросам свяжитесь с администратором."
        )

        await context.bot.send_message(
            chat_id=user.chat_id,
            text=message,
            parse_mode="HTML"
        )

        LoggerService.info(
            __name__,
            "Customer notified of price change",
            **{"booking_id": booking.id, "chat_id": user.chat_id}
        )
    except TelegramError as e:
        LoggerService.error(
            __name__,
            "Failed to notify customer of price change",
            exception=e,
            **{"booking_id": booking.id, "chat_id": user.chat_id}
        )


# Task 9: Change prepayment action
@safe_callback_query()
async def start_change_prepayment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask admin to enter new prepayment"""
    await update.callback_query.answer()

    data = string_helper.parse_manage_booking_callback(update.callback_query.data)
    booking_id = data["booking_id"]
    booking = database_service.get_booking_by_id(booking_id)
    user = database_service.get_user_by_id(booking.user_id)

    # Store context
    context.user_data["manage_booking_id"] = booking_id
    context.user_data["manage_user_chat_id"] = user.chat_id if user else None
    context.user_data["manage_old_value"] = booking.prepayment_price

    keyboard = [[InlineKeyboardButton("Отмена", callback_data=f"MBB_{booking_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"📝 <b>Изменение предоплаты бронирования #{booking_id}</b>\n\n"
        f"Текущая предоплата: <b>{booking.prepayment_price} руб.</b>\n\n"
        f"Введите новую предоплату цифрами (например: 100):"
    )

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    return MANAGE_CHANGE_PREPAYMENT


async def handle_prepayment_change_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle prepayment input from admin"""
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return END

    booking_id = context.user_data.get("manage_booking_id")
    if not booking_id:
        return END

    prepayment_text = update.message.text.strip()

    # Validate input
    try:
        new_prepayment = float(prepayment_text)
        if new_prepayment <= 0:
            await update.message.reply_text("❌ Предоплата должна быть положительным числом. Попробуйте еще раз:")
            return MANAGE_CHANGE_PREPAYMENT
    except ValueError:
        await update.message.reply_text("❌ Неверный формат. Введите число (например: 100). Попробуйте еще раз:")
        return MANAGE_CHANGE_PREPAYMENT

    old_prepayment = context.user_data.get("manage_old_value")

    # Update booking
    booking = database_service.update_booking(booking_id, prepayment_price=new_prepayment)
    user = database_service.get_user_by_id(booking.user_id)

    # Update calendar event description with new prepayment
    if booking.calendar_event_id:
        calendar_service.update_event_info(booking.calendar_event_id, booking, user)


    # Notify customer
    await notify_customer_prepayment_change(context, booking, user, old_prepayment)

    # Confirm to admin
    user_contact = user.contact if user else "N/A"
    message = (
        f"✅ <b>Предоплата изменена</b>\n\n"
        f"Старая предоплата: {old_prepayment} руб.\n"
        f"Новая предоплата: {new_prepayment} руб.\n\n"
        f"Клиент уведомлен: {user_contact}"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"MBD_{booking_id}")],
        [InlineKeyboardButton("📋 К списку бронирований", callback_data="MBL")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    # Clear context
    context.user_data.pop("manage_booking_id", None)
    context.user_data.pop("manage_user_chat_id", None)
    context.user_data.pop("manage_old_value", None)

    LoggerService.info(
        __name__,
        "Admin changed booking prepayment",
        update,
        **{"booking_id": booking_id, "old_prepayment": old_prepayment, "new_prepayment": new_prepayment}
    )

    return MANAGE_BOOKING_DETAIL


async def notify_customer_prepayment_change(
    context: ContextTypes.DEFAULT_TYPE,
    booking: BookingBase,
    user: UserBase,
    old_prepayment: float
):
    """Notify customer of prepayment change"""
    if not user or not user.chat_id:
        LoggerService.warning(
            __name__,
            "Cannot notify customer - no chat_id or user is None",
            **{"booking_id": booking.id, "user_id": user.id if user else None}
        )
        return

    try:
        message = (
            f"📢 <b>Изменение предоплаты бронирования</b>\n\n"
            f"Администратор изменил предоплату вашего бронирования:\n\n"
            f"📋 Детали:\n"
            f"Дата: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"Тариф: {tariff_helper.get_name(booking.tariff)}\n\n"
            f"💳 Старая предоплата: {old_prepayment} руб.\n"
            f"💳 Новая предоплата: {booking.prepayment_price} руб.\n\n"
            f"По всем вопросам свяжитесь с администратором."
        )

        await context.bot.send_message(
            chat_id=user.chat_id,
            text=message,
            parse_mode="HTML"
        )

        LoggerService.info(
            __name__,
            "Customer notified of prepayment change",
            **{"booking_id": booking.id, "chat_id": user.chat_id}
        )
    except TelegramError as e:
        LoggerService.error(
            __name__,
            "Failed to notify customer of prepayment change",
            exception=e,
            **{"booking_id": booking.id, "chat_id": user.chat_id}
        )


# Task 10: Change tariff action
@safe_callback_query()
async def start_change_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show tariff selection buttons"""
    await update.callback_query.answer()

    data = string_helper.parse_manage_booking_callback(update.callback_query.data)
    booking_id = data["booking_id"]
    booking = database_service.get_booking_by_id(booking_id)
    user = database_service.get_user_by_id(booking.user_id)

    # Store context
    context.user_data["manage_booking_id"] = booking_id
    context.user_data["manage_user_chat_id"] = user.chat_id if user else None
    context.user_data["manage_old_value"] = booking.tariff

    # Create tariff selection keyboard
    keyboard = []
    for tariff in Tariff:
        tariff_name = tariff_helper.get_name(tariff)
        keyboard.append([
            InlineKeyboardButton(
                f"🎯 {tariff_name}",
                callback_data=f"MBT_{tariff.value}_{booking_id}"
            )
        ])

    keyboard.append([InlineKeyboardButton("Отмена", callback_data=f"MBB_{booking_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    current_tariff = tariff_helper.get_name(booking.tariff)
    message = (
        f"📝 <b>Изменение тарифа бронирования #{booking_id}</b>\n\n"
        f"Текущий тариф: <b>{current_tariff}</b>\n\n"
        f"Выберите новый тариф:"
    )

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    return MANAGE_CHANGE_TARIFF


@safe_callback_query()
async def handle_tariff_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle tariff selection"""
    await update.callback_query.answer()

    data = string_helper.parse_manage_booking_callback(update.callback_query.data)
    new_tariff_value = data["tariff"]
    booking_id = data["booking_id"]

    new_tariff = Tariff(new_tariff_value)
    old_tariff = context.user_data.get("manage_old_value")

    booking = database_service.get_booking_by_id(booking_id)
    user = database_service.get_user_by_id(booking.user_id)

    # Update booking
    booking = database_service.update_booking(
        booking_id,
        tariff=new_tariff
    )

    # Update calendar event with new tariff (updates both summary and description)
    if booking.calendar_event_id:
        calendar_service.update_event_info(booking.calendar_event_id, booking, user)

    # Notify customer
    await notify_customer_tariff_change(context, booking, user, old_tariff)

    # Confirm to admin
    old_tariff_name = tariff_helper.get_name(old_tariff)
    new_tariff_name = tariff_helper.get_name(new_tariff)
    user_contact = user.contact if user else "N/A"

    message = (
        f"✅ <b>Тариф изменен</b>\n\n"
        f"🎯 Старый тариф: {old_tariff_name}\n"
        f"🎯 Новый тариф: {new_tariff_name}\n\n"
        f"Клиент уведомлен: {user_contact}"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"MBD_{booking_id}")],
        [InlineKeyboardButton("📋 К списку бронирований", callback_data="MBL")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    # Clear context
    context.user_data.pop("manage_booking_id", None)
    context.user_data.pop("manage_user_chat_id", None)
    context.user_data.pop("manage_old_value", None)

    LoggerService.info(
        __name__,
        "Admin changed booking tariff",
        update,
        **{
            "booking_id": booking_id,
            "old_tariff": old_tariff.name,
            "new_tariff": new_tariff.name
        }
    )

    return MANAGE_BOOKING_DETAIL


async def notify_customer_tariff_change(
    context: ContextTypes.DEFAULT_TYPE,
    booking: BookingBase,
    user: UserBase,
    old_tariff: Tariff
):
    """Notify customer of tariff change"""
    if not user or not user.chat_id:
        LoggerService.warning(
            __name__,
            "Cannot notify customer - no chat_id or user is None",
            **{"booking_id": booking.id, "user_id": user.id if user else None}
        )
        return

    try:
        old_tariff_name = tariff_helper.get_name(old_tariff)
        new_tariff_name = tariff_helper.get_name(booking.tariff)

        message = (
            f"📢 <b>Изменение тарифа бронирования</b>\n\n"
            f"Администратор изменил тариф вашего бронирования:\n\n"
            f"📋 Детали:\n"
            f"Дата: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"🎯 Старый тариф: {old_tariff_name}\n"
            f"🎯 Новый тариф: {new_tariff_name}\n\n"
            f"По всем вопросам свяжитесь с администратором."
        )

        await context.bot.send_message(
            chat_id=user.chat_id,
            text=message,
            parse_mode="HTML"
        )

        LoggerService.info(
            __name__,
            "Customer notified of tariff change",
            **{"booking_id": booking.id, "chat_id": user.chat_id}
        )
    except TelegramError as e:
        LoggerService.error(
            __name__,
            "Failed to notify customer of tariff change",
            exception=e,
            **{"booking_id": booking.id, "chat_id": user.chat_id}
        )


# Task 11: Reschedule booking
@safe_callback_query()
async def start_reschedule_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start reschedule booking process - show calendar for start date"""
    await update.callback_query.answer()

    data = string_helper.parse_manage_booking_callback(update.callback_query.data)
    booking_id = data["booking_id"]

    booking = database_service.get_booking_by_id(booking_id)
    if not booking:
        await update.callback_query.edit_message_text("❌ Бронирование не найдено.")
        return END

    # Store booking data in context
    context.user_data["reschedule_booking_id"] = booking_id
    context.user_data["reschedule_old_start_date"] = booking.start_date
    context.user_data["reschedule_old_end_date"] = booking.end_date

    # Show calendar for start date selection
    today = date.today()
    max_date_booking = today + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = today
    start_period, end_period = date_time_helper.month_bounds(today)
    feature_booking = database_service.get_booking_by_start_date_period(start_period, end_period)
    # Exclude current booking from occupied slots
    feature_booking = [b for b in feature_booking if b.id != booking_id]
    available_days = date_time_helper.get_free_dayes_slots(
        feature_booking, target_month=today.month, target_year=today.year
    )

    message = (
        f"📅 <b>Перенос бронирования #{booking_id}</b>\n\n"
        f"Текущая дата: {booking.start_date.strftime('%d.%m.%Y %H:%M')} - {booking.end_date.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Выберите новую дату начала бронирования:"
    )

    keyboard = [[InlineKeyboardButton("Отмена", callback_data=f"MBB_{booking_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=calendar_picker.create_calendar(
            today,
            min_date=min_date_booking,
            max_date=max_date_booking,
            action_text="Отмена",
            callback_prefix="-START",
            available_days=available_days,
        ),
        parse_mode="HTML"
    )

    return MANAGE_RESCHEDULE_DATE


@safe_callback_query()
async def handle_reschedule_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle start date selection for reschedule"""
    await update.callback_query.answer()

    booking_id = context.user_data.get("reschedule_booking_id")
    if not booking_id:
        await update.callback_query.edit_message_text("❌ Ошибка: данные бронирования не найдены.")
        return END

    booking = database_service.get_booking_by_id(booking_id)
    if not booking:
        await update.callback_query.edit_message_text("❌ Бронирование не найдено.")
        return END

    max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = date.today()
    (
        selected,
        selected_date,
        is_action,
        is_next_month,
        is_prev_month,
    ) = await calendar_picker.process_calendar_selection(update, context)

    if selected:
        selected_date_obj = selected_date.date() if isinstance(selected_date, datetime) else selected_date

        # Validate tariff availability
        if not tariff_helper.is_booking_available(booking.tariff, selected_date_obj):
            error_message = (
                "❌ <b>Ошибка!</b>\n\n"
                "⏳ <b>Тариф 'Рабочий' доступен только с понедельника по четверг.</b>\n"
                "🔄 Пожалуйста, выберите новую дату начала бронирования."
            )
            return await show_reschedule_start_date_calendar(update, context, booking_id, error_message)

        context.user_data["reschedule_start_date"] = selected_date_obj
        LoggerService.info(
            __name__,
            "Admin selected reschedule start date",
            update,
            **{"booking_id": booking_id, "start_date": selected_date_obj}
        )
        return await show_reschedule_start_time(update, context, booking_id)
    elif is_action:
        # Cancel - return to booking detail
        # Clear reschedule context data
        context.user_data.pop("reschedule_booking_id", None)
        context.user_data.pop("reschedule_old_start_date", None)
        context.user_data.pop("reschedule_old_end_date", None)
        context.user_data.pop("reschedule_start_date", None)

        # Show booking detail by passing booking_id directly
        return await show_booking_detail(update, context, booking_id=booking_id)
    elif is_next_month or is_prev_month:
        # Update calendar for new month
        return await show_reschedule_start_date_calendar(update, context, booking_id, selected_date=selected_date)

    return MANAGE_RESCHEDULE_DATE


async def show_reschedule_start_date_calendar(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    booking_id: int,
    error_message: Optional[str] = None,
    selected_date: Optional[datetime] = None
) -> int:
    """Show calendar for start date selection"""
    booking = database_service.get_booking_by_id(booking_id)
    if not booking:
        await update.callback_query.edit_message_text("❌ Бронирование не найдено.")
        return END

    if selected_date is None:
        selected_date = date.today()
    else:
        selected_date = selected_date.date() if isinstance(selected_date, datetime) else selected_date

    max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = date.today()
    start_period, end_period = date_time_helper.month_bounds(selected_date)
    feature_booking = database_service.get_booking_by_start_date_period(start_period, end_period)
    # Exclude current booking from occupied slots
    feature_booking = [b for b in feature_booking if b.id != booking_id]
    available_days = date_time_helper.get_free_dayes_slots(
        feature_booking, target_month=selected_date.month, target_year=selected_date.year
    )

    message = (
        f"📅 <b>Перенос бронирования #{booking_id}</b>\n\n"
        f"Текущая дата: {booking.start_date.strftime('%d.%m.%Y %H:%M')} - {booking.end_date.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Выберите новую дату начала бронирования:"
    )
    if error_message:
        message = error_message

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=calendar_picker.create_calendar(
            selected_date,
            min_date=min_date_booking,
            max_date=max_date_booking,
            action_text="Отмена",
            callback_prefix="-START",
            available_days=available_days,
        ),
        parse_mode="HTML"
    )

    return MANAGE_RESCHEDULE_DATE


async def show_reschedule_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE, booking_id: int) -> int:
    """Show time picker for start time"""
    booking = database_service.get_booking_by_id(booking_id)
    start_date = context.user_data.get("reschedule_start_date")

    feature_booking = database_service.get_booking_by_start_date_period(
        start_date - timedelta(days=2),
        start_date + timedelta(days=2),
    )
    # Exclude current booking from occupied slots
    feature_booking = [b for b in feature_booking if b.id != booking_id]
    available_slots = date_time_helper.get_free_time_slots(feature_booking, start_date)

    message = (
        "⏳ <b>Выберите время начала бронирования.</b>\n"
        f"Вы выбрали дату заезда: {start_date.strftime('%d.%m.%Y')}.\n"
        "Теперь укажите удобное время заезда.\n"
        "⛔ - время уже забронировано\n"
    )
    if booking.tariff == Tariff.WORKER or booking.tariff == Tariff.INCOGNITA_WORKER:
        message += (
            "\n📌 <b>Для тарифа 'Рабочий' доступны интервалы:</b>\n"
            "🕚 11:00 – 20:00\n"
            "🌙 22:00 – 09:00"
        )

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=hours_picker.create_hours_picker(
            action_text="Назад",
            free_slots=available_slots,
            date=start_date,
            callback_prefix="-START",
        ),
        parse_mode="HTML"
    )

    return MANAGE_RESCHEDULE_TIME


@safe_callback_query()
async def handle_reschedule_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle start time selection for reschedule"""
    await update.callback_query.answer()

    booking_id = context.user_data.get("reschedule_booking_id")
    if not booking_id:
        await update.callback_query.edit_message_text("❌ Ошибка: данные бронирования не найдены.")
        return END

    selected, time_obj, is_action = await hours_picker.process_hours_selection(update, context)

    if selected:
        start_date = context.user_data.get("reschedule_start_date")
        start_datetime = datetime.combine(start_date, time_obj)
        context.user_data["reschedule_start_datetime"] = start_datetime

        LoggerService.info(
            __name__,
            "Admin selected reschedule start time",
            update,
            **{"booking_id": booking_id, "start_datetime": start_datetime}
        )
        return await show_reschedule_finish_date(update, context, booking_id)
    elif is_action:
        # Back to start date selection
        return await show_reschedule_start_date_calendar(update, context, booking_id)

    return MANAGE_RESCHEDULE_TIME


async def show_reschedule_finish_date(update: Update, context: ContextTypes.DEFAULT_TYPE, booking_id: int) -> int:
    """Show calendar for finish date selection"""
    booking = database_service.get_booking_by_id(booking_id)
    start_datetime = context.user_data.get("reschedule_start_datetime")

    today = date.today()
    max_date_booking = today + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = (start_datetime + timedelta(hours=MIN_BOOKING_HOURS)).date()

    start_period, end_period = date_time_helper.month_bounds(start_datetime.date())
    feature_booking = database_service.get_booking_by_start_date_period(start_period, end_period)
    # Exclude current booking from occupied slots
    feature_booking = [b for b in feature_booking if b.id != booking_id]
    available_days = date_time_helper.get_free_dayes_slots(
        feature_booking, target_month=start_period.month, target_year=start_period.year
    )

    message = (
        "📅 <b>Выберите дату завершения бронирования.</b>\n"
        f"Вы выбрали дату и время заезда: {start_datetime.strftime('%d.%m.%Y %H:%M')}.\n"
        "Теперь укажите день, когда планируете выехать.\n"
        "📌 Выезд должен быть позже времени заезда."
    )

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=calendar_picker.create_calendar(
            start_datetime.date(),
            min_date=min_date_booking,
            max_date=max_date_booking,
            action_text="Назад",
            callback_prefix="-FINISH",
            available_days=available_days,
        ),
        parse_mode="HTML"
    )

    return MANAGE_RESCHEDULE_DATE


@safe_callback_query()
async def handle_reschedule_finish_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle finish date selection for reschedule"""
    await update.callback_query.answer()

    booking_id = context.user_data.get("reschedule_booking_id")
    if not booking_id:
        await update.callback_query.edit_message_text("❌ Ошибка: данные бронирования не найдены.")
        return END

    booking = database_service.get_booking_by_id(booking_id)
    start_datetime = context.user_data.get("reschedule_start_datetime")

    max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = (start_datetime + timedelta(hours=MIN_BOOKING_HOURS)).date()
    (
        selected,
        selected_date,
        is_action,
        is_next_month,
        is_prev_month,
    ) = await calendar_picker.process_calendar_selection(update, context)

    if selected:
        selected_date_obj = selected_date.date() if isinstance(selected_date, datetime) else selected_date
        context.user_data["reschedule_finish_date"] = selected_date_obj

        LoggerService.info(
            __name__,
            "Admin selected reschedule finish date",
            update,
            **{"booking_id": booking_id, "finish_date": selected_date_obj}
        )
        return await show_reschedule_finish_time(update, context, booking_id)
    elif is_action:
        # Back to start time selection
        return await show_reschedule_start_time(update, context, booking_id)
    elif is_next_month or is_prev_month:
        # Update calendar for new month
        return await show_reschedule_finish_date(update, context, booking_id)

    return MANAGE_RESCHEDULE_DATE


async def show_reschedule_finish_time(update: Update, context: ContextTypes.DEFAULT_TYPE, booking_id: int) -> int:
    """Show time picker for finish time"""
    booking = database_service.get_booking_by_id(booking_id)
    start_datetime = context.user_data.get("reschedule_start_datetime")
    finish_date = context.user_data.get("reschedule_finish_date")

    feature_booking = database_service.get_booking_by_start_date_period(
        finish_date - timedelta(days=2),
        finish_date + timedelta(days=2),
    )
    # Exclude current booking from occupied slots
    feature_booking = [b for b in feature_booking if b.id != booking_id]
    start_time = (
        time(0, 0)
        if start_datetime.date() != finish_date
        else (start_datetime + timedelta(hours=MIN_BOOKING_HOURS)).time()
    )
    available_slots = date_time_helper.get_free_time_slots(feature_booking, finish_date, start_time=start_time)

    message = (
        "⏳ <b>Выберите время завершения бронирования.</b>\n"
        f"Вы выбрали заезд: {start_datetime.strftime('%d.%m.%Y %H:%M')}.\n"
        f"Вы выбрали дату выезда: {finish_date.strftime('%d.%m.%Y')}.\n"
        "Теперь укажите время, когда хотите освободить дом.\n"
        "⛔ - время уже забронировано\n"
    )

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=hours_picker.create_hours_picker(
            action_text="Назад",
            free_slots=available_slots,
            date=finish_date,
            callback_prefix="-FINISH",
        ),
        parse_mode="HTML"
    )

    return MANAGE_RESCHEDULE_TIME


@safe_callback_query()
async def handle_reschedule_finish_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle finish time selection and validate reschedule"""
    await update.callback_query.answer()

    booking_id = context.user_data.get("reschedule_booking_id")
    if not booking_id:
        await update.callback_query.edit_message_text("❌ Ошибка: данные бронирования не найдены.")
        return END

    booking = database_service.get_booking_by_id(booking_id)
    start_datetime = context.user_data.get("reschedule_start_datetime")
    finish_date = context.user_data.get("reschedule_finish_date")

    selected, time_obj, is_action = await hours_picker.process_hours_selection(update, context)

    if selected:
        finish_datetime = datetime.combine(finish_date, time_obj)

        # Validate WORKER tariff time restrictions
        if (booking.tariff == Tariff.WORKER or booking.tariff == Tariff.INCOGNITA_WORKER) and \
           not tariff_helper.is_interval_in_allowed_ranges(start_datetime.time(), finish_datetime.time()):
            error_message = (
                "❌ <b>Ошибка!</b>\n\n"
                "⏳ <b>Выбранные дата и время не соответствуют условиям тарифа 'Рабочий'.</b>\n"
                "⚠️ В рамках этого тарифа бронирование возможно только с 11:00 до 20:00 или с 22:00 до 9:00.\n\n"
                "🔄 Пожалуйста, выберите другое время начала бронирования."
            )
            return await show_reschedule_start_date_calendar(update, context, booking_id, error_message)

        # Check for overlapping bookings
        created_bookings = database_service.get_booking_by_start_date_period(start_datetime, finish_datetime)
        is_any_booking = any(b.id != booking.id for b in created_bookings)
        if is_any_booking:
            error_message = (
                "❌ <b>Ошибка!</b>\n\n"
                "⏳ <b>Выбранные дата и время недоступны.</b>\n"
                "⚠️ Дата начала и конца бронирования пересекается с другим бронированием.\n\n"
                f"🧹 После каждого клиента нам нужно подготовить дом. Уборка занимает <b>{CLEANING_HOURS} часа</b>.\n\n"
                "🔄 Пожалуйста, выберите новую дату начала бронирования."
            )
            return await show_reschedule_start_date_calendar(update, context, booking_id, error_message)

        context.user_data["reschedule_finish_datetime"] = finish_datetime
        LoggerService.info(
            __name__,
            "Admin selected reschedule finish time",
            update,
            **{"booking_id": booking_id, "finish_datetime": finish_datetime}
        )
        return await show_reschedule_confirm(update, context, booking_id)
    elif is_action:
        # Back to finish date selection
        return await show_reschedule_finish_date(update, context, booking_id)

    return MANAGE_RESCHEDULE_TIME


async def show_reschedule_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, booking_id: int) -> int:
    """Show confirmation message for reschedule"""
    booking = database_service.get_booking_by_id(booking_id)
    start_datetime = context.user_data.get("reschedule_start_datetime")
    finish_datetime = context.user_data.get("reschedule_finish_datetime")
    old_start_date = context.user_data.get("reschedule_old_start_date")

    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data=f"MBR-CONFIRM_{booking_id}")],
        [InlineKeyboardButton("❌ Отмена", callback_data=f"MBB_{booking_id}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"📅 <b>Подтвердите перенос бронирования:</b>\n\n"
        f"🔹 <b>С</b> {old_start_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"🔹 <b>На</b> {start_datetime.strftime('%d.%m.%Y %H:%M')} "
        f"до {finish_datetime.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"✅ Подтвердить изменения?"
    )

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    return MANAGE_RESCHEDULE_TIME


@safe_callback_query()
async def handle_reschedule_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle reschedule confirmation and update booking"""
    await update.callback_query.answer()

    # Parse MBR-CONFIRM_{booking_id} format
    callback_data = update.callback_query.data
    if callback_data.startswith("MBR-CONFIRM_"):
        booking_id = int(callback_data.split("_")[1])
    else:
        booking_id = context.user_data.get("reschedule_booking_id")

    if not booking_id:
        await update.callback_query.edit_message_text("❌ Ошибка: данные бронирования не найдены.")
        return END

    booking = database_service.get_booking_by_id(booking_id)
    if not booking:
        await update.callback_query.edit_message_text("❌ Бронирование не найдено.")
        return END

    start_datetime = context.user_data.get("reschedule_start_datetime")
    finish_datetime = context.user_data.get("reschedule_finish_datetime")
    old_start_date = context.user_data.get("reschedule_old_start_date")

    if not start_datetime or not finish_datetime:
        await update.callback_query.edit_message_text("❌ Ошибка: данные о новых датах не найдены.")
        return END

    # Update booking (price remains unchanged)
    updated_booking = database_service.update_booking(
        booking_id,
        start_date=start_datetime,
        end_date=finish_datetime
    )

    # Get user for calendar update and notifications
    user = database_service.get_user_by_id(booking.user_id)

    # Update calendar event with new time and description
    if updated_booking.calendar_event_id:
        calendar_service.move_event(
            updated_booking.calendar_event_id,
            start_datetime,
            finish_datetime,
            booking=updated_booking,
            user=user)

    # Notify customer
    await notify_customer_reschedule(context, updated_booking, user, old_start_date)

    # Inform admin chat
    from src.handlers.admin_handler import inform_changing_booking_date
    await inform_changing_booking_date(
        update, context, updated_booking, old_start_date.date()
    )

    # Clear context
    context.user_data.pop("reschedule_booking_id", None)
    context.user_data.pop("reschedule_old_start_date", None)
    context.user_data.pop("reschedule_old_end_date", None)
    context.user_data.pop("reschedule_start_date", None)
    context.user_data.pop("reschedule_start_datetime", None)
    context.user_data.pop("reschedule_finish_date", None)
    context.user_data.pop("reschedule_finish_datetime", None)

    # Show confirmation
    message = (
        f"✅ <b>Бронирование успешно перенесено!</b>\n\n"
        f"📅 <b>С:</b> {start_datetime.strftime('%d.%m.%Y %H:%M')}\n"
        f"📅 <b>До:</b> {finish_datetime.strftime('%d.%m.%Y %H:%M')}"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"MBD_{booking_id}")],
        [InlineKeyboardButton("📋 К списку бронирований", callback_data="MBL")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    LoggerService.info(
        __name__,
        "Admin rescheduled booking",
        update,
        **{
            "booking_id": booking_id,
            "old_start": old_start_date,
            "new_start": start_datetime,
            "new_end": finish_datetime,
            "price": booking.price
        }
    )

    return MANAGE_BOOKING_DETAIL


async def notify_customer_reschedule(
    context: ContextTypes.DEFAULT_TYPE,
    booking: BookingBase,
    user: UserBase,
    old_start_date: datetime
):
    """Notify customer of booking reschedule"""
    if not user or not user.chat_id:
        LoggerService.warning(
            __name__,
            "Cannot notify customer - no chat_id or user is None",
            **{"booking_id": booking.id, "user_id": user.id if user else None}
        )
        return

    try:
        message = (
            f"📢 <b>Перенос бронирования</b>\n\n"
            f"Администратор перенес дату вашего бронирования:\n\n"
            f"📋 Детали:\n"
            f"🎯 Тариф: {tariff_helper.get_name(booking.tariff)}\n\n"
            f"📅 <b>Старая дата:</b> {old_start_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"📅 <b>Новая дата:</b> {booking.start_date.strftime('%d.%m.%Y %H:%M')} - {booking.end_date.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"По всем вопросам свяжитесь с администратором."
        )

        await context.bot.send_message(
            chat_id=user.chat_id,
            text=message,
            parse_mode="HTML"
        )

        LoggerService.info(
            __name__,
            "Customer notified of reschedule",
            **{"booking_id": booking.id, "chat_id": user.chat_id}
        )
    except TelegramError as e:
        LoggerService.error(
            __name__,
            "Failed to notify customer of reschedule",
            exception=e,
            **{"booking_id": booking.id, "chat_id": user.chat_id}
        )


# Task 12: Create conversation handler
def get_handler() -> ConversationHandler:
    """Returns ConversationHandler for booking details management"""
    handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_booking_detail, pattern="^MBD_\\d+$"),
        ],
        states={
            MANAGE_BOOKING_DETAIL: [
                # Action handlers
                CallbackQueryHandler(handle_approve_booking, pattern="^MBA_approve_\\d+$"),
                CallbackQueryHandler(start_cancel_booking, pattern="^MBA_cancel_\\d+$"),
                CallbackQueryHandler(handle_complete_booking, pattern="^MBA_complete_\\d+$"),
                CallbackQueryHandler(start_reschedule_booking, pattern="^MBA_reschedule_\\d+$"),
                CallbackQueryHandler(start_change_price, pattern="^MBA_price_\\d+$"),
                CallbackQueryHandler(start_change_prepayment, pattern="^MBA_prepay_\\d+$"),
                CallbackQueryHandler(start_change_tariff, pattern="^MBA_tariff_\\d+$"),
                # Back to detail / view detail
                CallbackQueryHandler(show_booking_detail, pattern="^MBD_\\d+$"),
                # Back to list
                CallbackQueryHandler(back_to_booking_list, pattern="^MBL$"),
            ],
            MANAGE_CHANGE_PRICE: [
                MessageHandler(
                    filters.Chat(chat_id=ADMIN_CHAT_ID) & filters.TEXT & ~filters.COMMAND,
                    handle_price_change_input,
                ),
                CallbackQueryHandler(show_booking_detail, pattern="^MBB_\\d+$"),
            ],
            MANAGE_CHANGE_PREPAYMENT: [
                MessageHandler(
                    filters.Chat(chat_id=ADMIN_CHAT_ID) & filters.TEXT & ~filters.COMMAND,
                    handle_prepayment_change_input,
                ),
                CallbackQueryHandler(show_booking_detail, pattern="^MBB_\\d+$"),
            ],
            MANAGE_CHANGE_TARIFF: [
                CallbackQueryHandler(handle_tariff_selection, pattern="^MBT_\\d+_\\d+$"),
                CallbackQueryHandler(show_booking_detail, pattern="^MBB_\\d+$"),
            ],
            MANAGE_RESCHEDULE_DATE: [
                CallbackQueryHandler(handle_reschedule_start_date, pattern="^CALENDAR-CALLBACK-START_.+$"),
                CallbackQueryHandler(handle_reschedule_finish_date, pattern="^CALENDAR-CALLBACK-FINISH_.+$"),
                CallbackQueryHandler(show_booking_detail, pattern="^MBB_\\d+$"),
            ],
            MANAGE_RESCHEDULE_TIME: [
                CallbackQueryHandler(handle_reschedule_start_time, pattern="^HOURS-CALLBACK-START_.+$"),
                CallbackQueryHandler(handle_reschedule_finish_time, pattern="^HOURS-CALLBACK-FINISH_.+$"),
                CallbackQueryHandler(handle_reschedule_confirm, pattern="^MBR-CONFIRM_\\d+$"),
                CallbackQueryHandler(show_booking_detail, pattern="^MBB_\\d+$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(back_to_booking_list, pattern="^MBL$"),
        ],
    )
    return handler
