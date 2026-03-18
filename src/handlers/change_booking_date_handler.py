import sys
import os

from src.services.navigation_service import NavigationService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.logger_service import LoggerService
from src.decorators.callback_error_handler import safe_callback_query
from src.models.enum.tariff import Tariff
from src.services.calendar_service import CalendarService
from src.models.rental_price import RentalPrice
from src.services.calculation_rate_service import CalculationRateService
from src.services.date_pricing_service import DatePricingService
from src.services.redis import RedisSessionService
from db.models.booking import BookingBase
from src.services.database_service import DatabaseService
from datetime import datetime, date, time, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from src.handlers import admin_handler, menu_handler
from src.helpers import date_time_helper, string_helper, tariff_helper
from src.date_time_picker import calendar_picker, hours_picker
from src.config.config import MIN_BOOKING_HOURS, PERIOD_IN_MONTHS, CLEANING_HOURS
from dateutil.relativedelta import relativedelta
from typing import Optional
from src.constants import (
    CHANGE_BOOKING_DATE_VALIDATE_USER,
    END,
    MENU,
    CHANGE_BOOKING_DATE,
    CONFIRM,
)

database_service = DatabaseService()
calculation_rate_service = CalculationRateService()
calendar_service = CalendarService()
navigation_service = NavigationService()
date_pricing_service = DatePricingService()
redis_service = RedisSessionService()


def get_handler():
    return [
        CallbackQueryHandler(choose_booking, pattern=rf"^CHANGE-BOOKING_(\d+|{END})$"),
        CallbackQueryHandler(
            enter_start_date, pattern=f"^CALENDAR-CALLBACK-START_(.+|{END})$"
        ),
        CallbackQueryHandler(
            enter_start_time, pattern=f"^HOURS-CALLBACK-START_(.+|{END})$"
        ),
        CallbackQueryHandler(
            enter_finish_date, pattern=f"^CALENDAR-CALLBACK-FINISH_(.+|{END})$"
        ),
        CallbackQueryHandler(
            enter_finish_time, pattern=f"^HOURS-CALLBACK-FINISH_(.+|{END})$"
        ),
        CallbackQueryHandler(
            confirm_booking, pattern=f"^CHANGE-CONFIRM_({CONFIRM}|{END})$"
        ),
        CallbackQueryHandler(back_navigation, pattern=f"^{END}$"),
    ]


async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler.show_menu(update, context)
    LoggerService.info(__name__, "Back to menu", update)
    redis_service.clear_change_booking(update)
    return MENU


@safe_callback_query()
async def enter_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.init_change_booking(update)
    LoggerService.info(__name__, "Enter user contact", update)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="📲 Укажите ваш <b>Telegram</b> или номер телефона:\n\n"
        "🔹 <b>Telegram:</b> @username (начинайте с @)\n"
        "🔹 <b>Телефон:</b> +375XXXXXXXXX (обязательно с +375)\n"
        "❗️ Пожалуйста, вводите данные строго в указанном формате.",
        reply_markup=reply_markup,
    )
    return CHANGE_BOOKING_DATE_VALIDATE_USER


async def check_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user_input = update.message.text
        is_valid, cleaned_contact = string_helper.is_valid_user_contact(user_input)
        if is_valid:
            redis_service.update_change_booking_field(update, "user_contact", cleaned_contact)

            # Save contact to database
            try:
                chat_id = navigation_service.get_chat_id(update)
                user = database_service.get_user_by_chat_id(chat_id)

                if user:
                    database_service.update_user_contact(chat_id, cleaned_contact)
                    LoggerService.info(
                        __name__,
                        "User contact saved to database",
                        update,
                        **{"chat_id": chat_id, "contact": cleaned_contact},
                    )
                else:
                    user_name = update.effective_user.username or cleaned_contact
                    database_service.update_user_chat_id(user_name, chat_id)
                    database_service.update_user_contact(chat_id, cleaned_contact)
                    LoggerService.warning(
                        __name__,
                        "User not found by chat_id, created new user",
                        update,
                        **{"chat_id": chat_id, "contact": cleaned_contact},
                    )
            except Exception as e:
                LoggerService.error(
                    __name__,
                    "Failed to save user contact to database",
                    exception=e,
                    **{"contact": cleaned_contact},
                )

            return await choose_booking_message(update, context)
        else:
            LoggerService.warning(__name__, "User name is invalid", update)
            await update.message.reply_text(
                "❌ <b>Ошибка!</b>\n"
                "Имя пользователя в Telegram или номер телефона введены некорректно.\n\n"
                "🔄 Пожалуйста, попробуйте еще раз.",
                parse_mode="HTML"
            )

    return CHANGE_BOOKING_DATE_VALIDATE_USER


@safe_callback_query()
async def choose_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    draft = redis_service.get_change_booking(update)
    # Find booking from database by selected_bookings
    selected_bookings_list = database_service.get_booking_by_user_contact(draft.user_contact)
    booking = next((b for b in selected_bookings_list if str(b.id) == data), None)

    if not booking:
        LoggerService.error(__name__, "Booking not found", update)
        return await back_navigation(update, context)

    if booking.is_date_changed:
        error_message = (
            "❌ <b>Ошибка!</b>\n\n"
            "⏳ <b>Вы превысили лимит переносов бронирования.</b>\n"
            "🔄 Пожалуйста, обратитесь к администратору для решения этой проблемы."
        )
        LoggerService.warning(__name__, "reschedule count is more than 1", update)
        return await choose_booking_message(
            update, context, error_message=error_message
        )

    # Store booking data in Redis
    redis_service.update_change_booking_field(update, "selected_booking_id", booking.id)
    redis_service.update_change_booking_field(update, "old_booking_date", booking.start_date)
    redis_service.update_change_booking_field(update, "booking_price", booking.price)
    redis_service.update_change_booking_field(update, "booking_tariff", booking.tariff.name)
    redis_service.update_change_booking_field(update, "booking_has_sauna", booking.has_sauna)
    redis_service.update_change_booking_field(update, "booking_has_photoshoot", booking.has_photoshoot)
    redis_service.update_change_booking_field(update, "booking_has_secret_room", booking.has_secret_room)
    redis_service.update_change_booking_field(update, "booking_has_white_bedroom", booking.has_white_bedroom)
    redis_service.update_change_booking_field(update, "booking_has_green_bedroom", booking.has_green_bedroom)

    LoggerService.info(__name__, "Choose booking", update, **{"booking_id": booking.id})
    return await start_date_message(update, context)


@safe_callback_query()
async def enter_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
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
        draft = redis_service.get_change_booking(update)
        booking = database_service.get_booking_by_id(draft.selected_booking_id)

        if not tariff_helper.is_booking_available(booking.tariff, selected_date):
            LoggerService.warning(
                __name__, f"start date is incorrect for {booking.tariff}", update
            )
            error_message = (
                "❌ <b>Ошибка!</b>\n\n"
                "⏳ <b>Тариф 'Рабочий' доступен только с понедельника по четверг.</b>\n"
                "🔄 Пожалуйста, выберите новую дату начала бронирования."
            )
            LoggerService.warning(
                __name__, "there are bookings between the selected dates", update
            )
            return await start_date_message(
                update, context, error_message=error_message
            )

        redis_service.update_change_booking_field(update, "start_booking_date", selected_date)
        LoggerService.info(
            __name__,
            "select start date",
            update,
            **{"start_date": selected_date.date()},
        )
        return await start_time_message(update, context)
    elif is_action:
        LoggerService.info(
            __name__, "select start date", update, **{"start_date": "cancel"}
        )
        return await back_navigation(update, context)
    elif is_next_month or is_prev_month:
        query = update.callback_query
        start_period, end_period = date_time_helper.month_bounds(selected_date)
        feature_booking = database_service.get_booking_by_start_date_period(
            start_period, end_period
        )

        # Exclude current user's booking from occupied slots
        draft = redis_service.get_change_booking(update)
        if draft and draft.selected_booking_id:
            feature_booking = [b for b in feature_booking if b.id != draft.selected_booking_id]

        available_days = date_time_helper.get_free_dayes_slots(
            feature_booking,
            target_month=start_period.month,
            target_year=start_period.year,
        )

        # Update special dates info for the new month
        special_dates_info = get_special_dates_info(
            selected_date.month, selected_date.year
        )
        message = (
            "✅ <b>Ваше бронирование найдено!</b>\n\n"
            "📅 <b>Введите новую дату, на которую хотите перенести бронирование.</b>"
        )
        if special_dates_info:
            message += f"\n\n{special_dates_info}"

        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
            reply_markup=calendar_picker.create_calendar(
                selected_date,
                min_date=min_date_booking,
                max_date=max_date_booking,
                action_text="Назад в меню",
                callback_prefix="-START",
                available_days=available_days,
            ),
        )
    return CHANGE_BOOKING_DATE


@safe_callback_query()
async def enter_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    selected, time, is_action = await hours_picker.process_hours_selection(
        update, context
    )
    if selected:
        draft = redis_service.get_change_booking(update)
        start_booking_date = draft.start_booking_date.replace(
            hour=time.hour, minute=time.minute
        )
        redis_service.update_change_booking_field(update, "start_booking_date", start_booking_date)
        LoggerService.info(
            __name__,
            "select start time",
            update,
            **{"start_time": start_booking_date.time()},
        )
        return await finish_date_message(update, context)
    elif is_action:
        LoggerService.info(
            __name__, "select start time", update, **{"start_time": "back"}
        )
        return await start_date_message(update, context)
    return CHANGE_BOOKING_DATE


@safe_callback_query()
async def enter_finish_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    draft = redis_service.get_change_booking(update)
    max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = (draft.start_booking_date + timedelta(hours=MIN_BOOKING_HOURS)).date()
    (
        selected,
        selected_date,
        is_action,
        is_next_month,
        is_prev_month,
    ) = await calendar_picker.process_calendar_selection(update, context)
    if selected:
        redis_service.update_change_booking_field(update, "finish_booking_date", selected_date)
        LoggerService.info(
            __name__,
            "select finish date",
            update,
            **{"finish_date": selected_date.date()},
        )
        return await finish_time_message(update, context)
    elif is_action:
        LoggerService.info(
            __name__, "select finish date", update, **{"finish_date": "back"}
        )
        return await start_time_message(update, context)
    elif is_next_month or is_prev_month:
        query = update.callback_query
        start_period, end_period = date_time_helper.month_bounds(selected_date)
        feature_booking = database_service.get_booking_by_start_date_period(
            start_period, end_period
        )

        # Exclude current user's booking from occupied slots
        draft = redis_service.get_change_booking(update)
        if draft and draft.selected_booking_id:
            feature_booking = [b for b in feature_booking if b.id != draft.selected_booking_id]

        available_days = date_time_helper.get_free_dayes_slots(
            feature_booking,
            target_month=start_period.month,
            target_year=start_period.year,
        )

        # Update special dates info for the new month
        special_dates_info = get_special_dates_info(
            selected_date.month, selected_date.year
        )
        message = (
            "📅 <b>Выберите дату завершения бронирования.</b>\n"
            f"Вы выбрали дату и время заезда: {draft.start_booking_date.strftime('%d.%m.%Y %H:%M')}.\n"
            "Теперь укажите день, когда планируете выехать.\n"
            "📌 Выезд должен быть позже времени заезда."
        )
        if special_dates_info:
            message += f"\n\n{special_dates_info}"

        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
            reply_markup=calendar_picker.create_calendar(
                selected_date,
                min_date=min_date_booking,
                max_date=max_date_booking,
                action_text="Назад",
                callback_prefix="-FINISH",
                available_days=available_days,
            ),
        )
    return CHANGE_BOOKING_DATE


@safe_callback_query()
async def enter_finish_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    selected, time, is_action = await hours_picker.process_hours_selection(
        update, context
    )
    if selected:
        draft = redis_service.get_change_booking(update)
        finish_booking_date = draft.finish_booking_date.replace(hour=time.hour, minute=time.minute)
        redis_service.update_change_booking_field(update, "finish_booking_date", finish_booking_date)

        LoggerService.info(
            __name__,
            "select finish time",
            update,
            **{"finish_time": finish_booking_date.time()},
        )

        booking = database_service.get_booking_by_id(draft.selected_booking_id)
        created_bookings = database_service.get_booking_by_start_date_period(
            draft.start_booking_date, finish_booking_date
        )

        if (
            booking.tariff == Tariff.WORKER or booking.tariff == Tariff.INCOGNITA_WORKER
        ) and tariff_helper.is_interval_in_allowed_ranges(
            draft.start_booking_date.time(), finish_booking_date.time()
        ) == False:
            error_message = (
                "❌ <b>Ошибка!</b>\n\n"
                "⏳ <b>Выбранные дата и время не соответствуют условиям тарифа 'Рабочий'.</b>\n"
                "⚠️ В рамках этого тарифа бронирование возможно только с 11:00 до 20:00 или с 22:00 до 9:00.\n\n"
                "🔄 Пожалуйста, выберите другое время начала бронирования.\n\n"
                "ℹ️ Если вы планируете забронировать в другое время — выберите, пожалуйста, тариф '12 часов', 'Суточно' или 'Инкогнито'."
            )
            LoggerService.warning(__name__, "incorect time for tariff Worker", update)
            return await start_date_message(
                update, context, error_message=error_message
            )

        is_any_booking = any(b.id != booking.id for b in created_bookings)
        if is_any_booking:
            error_message = (
                "❌ <b>Ошибка!</b>\n\n"
                "⏳ <b>Выбранные дата и время недоступны.</b>\n"
                "⚠️ Дата начала и конца бронирования пересекается с другим бронированием.\n\n"
                f"🧹 После каждого клиента нам нужно подготовить дом. Уборка занимает <b>{CLEANING_HOURS} часа</b>.\n\n"
                "🔄 Пожалуйста, выберите новую дату начала бронирования."
            )
            LoggerService.info(
                __name__, "there are bookings between the selected dates", update
            )
            return await start_date_message(
                update, context, error_message=error_message
            )

        selected_duration = finish_booking_date - draft.start_booking_date
        duration_booking_hours = date_time_helper.seconds_to_hours(
            selected_duration.total_seconds()
        )
        rental_price = calculation_rate_service.get_by_tariff(booking.tariff)
        booking_duration_hours = max(
            (booking.end_date - booking.start_date).total_seconds() / 3600,
            rental_price.duration_hours,
        )
        if duration_booking_hours > booking_duration_hours:
            error_message = (
                "❌ <b>Ошибка!</b>\n\n"
                "⏳ <b>Максимальная продолжительность тарифа превышена.</b>\n"
                f"🕒 Длительность <b>{rental_price.name}</b>: {rental_price.duration_hours} ч.\n\n"
                "🔄 Пожалуйста, повторите попытку и выберите доступный вариант.\n\n"
                "📅 Выберите новую дату начала бронирования."
            )
            return await start_date_message(
                update, context, error_message=error_message
            )

        return await confirm_message(update, context)
    elif is_action:
        LoggerService.info(
            __name__, "select finish time", update, **{"finish_time": "back"}
        )
        return await finish_date_message(update, context)
    return CHANGE_BOOKING_DATE


@safe_callback_query()
async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    LoggerService.info(__name__, "Confirm booking", update)

    draft = redis_service.get_change_booking(update)
    if not draft or not draft.selected_booking_id:
        LoggerService.warning(__name__, "Draft is None or booking_id is missing (double click protection)", update)
        return await back_navigation(update, context)

    booking = database_service.get_booking_by_id(draft.selected_booking_id)

    # Calculate new price based on new dates
    selected_duration = draft.finish_booking_date - draft.start_booking_date
    duration_booking_hours = date_time_helper.seconds_to_hours(
        selected_duration.total_seconds()
    )

    # Calculate new price with date-specific pricing rules
    new_price = calculation_rate_service.calculate_price_for_date(
        booking_date=draft.start_booking_date.date(),
        tariff=booking.tariff,
        duration_hours=duration_booking_hours,
        is_sauna=booking.has_sauna,
        is_photoshoot=booking.has_photoshoot,
        is_secret_room=booking.has_secret_room,
        is_second_room=booking.has_green_bedroom or booking.has_white_bedroom,
    )

    updated_booking = database_service.update_booking(
        booking.id,
        start_date=draft.start_booking_date,
        end_date=draft.finish_booking_date,
        is_date_changed=True,
        price=new_price,
    )

    # Get user for calendar update
    user = database_service.get_user_by_id(booking.user_id)

    # Update Google Calendar event with new time and description
    if updated_booking.calendar_event_id:
        calendar_service.move_event(
            updated_booking.calendar_event_id,
            draft.start_booking_date,
            draft.finish_booking_date,
            booking=updated_booking,
            user=user)

    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await admin_handler.inform_changing_booking_date(
        update, context, updated_booking, draft.old_booking_date
    )

    # Prepare confirmation message
    message = (
        f"✅ <b>Бронирование успешно перенесено!</b>\n\n"
        f"📅 <b>С:</b> {draft.start_booking_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"📅 <b>До:</b> {draft.finish_booking_date.strftime('%d.%m.%Y %H:%M')}"
    )

    # Show price change if it occurred
    if new_price != booking.price:
        message += (
            f"\n\n💰 <b>Цена изменена:</b>\n"
            f"💵 <b>Было:</b> {booking.price} руб.\n"
            f"💵 <b>Стало:</b> {new_price} руб."
        )

    message += ".\n"

    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query, text=message, reply_markup=reply_markup
    )
    redis_service.clear_change_booking(update)
    return CHANGE_BOOKING_DATE


async def choose_booking_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    error_message: Optional[str] = None,
):
    draft = redis_service.get_change_booking(update)
    booking_list = database_service.get_booking_by_user_contact(draft.user_contact)
    selected_bookings = list(
        filter(lambda x: x.start_date.date() >= date.today(), booking_list)
    )

    if not selected_bookings or len(selected_bookings) == 0:
        return await warning_message(update, context)

    # Store booking IDs in Redis
    booking_ids = [b.id for b in selected_bookings]
    redis_service.update_change_booking_field(update, "selected_bookings", booking_ids)

    keyboard = []
    for booking in selected_bookings:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{booking.start_date.strftime('%d.%m.%Y %H:%M')} - {booking.end_date.strftime('%d.%m.%Y %H:%M')}",
                    callback_data=f"CHANGE-BOOKING_{booking.id}",
                )
            ]
        )

    keyboard.append([InlineKeyboardButton("Назад в меню", callback_data=END)])
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "📅 <b>Выберите бронирование, которое хотите изменить.</b>\n"
    if error_message:
        message = message + "\n\n" + error_message

    if update.message == None:
        await update.callback_query.answer()
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
            reply_markup=reply_markup,
        )
    else:
        await update.message.reply_text(
            text=message, parse_mode="HTML", reply_markup=reply_markup
        )

    return CHANGE_BOOKING_DATE


async def start_date_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    error_message: Optional[str] = None,
):
    today = date.today()
    max_date_booking = today + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = today
    start_period, end_period = date_time_helper.month_bounds(today)
    feature_booking = database_service.get_booking_by_start_date_period(start_period, end_period)

    # Exclude current user's booking from occupied slots
    draft = redis_service.get_change_booking(update)
    if draft and draft.selected_booking_id:
        feature_booking = [b for b in feature_booking if b.id != draft.selected_booking_id]

    available_days = date_time_helper.get_free_dayes_slots(
        feature_booking, target_month=today.month, target_year=today.year
    )

    special_dates_info = get_special_dates_info(today.month, today.year)

    if error_message:
        message = error_message
        if special_dates_info:
            message += f"\n\n{special_dates_info}"
    else:
        message = (
            "✅ <b>Ваше бронирование найдено!</b>\n\n"
            "📅 <b>Введите новую дату, на которую хотите перенести бронирование.</b>"
        )
        if special_dates_info:
            message += f"\n\n{special_dates_info}"

    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text=message,
        reply_markup=calendar_picker.create_calendar(
            today,
            min_date=min_date_booking,
            max_date=max_date_booking,
            action_text="Назад в меню",
            callback_prefix="-START",
            available_days=available_days,
        ),
    )
    return CHANGE_BOOKING_DATE


@safe_callback_query()
async def start_time_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    draft = redis_service.get_change_booking(update)
    booking = database_service.get_booking_by_id(draft.selected_booking_id)

    feature_booking = database_service.get_booking_by_start_date_period(
        draft.start_booking_date.date() - timedelta(days=2),
        draft.start_booking_date.date() + timedelta(days=2),
    )

    # Exclude current user's booking from occupied slots
    if draft and draft.selected_booking_id:
        feature_booking = [b for b in feature_booking if b.id != draft.selected_booking_id]

    available_slots = date_time_helper.get_free_time_slots(
        feature_booking, draft.start_booking_date.date()
    )

    special_date_info = get_special_date_info_for_day(draft.start_booking_date.date())

    if len(available_slots) == 0:
        message = f"⏳ <b>К сожалению, все слоты заняты для {draft.start_booking_date.strftime('%d.%m.%Y')}.</b>\n"
    else:
        message = (
            "⏳ <b>Выберите время начала бронирования.</b>\n"
            f"Вы выбрали дату заезда: {draft.start_booking_date.strftime('%d.%m.%Y')}.\n"
            "Теперь укажите удобное время заезда.\n"
            "⛔ - время уже забронировано\n"
        )
        if booking.tariff == Tariff.WORKER or booking.tariff == Tariff.INCOGNITA_WORKER:
            message += (
                "\n📌 <b>Для тарифа 'Рабочий' доступны интервалы:</b>\n"
                "🕚 11:00 – 20:00\n"
                "🌙 22:00 – 09:00"
            )

    if special_date_info:
        message += f"\n\n{special_date_info}"

    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text=message,
        reply_markup=hours_picker.create_hours_picker(
            action_text="Назад",
            free_slots=available_slots,
            date=draft.start_booking_date.date(),
            callback_prefix="-START",
        ),
    )
    return CHANGE_BOOKING_DATE


@safe_callback_query()
async def finish_date_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    draft = redis_service.get_change_booking(update)
    today = date.today()
    max_date_booking = today + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = (draft.start_booking_date + timedelta(hours=MIN_BOOKING_HOURS)).date()

    start_period, end_period = date_time_helper.month_bounds(draft.start_booking_date.date())
    feature_booking = database_service.get_booking_by_start_date_period(start_period, end_period)

    # Exclude current user's booking from occupied slots
    if draft and draft.selected_booking_id:
        feature_booking = [b for b in feature_booking if b.id != draft.selected_booking_id]

    available_days = date_time_helper.get_free_dayes_slots(
        feature_booking, target_month=start_period.month, target_year=start_period.year
    )

    special_dates_info = get_special_dates_info(
        draft.start_booking_date.month, draft.start_booking_date.year
    )

    message = (
        "📅 <b>Выберите дату завершения бронирования.</b>\n"
        f"Вы выбрали дату и время заезда: {draft.start_booking_date.strftime('%d.%m.%Y %H:%M')}.\n"
        "Теперь укажите день, когда планируете выехать.\n"
        "📌 Выезд должен быть позже времени заезда."
    )
    if special_dates_info:
        message += f"\n\n{special_dates_info}"

    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text=message,
        reply_markup=calendar_picker.create_calendar(
            draft.start_booking_date.date(),
            min_date=min_date_booking,
            max_date=max_date_booking,
            action_text="Назад",
            callback_prefix="-FINISH",
            available_days=available_days,
        ),
    )
    return CHANGE_BOOKING_DATE


@safe_callback_query()
async def finish_time_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    draft = redis_service.get_change_booking(update)
    feature_booking = database_service.get_booking_by_start_date_period(
        draft.finish_booking_date.date() - timedelta(days=2),
        draft.finish_booking_date.date() + timedelta(days=2),
    )

    # Exclude current user's booking from occupied slots
    if draft and draft.selected_booking_id:
        feature_booking = [b for b in feature_booking if b.id != draft.selected_booking_id]

    start_time = (
        time(0, 0)
        if draft.start_booking_date.date() != draft.finish_booking_date.date()
        else (draft.start_booking_date + timedelta(hours=MIN_BOOKING_HOURS)).time()
    )
    available_slots = date_time_helper.get_free_time_slots(
        feature_booking, draft.finish_booking_date.date(), start_time=start_time
    )

    special_date_info = get_special_date_info_for_day(draft.finish_booking_date.date())

    if len(available_slots) == 0:
        message = f"⏳ <b>К сожалению, все слоты заняты для {draft.finish_booking_date.strftime('%d.%m.%Y')}.</b>\n"
    else:
        message = (
            "⏳ <b>Выберите времня завершения бронирования.</b>\n"
            f"Вы выбрали заезд: {draft.start_booking_date.strftime('%d.%m.%Y %H:%M')}.\n"
            f"Вы выбрали дату выезда: {draft.finish_booking_date.strftime('%d.%m.%Y')}.\n"
            "Теперь укажите время, когда хотите освободить дом.\n"
            "⛔ - время уже забронировано\n"
        )

    if special_date_info:
        message += f"\n\n{special_date_info}"

    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text=message,
        reply_markup=hours_picker.create_hours_picker(
            action_text="Назад",
            free_slots=available_slots,
            date=draft.finish_booking_date.date(),
            callback_prefix="-FINISH",
        ),
    )
    return CHANGE_BOOKING_DATE


async def confirm_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    draft = redis_service.get_change_booking(update)
    booking = database_service.get_booking_by_id(draft.selected_booking_id)

    keyboard = [
        [
            InlineKeyboardButton(
                "Подтвердить", callback_data=f"CHANGE-CONFIRM_{CONFIRM}"
            )
        ],
        [InlineKeyboardButton("Назад в меню", callback_data=f"CHANGE-CONFIRM_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Calculate potential new price to show user
    selected_duration = draft.finish_booking_date - draft.start_booking_date
    duration_booking_hours = date_time_helper.seconds_to_hours(
        selected_duration.total_seconds()
    )

    potential_new_price = calculation_rate_service.calculate_price_for_date(
        booking_date=draft.start_booking_date.date(),
        tariff=booking.tariff,
        duration_hours=duration_booking_hours,
        is_sauna=booking.has_sauna,
        is_photoshoot=booking.has_photoshoot,
        is_secret_room=booking.has_secret_room,
        is_second_room=booking.has_green_bedroom or booking.has_white_bedroom,
    )

    message = (
        f"📅 Подтвердите изменение даты бронирования:\n"
        f"🔹 <b>С</b> {draft.old_booking_date.strftime('%d.%m.%Y')} \n"
        f"🔹 <b>На</b> {draft.start_booking_date.strftime('%d.%m.%Y %H:%M')} "
        f"до {draft.finish_booking_date.strftime('%d.%m.%Y %H:%M')}"
    )

    # Show price change if it would occur
    if potential_new_price != booking.price:
        message += (
            f"\n\n💰 <b>Цена изменится:</b>\n"
            f"💵 <b>Было:</b> {booking.price} руб.\n"
            f"💵 <b>Будет:</b> {potential_new_price} руб."
        )

    message += "\n\n✅ Подтвердить изменения?"

    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query, text=message, reply_markup=reply_markup
    )
    return CHANGE_BOOKING_DATE


async def warning_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    draft = redis_service.get_change_booking(update)
    LoggerService.info(__name__, "Not found bookings", update)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="❌ <b>Ошибка!</b>\n"
        f"🔍 Не удалось найти бронирование для аккаунта {draft.user_contact}.\n"
        "🔄 Пожалуйста, попробуйте еще раз.\n\n"
        "📲 Укажите ваш <b>Telegram</b> или номер телефона:\n\n"
        "🔹 <b>Telegram:</b> @username (начинайте с @)\n"
        "🔹 <b>Телефон:</b> +375XXXXXXXXX (обязательно с +375)\n"
        "❗️ Пожалуйста, вводите данные строго в указанном формате.",
        parse_mode="HTML",
        reply_markup=reply_markup,
    )
    return CHANGE_BOOKING_DATE_VALIDATE_USER


def get_special_dates_info(target_month: int = None, target_year: int = None) -> str:
    """Get special pricing dates info for display in calendar messages."""
    today = date.today()
    if target_month is None:
        target_month = today.month
    if target_year is None:
        target_year = today.year

    rules = date_pricing_service._try_load_rules()
    special_dates = []

    for rule in rules:
        if not rule.is_active:
            continue

        # Check if rule overlaps with target month
        rule_start = datetime.strptime(rule.start_date, "%Y-%m-%d").date()
        rule_end = datetime.strptime(rule.end_date, "%Y-%m-%d").date()
        month_start = date(target_year, target_month, 1)

        # Get last day of month
        if target_month == 12:
            month_end = date(target_year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(target_year, target_month + 1, 1) - timedelta(days=1)

        # Check if rule overlaps with this month
        if rule_end >= month_start and rule_start <= month_end:
            # Collect dates that are in this month
            current_date = max(rule_start, month_start)
            end_date = min(rule_end, month_end)

            while current_date <= end_date:
                special_dates.append((current_date, rule))
                current_date += timedelta(days=1)

    if not special_dates:
        return ""

    # Group by rule and format
    formatted_dates = []
    processed_rules = set()

    for date_obj, rule in special_dates:
        if rule.rule_id not in processed_rules:
            rule_dates = [d[0] for d in special_dates if d[1].rule_id == rule.rule_id]
            if len(rule_dates) == 1:
                date_str = rule_dates[0].strftime("%d.%m")
            else:
                date_str = f"{min(rule_dates).strftime('%d.%m')}-{max(rule_dates).strftime('%d.%m')}"

            description = rule.description or rule.name or "Специальная цена"
            formatted_dates.append(
                f"• {date_str}: {description} ({rule.price_override} руб.)"
            )
            processed_rules.add(rule.rule_id)

    return "🎯 <b>Специальные цены:</b>\n" + "\n".join(formatted_dates)


def get_special_date_info_for_day(target_date: date) -> str:
    """Get special pricing info for a specific date."""
    effective_rule = date_pricing_service.get_effective_rule(target_date)
    if effective_rule:
        description = (
            effective_rule.description or effective_rule.name or "Специальная цена"
        )
        return f"🎯 <b>Специальная цена:</b> {description} ({effective_rule.price_override} руб.)"
    return ""
