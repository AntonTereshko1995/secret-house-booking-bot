import sys
import os
from src.models.enum.booking_step import BookingStep
from src.services.navigation_service import NavigationService
from src.services.redis_service import RedisService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.logger_service import LoggerService
from src.decorators.callback_error_handler import safe_callback_query
from matplotlib.dates import relativedelta
from db.models.booking import BookingBase
from src.date_time_picker import calendar_picker, hours_picker
from src.services.database_service import DatabaseService
from src.config.config import (
    MIN_BOOKING_HOURS,
    PERIOD_IN_MONTHS,
    PREPAYMENT,
    CLEANING_HOURS,
    BANK_PHONE_NUMBER,
    BANK_CARD_NUMBER,
)
from src.services.calculation_rate_service import CalculationRateService
from src.services.date_pricing_service import DatePricingService
from datetime import date, time, timedelta, datetime
from telegram import Document, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from src.handlers import menu_handler
from src.helpers import date_time_helper, string_helper, tariff_helper, bedroom_halper
from src.handlers import admin_handler
from src.models.enum.bedroom import Bedroom
from src.models.enum.tariff import Tariff
from typing import Optional
from src.constants import (
    BACK,
    BOOKING_COMMENT,
    BOOKING_WRITE_CODE,
    END,
    MENU,
    BOOKING,
    SET_USER,
    BOOKING_VALIDATE_USER,
    SKIP,
    CONFIRM,
    BOOKING_PHOTO_UPLOAD,
    CASH_PAY,
    INCOGNITO_WINE,
    INCOGNITO_TRANSFER,
    PROMOCODE_INPUT,
)

MAX_PEOPLE = 6

rate_service = CalculationRateService()
date_pricing_service = DatePricingService()
database_service = DatabaseService()
redis_service = RedisService()
navigation_service = NavigationService()


def get_handler():
    return [
        CallbackQueryHandler(select_tariff, pattern=f"^BOOKING-TARIFF_(\d+|{END})$"),
        CallbackQueryHandler(
            include_photoshoot, pattern=f"^BOOKING-PHOTO_(?i:true|false|{END})$"
        ),
        CallbackQueryHandler(
            include_secret_room, pattern=f"^BOOKING-SECRET_(?i:true|false|{END})$"
        ),
        CallbackQueryHandler(
            include_sauna, pattern=f"^BOOKING-SAUNA_(?i:true|false|{END})$"
        ),
        CallbackQueryHandler(select_bedroom, pattern=f"^BOOKING-BEDROOM_(\d+|{END})$"),
        CallbackQueryHandler(
            select_additional_bedroom,
            pattern=f"^BOOKING-ADD-BEDROOM_(?i:true|false|{END})$",
        ),
        CallbackQueryHandler(
            select_number_of_people, pattern=f"^BOOKING-PEOPLE_(\d+|{END})$"
        ),
        CallbackQueryHandler(
            enter_start_date, pattern=f"^CALENDAR-CALLBACK-START_(.+|{BACK})$"
        ),
        CallbackQueryHandler(
            enter_start_time, pattern=f"^HOURS-CALLBACK-START_(.+|{BACK})$"
        ),
        CallbackQueryHandler(
            enter_finish_date, pattern=f"^CALENDAR-CALLBACK-FINISH_(.+|{BACK})$"
        ),
        CallbackQueryHandler(
            enter_finish_time, pattern=f"^HOURS-CALLBACK-FINISH_(.+|{BACK})$"
        ),
        CallbackQueryHandler(write_secret_code, pattern=f"^BOOKING-CODE_({END})$"),
        CallbackQueryHandler(pay, pattern=f"^BOOKING-PAY_({CASH_PAY}|{END})$"),
        CallbackQueryHandler(enter_user_contact, pattern=SET_USER),
        CallbackQueryHandler(
            confirm_booking, pattern=f"^BOOKING-CONFIRM_({CONFIRM}|{END})$"
        ),
        CallbackQueryHandler(back_navigation, pattern=f"^BOOKING-BACK_{BACK}$"),
        CallbackQueryHandler(
            handle_wine_preference, pattern=f"^BOOKING-WINE_(.+|{END})$"
        ),
        CallbackQueryHandler(
            handle_transfer_skip, pattern=f"^BOOKING-TRANSFER_({SKIP}|{END})$"
        ),
        CallbackQueryHandler(skip_promocode, pattern=f"^BOOKING-PROMO_({SKIP}|{END})$"),
    ]


@safe_callback_query()
async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler.show_menu(update, context)
    LoggerService.info(__name__, "Back to menu", update)
    redis_service.clear_booking(update)
    return MENU


@safe_callback_query()
async def generate_tariff_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # await update.callback_query.answer()
    # return await send_approving_to_admin(update, context, None, is_cash=True)
    LoggerService.info(__name__, "Generate tariff", update)

    redis_service.init_booking(update)
    redis_service.update_booking_field(update, "navigation_step", BookingStep.TARIFF)

    keyboard = [
        [
            InlineKeyboardButton(
                f"🔹 {tariff_helper.get_name(Tariff.INCOGNITA_DAY)} — {rate_service.get_price(Tariff.INCOGNITA_DAY)} руб",
                callback_data=f"BOOKING-TARIFF_{Tariff.INCOGNITA_DAY.value}",
            )
        ],
        [
            InlineKeyboardButton(
                f"🔹 {tariff_helper.get_name(Tariff.INCOGNITA_HOURS)} — {rate_service.get_price(Tariff.INCOGNITA_HOURS)} руб",
                callback_data=f"BOOKING-TARIFF_{Tariff.INCOGNITA_HOURS.value}",
            )
        ],
        [
            InlineKeyboardButton(
                f"🔹 {tariff_helper.get_name(Tariff.INCOGNITA_WORKER)} — {rate_service.get_price(Tariff.INCOGNITA_WORKER)} руб",
                callback_data=f"BOOKING-TARIFF_{Tariff.INCOGNITA_WORKER.value}",
            )
        ],
        [
            InlineKeyboardButton(
                f"🔹 {tariff_helper.get_name(Tariff.DAY)} — {rate_service.get_price(Tariff.DAY)} руб",
                callback_data=f"BOOKING-TARIFF_{Tariff.DAY.value}",
            )
        ],
        [
            InlineKeyboardButton(
                f"🔹 {tariff_helper.get_name(Tariff.DAY_FOR_COUPLE)} — {rate_service.get_price(Tariff.DAY_FOR_COUPLE)} руб",
                callback_data=f"BOOKING-TARIFF_{Tariff.DAY_FOR_COUPLE.value}",
            )
        ],
        [
            InlineKeyboardButton(
                f"🔹 {tariff_helper.get_name(Tariff.HOURS_12)} — от {rate_service.get_price(Tariff.HOURS_12)} руб",
                callback_data=f"BOOKING-TARIFF_{Tariff.HOURS_12.value}",
            )
        ],
        [
            InlineKeyboardButton(
                f"🔹 {tariff_helper.get_name(Tariff.WORKER)} — от {rate_service.get_price(Tariff.WORKER)} руб",
                callback_data=f"BOOKING-TARIFF_{Tariff.WORKER.value}",
            )
        ],
        [
            InlineKeyboardButton(
                f"🔹 {tariff_helper.get_name(Tariff.GIFT)}",
                callback_data=f"BOOKING-TARIFF_{Tariff.GIFT.value}",
            )
        ],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-TARIFF_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text="<b>Выберите тариф для бронирования:</b>",
            reply_markup=reply_markup,
        )

    return BOOKING


@safe_callback_query()
async def select_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        data = string_helper.get_callback_data(update.callback_query.data)
        if data == str(END):
            return await back_navigation(update, context)

    tariff = tariff_helper.get_by_str(data)
    redis_service.update_booking_field(update, "tariff", tariff)
    LoggerService.info(__name__, "Select tariff", update, kwargs={"tariff": tariff})

    if tariff != Tariff.GIFT:
        rental_rate = rate_service.get_by_tariff(tariff)
        redis_service.update_booking_field(update, "rental_rate", rental_rate)

    if (
        tariff == Tariff.INCOGNITA_DAY
        or tariff == Tariff.INCOGNITA_HOURS
        or tariff == Tariff.INCOGNITA_WORKER
    ):
        redis_service.update_booking_field(update, "is_sauna_included", True)
        redis_service.update_booking_field(update, "is_secret_room_included", True)
        redis_service.update_booking_field(update, "is_white_room_included", True)
        redis_service.update_booking_field(update, "is_green_room_included", True)
        redis_service.update_booking_field(
            update, "is_additional_bedroom_included", True
        )

        if tariff == Tariff.INCOGNITA_DAY:
            redis_service.update_booking_field(update, "is_photoshoot_included", True)
            return await photoshoot_message(update, context)
        elif tariff == Tariff.INCOGNITA_HOURS or tariff == Tariff.INCOGNITA_WORKER:
            redis_service.update_booking_field(update, "is_photoshoot_included", False)
            return await count_of_people_message(update, context)
    elif tariff == Tariff.DAY or tariff == Tariff.DAY_FOR_COUPLE:
        redis_service.update_booking_field(update, "is_photoshoot_included", False)
        redis_service.update_booking_field(update, "is_sauna_included", False)
        redis_service.update_booking_field(update, "is_secret_room_included", True)
        redis_service.update_booking_field(update, "is_white_room_included", True)
        redis_service.update_booking_field(update, "is_green_room_included", True)
        redis_service.update_booking_field(
            update, "is_additional_bedroom_included", True
        )
        return await sauna_message(update, context)
    elif tariff == Tariff.HOURS_12 or tariff == Tariff.WORKER:
        return await bedroom_message(update, context)
    elif tariff == Tariff.GIFT:
        return await write_code_message(update, context)
    elif tariff == Tariff.INCOGNITA_HOURS:
        return await count_of_people_message(update, context)


@safe_callback_query()
async def enter_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, "Enter user contact", update)
    redis_service.update_booking_field(update, "navigation_step", BookingStep.CONTACT)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "📲 Укажите ваш <b>Telegram</b> или номер телефона:\n\n"
        "🔹 <b>Telegram:</b> @username (начинайте с @)\n"
        "или\n"
        "🔹 <b>Телефон:</b> +375XXXXXXXXX (обязательно с +375)\n"
        "❗️ Пожалуйста, вводите данные строго в указанном формате."
    )
    if update.message == None:
        if update.callback_query:
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

    return BOOKING_VALIDATE_USER


async def check_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user_input = update.message.text
        is_valid, cleaned_contact = string_helper.is_valid_user_contact(user_input)
        if is_valid:
            booking = redis_service.get_booking(update)
            redis_service.update_booking_field(update, "user_contact", cleaned_contact)

            # Save contact to database
            try:
                chat_id = navigation_service.get_chat_id(update)
                database_service.update_user_contact(chat_id, cleaned_contact)
                LoggerService.info(
                    __name__,
                    "User contact saved to database",
                    update,
                    kwargs={"chat_id": chat_id, "contact": cleaned_contact},
                )
            except Exception as e:
                LoggerService.error(
                    __name__,
                    "Failed to save user contact to database",
                    exception=e,
                    kwargs={"contact": cleaned_contact},
                )
                # Continue with booking flow even if DB update fails

            LoggerService.info(
                __name__, "User name is valid", update, kwargs={"user_name": user_input}
            )
            if booking.gift_id:
                if is_any_additional_payment(update):
                    return await pay(update, context)
                else:
                    return await send_approving_to_admin(update, context, is_cash=True)
            else:
                return await pay(update, context)
        else:
            LoggerService.warning(__name__, "User name is invalid", update)
            await update.message.reply_text(
                "❌ <b>Ошибка!</b>\n"
                "Имя пользователя в Telegram или номер телефона введены некорректно.\n\n"
                "🔄 Пожалуйста, попробуйте еще раз.\n\n"
                "🔹 <b>Telegram:</b> @username (начинайте с @)\n"
                "или\n"
                "🔹 <b>Телефон:</b> +375XXXXXXXXX (обязательно с +375)\n",
                parse_mode="HTML",
            )
    return BOOKING_VALIDATE_USER


@safe_callback_query()
async def include_photoshoot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    is_photoshoot_included = eval(data)
    redis_service.update_booking_field(
        update, "is_photoshoot_included", is_photoshoot_included
    )
    LoggerService.info(
        __name__,
        "Include photoshoot",
        update,
        kwargs={"is_photoshoot_included": is_photoshoot_included},
    )
    return await count_of_people_message(update, context)


@safe_callback_query()
async def include_sauna(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    is_sauna_included = eval(data)
    redis_service.update_booking_field(update, "is_sauna_included", is_sauna_included)
    LoggerService.info(
        __name__,
        "Include sauna",
        update,
        kwargs={"is_sauna_included": is_sauna_included},
    )

    booking = redis_service.get_booking(update)
    if booking.gift_id:
        return await navigate_next_step_for_gift(update, context)
    elif booking.tariff == Tariff.DAY or booking.tariff == Tariff.DAY_FOR_COUPLE:
        return await photoshoot_message(update, context)

    return await count_of_people_message(update, context)


@safe_callback_query()
async def include_secret_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    is_secret_room_included = eval(data)
    redis_service.update_booking_field(
        update, "is_secret_room_included", is_secret_room_included
    )
    LoggerService.info(
        __name__,
        "Include secret room",
        update,
        kwargs={"is_secret_room_included": is_secret_room_included},
    )
    booking = redis_service.get_booking(update)
    if booking.gift_id:
        return await navigate_next_step_for_gift(update, context)

    return await sauna_message(update, context)


@safe_callback_query()
async def select_bedroom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    bedroom = bedroom_halper.get_by_str(data)
    LoggerService.info(__name__, "Select bedroom", update, kwargs={"bedroom": bedroom})

    if bedroom == Bedroom.GREEN:
        redis_service.update_booking_field(update, "is_white_room_included", False)
        redis_service.update_booking_field(update, "is_green_room_included", True)
    else:
        redis_service.update_booking_field(update, "is_white_room_included", True)
        redis_service.update_booking_field(update, "is_green_room_included", False)

    booking = redis_service.get_booking(update)
    if booking.gift_id:
        return await navigate_next_step_for_gift(update, context)

    return await additional_bedroom_message(update, context)


@safe_callback_query()
async def select_additional_bedroom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    is_added = eval(data)
    LoggerService.info(
        __name__, "Select additional bedroom", update, kwargs={"is_added": is_added}
    )
    if is_added:
        redis_service.update_booking_field(
            update, "is_additional_bedroom_included", True
        )
        redis_service.update_booking_field(update, "is_white_room_included", True)
        redis_service.update_booking_field(update, "is_green_room_included", True)
    else:
        redis_service.update_booking_field(
            update, "is_additional_bedroom_included", False
        )

    booking = redis_service.get_booking(update)
    if booking.gift_id:
        return await navigate_next_step_for_gift(update, context)

    return await secret_room_message(update, context)


@safe_callback_query()
async def select_number_of_people(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    number_of_guests = int(data)
    redis_service.update_booking_field(update, "number_of_guests", number_of_guests)
    LoggerService.info(
        __name__,
        "Select number of people",
        update,
        kwargs={"number_of_guests": number_of_guests},
    )
    return await start_date_message(update, context)


@safe_callback_query()
async def write_secret_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message == None:
        await update.callback_query.answer()
        data = string_helper.get_callback_data(update.callback_query.data)
        if data == str(END):
            return await back_navigation(update, context)

    LoggerService.info(__name__, "Write secret code", update)
    return await init_gift_code(update, context)


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
        booking = redis_service.get_booking(update)
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

        redis_service.update_booking_field(update, "start_booking_date", selected_date)
        LoggerService.info(
            __name__,
            "select start date",
            update,
            kwargs={"start_date": selected_date.date()},
        )
        return await start_time_message(update, context)
    elif is_action:
        LoggerService.info(
            __name__, "select start date", update, kwargs={"start_date": "back"}
        )
        return await back_navigation(update, context)
    elif is_next_month or is_prev_month:
        start_period, end_period = date_time_helper.month_bounds(selected_date)
        feature_booking = database_service.get_booking_by_period(
            start_period, end_period
        )
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
            "📅 <b>Выберите дату начала бронирования.</b>\n"
            "Укажите день, когда хотите заселиться в дом."
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

    return BOOKING


@safe_callback_query()
async def enter_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    selected, time, is_action = await hours_picker.process_hours_selection(
        update, context
    )
    if selected:
        booking = redis_service.get_booking(update)
        start_booking_date = booking.start_booking_date.replace(
            hour=time.hour, minute=time.minute
        )
        redis_service.update_booking_field(
            update, "start_booking_date", start_booking_date
        )
        LoggerService.info(
            __name__,
            "select start time",
            update,
            kwargs={"start_time": start_booking_date.time()},
        )
        return await finish_date_message(update, context)
    elif is_action:
        LoggerService.info(
            __name__, "select start time", update, kwargs={"start_time": "back"}
        )
        return await start_date_message(update, context)
    return BOOKING


@safe_callback_query()
async def enter_finish_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    booking = redis_service.get_booking(update)
    max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = (
        booking.start_booking_date + timedelta(hours=MIN_BOOKING_HOURS)
    ).date()
    (
        selected,
        selected_date,
        is_action,
        is_next_month,
        is_prev_month,
    ) = await calendar_picker.process_calendar_selection(update, context)
    if selected:
        redis_service.update_booking_field(update, "finish_booking_date", selected_date)
        LoggerService.info(
            __name__,
            "select finish date",
            update,
            kwargs={"finish_date": selected_date.date()},
        )
        return await finish_time_message(update, context)
    elif is_action:
        LoggerService.info(
            __name__, "select finish date", update, kwargs={"finish_date": "back"}
        )
        return await start_time_message(update, context)
    elif is_next_month or is_prev_month:
        start_period, end_period = date_time_helper.month_bounds(selected_date)
        feature_booking = database_service.get_booking_by_period(
            start_period, end_period
        )
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
            f"Вы выбрали дату и время заезда: {booking.start_booking_date.strftime('%d.%m.%Y %H:%M')}.\n"
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

    return BOOKING


@safe_callback_query()
async def enter_finish_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    selected, time, is_action = await hours_picker.process_hours_selection(
        update, context
    )
    if selected:
        booking = redis_service.get_booking(update)
        finish_booking_date = booking.finish_booking_date.replace(
            hour=time.hour, minute=time.minute
        )
        redis_service.update_booking_field(
            update, "finish_booking_date", finish_booking_date
        )
        LoggerService.info(
            __name__,
            "select finish time",
            update,
            kwargs={"finish_time": finish_booking_date.time()},
        )

        if (
            booking.tariff == Tariff.WORKER or booking.tariff == Tariff.INCOGNITA_WORKER
        ) and tariff_helper.is_interval_in_allowed_ranges(
            booking.start_booking_date.time(), finish_booking_date.time()
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

        is_any_booking = database_service.is_booking_between_dates(
            booking.start_booking_date - timedelta(hours=CLEANING_HOURS),
            finish_booking_date + timedelta(hours=CLEANING_HOURS),
        )
        if is_any_booking:
            error_message = (
                "❌ <b>Ошибка!</b>\n\n"
                "⏳ <b>Выбранные дата и время недоступны.</b>\n"
                "⚠️ Дата начала и конца бронирования пересекается с другим бронированием.\n\n"
                "🔄 Пожалуйста, выберите новую дату начала бронирования."
            )
            LoggerService.warning(
                __name__, "there are bookings between the selected dates", update
            )
            return await start_date_message(
                update, context, error_message=error_message
            )

        return await comment_message(update, context)
    elif is_action:
        LoggerService.info(
            __name__, "select finish time", update, kwargs={"finish_time": "cancel"}
        )
        return await finish_date_message(update, context)
    return BOOKING


async def write_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.COMMENT)

    if update.message == None:
        if update.callback_query:
            await update.callback_query.answer()
            data = string_helper.get_callback_data(update.callback_query.data)
            if data == str(END):
                return await back_navigation(update, context)
    else:
        booking_comment = update.message.text
        redis_service.update_booking_field(update, "booking_comment", booking_comment)
        LoggerService.info(
            __name__, "Write comment", update, kwargs={"comment": booking_comment}
        )

    # Check if Incognito tariff and route to questionnaire
    booking = redis_service.get_booking(update)
    if (
        booking.tariff == Tariff.INCOGNITA_DAY
        or booking.tariff == Tariff.INCOGNITA_HOURS
        or booking.tariff == Tariff.INCOGNITA_WORKER
    ):
        return await wine_preference_message(update, context)
    else:
        # Route to promocode entry for non-incognito flows
        return await promocode_entry_message(update, context)


async def promocode_entry_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show promo code entry prompt with SKIP option"""
    redis_service.update_booking_field(update, "navigation_step", BookingStep.PROMOCODE)

    keyboard = [
        [InlineKeyboardButton("Пропустить", callback_data=f"BOOKING-PROMO_{SKIP}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-PROMO_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "🎟️ <b>Есть промокод?</b>\n\n"
        "Введите промокод, чтобы получить скидку.\n"
        "Или нажмите <b>Пропустить</b>, если у вас нет промокода."
    )

    if update.callback_query:
        await update.callback_query.answer()
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
            reply_markup=reply_markup,
        )
    elif update.message:
        await update.message.reply_text(
            text=message, parse_mode="HTML", reply_markup=reply_markup
        )

    LoggerService.info(__name__, "Promocode entry message displayed", update)
    return PROMOCODE_INPUT


async def handle_promocode_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for promo code"""
    if not update.message or not update.message.text:
        return PROMOCODE_INPUT

    promo_code = update.message.text.strip().upper()
    booking = redis_service.get_booking(update)

    # Validate against booking start_date and tariff
    is_valid, message_text, promo = database_service.validate_promocode(
        promo_code, booking.start_booking_date.date(), booking.tariff
    )

    if is_valid:
        # Store promocode_id in redis, will be saved to DB later
        redis_service.update_booking_field(update, "promocode_id", promo.id)
        redis_service.update_booking_field(
            update, "promocode_discount", promo.discount_percentage
        )

        await update.message.reply_text(
            f"✅ {message_text}\n"
            f"🎉 Скидка <b>{promo.discount_percentage}%</b> будет применена!",
            parse_mode="HTML",
        )

        LoggerService.info(
            __name__,
            "Promocode applied",
            update,
            kwargs={
                "promocode": promo_code,
                "discount": promo.discount_percentage,
            },
        )

        # Progress to next step
        return await confirm_pay(update, context)
    else:
        # Show error with skip button, stay in same state for retry
        keyboard = [
            [InlineKeyboardButton("Пропустить", callback_data=f"BOOKING-PROMO_{SKIP}")],
            [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-PROMO_{END}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"{message_text}\n\n"
            "Попробуйте ввести другой код или нажмите <b>Пропустить</b>.",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )

        LoggerService.warning(
            __name__,
            "Invalid promocode",
            update,
            kwargs={"promocode": promo_code, "error": message_text},
        )

        return PROMOCODE_INPUT


@safe_callback_query()
async def skip_promocode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip promocode entry"""
    await update.callback_query.answer()

    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    LoggerService.info(__name__, "Promocode skipped", update)
    return await confirm_pay(update, context)


async def confirm_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(
        update, "navigation_step", BookingStep.CONFIRM_BOOKING
    )
    booking = redis_service.get_booking(update)

    keyboard = [
        [InlineKeyboardButton("Перейти к оплате.", callback_data=SET_USER)],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-BACK_{BACK}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    selected_duration = booking.finish_booking_date - booking.start_booking_date
    duration_booking_hours = round(
        date_time_helper.seconds_to_hours(int(selected_duration.total_seconds()))
    )

    # Use date-aware pricing calculation
    booking_start_date = booking.start_booking_date.date()
    price = rate_service.calculate_price_for_date(
        booking_date=booking_start_date,
        tariff=booking.tariff,
        duration_hours=duration_booking_hours,
        is_sauna=booking.is_sauna_included,
        is_secret_room=booking.is_secret_room_included,
        is_second_room=booking.is_additional_bedroom_included,
        is_photoshoot=booking.is_photoshoot_included,
        count_people=booking.number_of_guests,
    )

    # Apply promocode discount if available
    promocode_info = ""
    if hasattr(booking, "promocode_id") and booking.promocode_id:
        if hasattr(booking, "promocode_discount") and booking.promocode_discount:
            discount_percentage = booking.promocode_discount
            discount_amount = int(price * (discount_percentage / 100))
            price = price - discount_amount
            # Save discounted price to Redis
            redis_service.update_booking_field(update, "price", price)
            promocode_info = (
                f"\n🎟️ <b>Промокод:</b> скидка {discount_percentage}% "
                f"(-{discount_amount} руб.)\n"
            )

    extra_hours = duration_booking_hours - booking.rental_rate.duration_hours
    categories = rate_service.get_price_categories(
        booking.rental_rate,
        booking.is_sauna_included,
        booking.is_secret_room_included,
        booking.is_additional_bedroom_included,
        booking.number_of_guests,
        extra_hours,
    )
    photoshoot_text = ", фото сессия" if booking.is_photoshoot_included else ""

    # Check for special pricing information
    special_pricing_info = ""
    if date_pricing_service.has_date_override(booking_start_date):
        pricing_description = date_pricing_service.get_rule_description(
            booking_start_date
        )
        if pricing_description:
            special_pricing_info = (
                f"\n🎯 <b>Специальная цена:</b> {pricing_description}\n"
            )

    LoggerService.info(
        __name__,
        "Confirm pay",
        update,
        kwargs={"price": price, "has_special_pricing": bool(special_pricing_info)},
    )

    if booking.gift_id:
        gift = database_service.get_gift_by_id(booking.gift_id)
        payed_price = gift.price if gift else booking.rental_rate.price
        price = int(price - payed_price)
        message = (
            f"💰 <b>Доплата: {price} руб.</b>\n{special_pricing_info}{promocode_info}\n"
            f"📌 <b>Что включено:</b> {categories}{photoshoot_text}\n"
            f"📅 <b>Заезд:</b> {booking.start_booking_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"📅 <b>Выезд:</b> {booking.finish_booking_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"💬 <b>Комментарий:</b> {booking.booking_comment if booking.booking_comment else ''}\n\n"
            "✅ <b>Подтвердите бронирование дома</b>"
        )
    else:
        message = (
            f"💰 <b>Итоговая сумма:</b> {price} руб.\n{special_pricing_info}{promocode_info}\n"
            f"📌 <b>Включено:</b> {categories}{photoshoot_text}.\n"
            f"📅 <b>Заезд:</b> {booking.start_booking_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"📅 <b>Выезд:</b> {booking.finish_booking_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"💬 <b>Комментарий:</b> {booking.booking_comment if booking.booking_comment else ''}\n\n"
            "✅ <b>Подтвердить бронирование?</b>"
        )

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

    redis_service.update_booking_field(update, "price", price)
    return BOOKING


@safe_callback_query()
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.PAY)
    booking = redis_service.get_booking(update)

    if update.callback_query and update.callback_query.data:
        await update.callback_query.answer()
        if update.callback_query.data == str(END):
            return await back_navigation(update, context)

    LoggerService.info(__name__, "Pay", update)
    keyboard = []
    if booking.gift_id:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "Оплата наличкой", callback_data=f"BOOKING-PAY_{CASH_PAY}"
                )
            ]
        )
        message = (
            f"💰 <b>Сумма доплаты:</b> {booking.price} руб.\n\n"
            "📌 <b>Доступные способы оплаты (Альфа-Банк):</b>\n"
            f"📱 По номеру телефона: <b>{BANK_PHONE_NUMBER}</b>\n"
            f"💳 По номеру карты: <b>{BANK_CARD_NUMBER}</b>\n"
            "💵 Наличными при заселении.\n\n"
            "❗️ <b>Важно!</b>\n"
            "После оплаты отправьте скриншот или PDF документ с чеком.\n"
            "📩 Только так мы сможем подтвердить получение предоплаты.\n\n"
            "🙏 Спасибо за понимание!"
        )
    else:
        message = (
            f"💰 <b>Общая сумма оплаты:</b> {booking.price} руб.\n\n"
            f"🔹 <b>Предоплата:</b> {PREPAYMENT} руб.\n"
            "💡 Предоплата не возвращается при отмене бронирования, но вы можете перенести бронь на другую дату.\n\n"
            "📌 <b>Способы оплаты (Альфа-Банк):</b>\n"
            f"📱 По номеру телефона: <b>{BANK_PHONE_NUMBER}</b>. Обращаем внимание, что предоплату не нужно переводить на счёт мобильного оператора Лайф.\n"
            f"💳 По номеру карты: <b>{BANK_CARD_NUMBER}</b>\n\n"
            "❗ <b>Важно!</b>\n"
            "После оплаты отправьте скриншот или PDF документ с чеком.\n"
            "📩 Это необходимо для подтверждения вашей предоплаты.\n\n"
            "🙏 Спасибо за понимание!"
        )
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    if update.message:
        await update.message.reply_text(
            text=message, parse_mode="HTML", reply_markup=reply_markup
        )
    else:
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
            reply_markup=reply_markup,
        )
    return BOOKING_PHOTO_UPLOAD


async def cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, "Cancel booking", update)
    await update.callback_query.answer()

    booking = redis_service.get_booking(update)
    if booking:
        database_service.update_booking(booking.id, is_canceled=True)
    return await back_navigation(update, context)


@safe_callback_query()
async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, "Confirm booking", update)

    redis_service.update_booking_field(update, "navigation_step", BookingStep.FINISH)
    booking = redis_service.get_booking(update)

    keyboard = [
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-BACK_{BACK}")]
    ]
    message = (
        "✨ <b>Спасибо за доверие к The Secret House!</b> ✨\n"
        "📩 Мы скоро отправим вам сообщение с подтверждением бронирования.\n\n"
        f"📅 <b>Дата заезда:</b> {booking.start_booking_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"🏁 <b>Дата выезда:</b> {booking.finish_booking_date.strftime('%d.%m.%Y %H:%M')}\n\n"
        "🛎 <i>Если у вас есть вопросы, напишите нам — мы всегда на связи!</i>"
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

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
    return BOOKING


async def photoshoot_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(
        update, "navigation_step", BookingStep.PHOTOSHOOT
    )
    booking = redis_service.get_booking(update)

    keyboard = [
        [InlineKeyboardButton("Да", callback_data=f"BOOKING-PHOTO_{str(True)}")],
        [InlineKeyboardButton("Нет", callback_data=f"BOOKING-PHOTO_{str(False)}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-PHOTO_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"📸 <b>Хотите заказать фотосессию?</b>\n"
        "✨ Она уже включена в стоимость выбранного тарифа!\n"
        "Фотосессия длится 2 часа.\n"
        "Instagram фотографа: https://www.instagram.com/eugenechulitskyphoto/\n\n"
        f"💰 <b>Стоимость:</b> {booking.rental_rate.photoshoot_price} руб.\n"
    )
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
    return BOOKING


async def secret_room_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(
        update, "navigation_step", BookingStep.SECRET_ROOM
    )
    booking = redis_service.get_booking(update)

    keyboard = [
        [InlineKeyboardButton("Да", callback_data=f"BOOKING-SECRET_{str(True)}")],
        [InlineKeyboardButton("Нет", callback_data=f"BOOKING-SECRET_{str(False)}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-SECRET_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "🔞 <b>Хотите воспользоваться 'Секретной комнатой'?</b>\n\n"
        f"💰 <b>Стоимость:</b> {booking.rental_rate.secret_room_price} руб.\n"
        f"📌 <b>Для тарифа:</b> {tariff_helper.get_name(booking.tariff)}"
    )
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
    return BOOKING


async def write_code_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE, is_error: bool = False
):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.COMMENT)
    booking = redis_service.get_booking(update)

    keyboard = [
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-CODE_{END}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_error:
        message = "❌ <b>Ошибка:</b> код введён некорректно или устарел.\n🔄 Пожалуйста, введите код ещё раз."
    elif booking.tariff == Tariff.GIFT:
        message = "🎁 <b>Введите проверочный код подарочного сертификата.</b>\n🔢 Длина кода — 15 символов."

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
    return BOOKING_WRITE_CODE


async def count_of_people_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(
        update, "navigation_step", BookingStep.NUMBER_GUESTS
    )
    booking = redis_service.get_booking(update)

    keyboard = [
        [InlineKeyboardButton("1 гость", callback_data="BOOKING-PEOPLE_1")],
        [InlineKeyboardButton("2 гостя", callback_data="BOOKING-PEOPLE_2")],
        [InlineKeyboardButton("3 гостя", callback_data="BOOKING-PEOPLE_3")],
        [InlineKeyboardButton("4 гостя", callback_data="BOOKING-PEOPLE_4")],
        [InlineKeyboardButton("5 гостей", callback_data="BOOKING-PEOPLE_5")],
        [InlineKeyboardButton("6 гостей", callback_data="BOOKING-PEOPLE_6")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-BACK_{BACK}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    additional_people_text = (
        f"💰 <b>Доплата за каждого дополнительного гостя:</b> {booking.rental_rate.extra_people_price} руб."
        if booking.rental_rate.max_people != MAX_PEOPLE
        else ""
    )
    message = (
        "👥 <b>Сколько гостей будет присутствовать?</b>\n\n"
        f"📌 <b>Максимальное количество гостей для '{booking.rental_rate.name}':</b> {booking.rental_rate.max_people} чел.\n"
        f"{additional_people_text}"
    )

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
    return BOOKING


def get_special_dates_info(target_month: int = None, target_year: int = None) -> str:
    """Get formatted information about special pricing dates for a specific month."""
    rules = date_pricing_service._try_load_rules()

    if not rules:
        return ""

    active_rules = [
        rule for rule in rules if rule.is_active and rule.price_override is not None
    ]
    if not active_rules:
        return ""

    # Filter rules by month if specified
    if target_month and target_year:
        filtered_rules = []
        for rule in active_rules:
            start_date_obj = datetime.strptime(rule.start_date, "%Y-%m-%d")
            end_date_obj = datetime.strptime(rule.end_date, "%Y-%m-%d")

            # Check if rule overlaps with target month
            target_month_start = date(target_year, target_month, 1)
            if target_month == 12:
                target_month_end = date(target_year + 1, 1, 1) - timedelta(days=1)
            else:
                target_month_end = date(target_year, target_month + 1, 1) - timedelta(
                    days=1
                )

            # Rule overlaps if start <= month_end and end >= month_start
            if (
                start_date_obj.date() <= target_month_end
                and end_date_obj.date() >= target_month_start
            ):
                filtered_rules.append(rule)

        active_rules = filtered_rules

    if not active_rules:
        return ""

    info_lines = []
    info_lines.append("🎯 <b>Специальные цены:</b>")

    for rule in active_rules:
        # Format date range with DD.MM format
        start_date_obj = datetime.strptime(rule.start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(rule.end_date, "%Y-%m-%d")

        if rule.start_date == rule.end_date:
            date_str = start_date_obj.strftime("%d.%m")
        else:
            date_str = (
                f"{start_date_obj.strftime('%d.%m')} - {end_date_obj.strftime('%d.%m')}"
            )

        # Format time range if specified
        time_str = ""
        if rule.start_time and rule.end_time:
            time_str = f" ({rule.start_time}-{rule.end_time})"

        # Format price
        price_str = f"{rule.price_override} руб."

        info_lines.append(
            f"• {date_str}{time_str}: {price_str} - {rule.description or rule.name}"
        )

    return "\n".join(info_lines) + "\n"


def get_special_date_info_for_day(target_date: date) -> str:
    """Get formatted information about special pricing for a specific date."""
    if not date_pricing_service.has_date_override(target_date):
        return ""

    effective_rule = date_pricing_service.get_effective_rule(target_date)
    if not effective_rule or not effective_rule.price_override:
        return ""

    # Format time range if specified
    time_str = ""
    if effective_rule.start_time and effective_rule.end_time:
        time_str = f" ({effective_rule.start_time}-{effective_rule.end_time})"

    price_str = f"{effective_rule.price_override} руб."
    description = effective_rule.description or effective_rule.name

    return f"\n🎯 <b>Специальная цена{time_str}:</b> {price_str} - {description}\n"


async def start_date_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    error_message: Optional[str] = None,
):
    redis_service.update_booking_field(
        update, "navigation_step", BookingStep.START_DATE
    )
    today = date.today()
    max_date_booking = today + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = today

    # Check if user already has a selected date to preserve the month
    booking = redis_service.get_booking(update)
    if booking and booking.start_booking_date:
        # Use the month from the previously selected date
        reference_date = booking.start_booking_date.date()
    else:
        # Use today as reference
        reference_date = today

    start_period, end_period = date_time_helper.month_bounds(reference_date)
    feature_booking = database_service.get_booking_by_period(start_period, end_period)
    available_days = date_time_helper.get_free_dayes_slots(
        feature_booking,
        target_month=reference_date.month,
        target_year=reference_date.year,
    )

    special_dates_info = get_special_dates_info(
        reference_date.month, reference_date.year
    )

    if error_message:
        message = error_message
        if special_dates_info:
            message += f"\n\n{special_dates_info}"
    else:
        message = (
            "📅 <b>Выберите дату начала бронирования.</b>\n"
            "Укажите день, когда хотите заселиться в дом."
        )
        if special_dates_info:
            message += f"\n\n{special_dates_info}"

    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text=message,
        reply_markup=calendar_picker.create_calendar(
            reference_date,
            min_date=min_date_booking,
            max_date=max_date_booking,
            action_text="Назад в меню",
            callback_prefix="-START",
            available_days=available_days,
        ),
    )
    return BOOKING


async def start_time_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(
        update, "navigation_step", BookingStep.START_TIME
    )
    booking = redis_service.get_booking(update)

    feature_booking = database_service.get_booking_by_period(
        booking.start_booking_date.date() - timedelta(days=2),
        booking.start_booking_date.date() + timedelta(days=2),
    )
    available_slots = date_time_helper.get_free_time_slots(
        feature_booking, booking.start_booking_date.date()
    )

    special_date_info = get_special_date_info_for_day(booking.start_booking_date.date())

    if len(available_slots) == 0:
        message = f"⏳ <b>К сожалению, все слоты заняты для {booking.start_booking_date.strftime('%d.%m.%Y')}.</b>\n"
    else:
        message = (
            "⏳ <b>Выберите время начала бронирования.</b>\n"
            f"Вы выбрали дату заезда: {booking.start_booking_date.strftime('%d.%m.%Y')}.\n"
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
        message += special_date_info

    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text=message,
        reply_markup=hours_picker.create_hours_picker(
            action_text="Назад",
            free_slots=available_slots,
            date=booking.start_booking_date.date(),
            callback_prefix="-START",
        ),
    )
    return BOOKING


async def finish_date_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(
        update, "navigation_step", BookingStep.FINISH_DATE
    )
    booking = redis_service.get_booking(update)

    today = date.today()
    max_date_booking = today + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = (
        booking.start_booking_date + timedelta(hours=MIN_BOOKING_HOURS)
    ).date()

    # Use finish_booking_date if available, otherwise use start_booking_date
    if booking.finish_booking_date:
        reference_date = booking.finish_booking_date.date()
    else:
        reference_date = booking.start_booking_date.date()

    start_period, end_period = date_time_helper.month_bounds(reference_date)
    feature_booking = database_service.get_booking_by_period(start_period, end_period)
    available_days = date_time_helper.get_free_dayes_slots(
        feature_booking,
        target_month=reference_date.month,
        target_year=reference_date.year,
    )

    special_dates_info = get_special_dates_info(
        reference_date.month, reference_date.year
    )

    message = (
        "📅 <b>Выберите дату завершения бронирования.</b>\n"
        f"Вы выбрали дату и время заезда: {booking.start_booking_date.strftime('%d.%m.%Y %H:%M')}.\n"
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
            reference_date,
            min_date=min_date_booking,
            max_date=max_date_booking,
            action_text="Назад",
            callback_prefix="-FINISH",
            available_days=available_days,
        ),
    )
    return BOOKING


async def finish_time_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(
        update, "navigation_step", BookingStep.FINISH_TIME
    )
    booking = redis_service.get_booking(update)

    feature_booking = database_service.get_booking_by_period(
        booking.finish_booking_date.date() - timedelta(days=2),
        booking.finish_booking_date.date() + timedelta(days=2),
    )
    start_time = (
        time(0, 0)
        if booking.start_booking_date.date() != booking.finish_booking_date.date()
        else (booking.start_booking_date + timedelta(hours=MIN_BOOKING_HOURS)).time()
    )
    available_slots = date_time_helper.get_free_time_slots(
        feature_booking, booking.finish_booking_date.date(), start_time=start_time
    )

    special_date_info = get_special_date_info_for_day(
        booking.finish_booking_date.date()
    )

    if len(available_slots) == 0:
        message = f"⏳ <b>К сожалению, все слоты заняты для {booking.finish_booking_date.strftime('%d.%m.%Y')}.</b>\n"
    else:
        message = (
            "⏳ <b>Выберите времня завершения бронирования.</b>\n"
            f"Вы выбрали заезд: {booking.start_booking_date.strftime('%d.%m.%Y %H:%M')}.\n"
            f"Вы выбрали дату выезда: {booking.finish_booking_date.strftime('%d.%m.%Y')}.\n"
            "Теперь укажите время, когда хотите освободить дом.\n"
            "⛔ - время уже забронировано\n"
        )

    if special_date_info:
        message += special_date_info
    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text=message,
        reply_markup=hours_picker.create_hours_picker(
            action_text="Назад",
            free_slots=available_slots,
            date=booking.finish_booking_date.date(),
            callback_prefix="-FINISH",
        ),
    )
    return BOOKING


async def sauna_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.SAUNA)
    booking = redis_service.get_booking(update)

    keyboard = [
        [InlineKeyboardButton("Да", callback_data=f"BOOKING-SAUNA_{str(True)}")],
        [InlineKeyboardButton("Нет", callback_data=f"BOOKING-SAUNA_{str(False)}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-SAUNA_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "🧖‍♂️ <b>Хотите воспользоваться сауной?</b>\n\n"
        f"💰 <b>Стоимость:</b> {booking.rental_rate.sauna_price} руб.\n"
        f"📌 <b>Для тарифа:</b> {tariff_helper.get_name(booking.tariff)}"
    )

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
    return BOOKING


async def comment_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.COMMENT)
    keyboard = [
        [InlineKeyboardButton("Пропустить", callback_data=f"BOOKING-COMMENT_{SKIP}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-COMMENT_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="💬 <b>Хотите оставить комментарий?</b>\n"
        "Если у вас есть пожелания или дополнительная информация, напишите их здесь.",
        reply_markup=reply_markup,
    )
    return BOOKING_COMMENT


async def wine_preference_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(
        update, "navigation_step", BookingStep.WINE_PREFERENCE
    )

    keyboard = [
        [InlineKeyboardButton("Не нужно вино", callback_data="BOOKING-WINE_none")],
        [
            InlineKeyboardButton(
                "Белое сладкое", callback_data="BOOKING-WINE_white-sweet"
            )
        ],
        [
            InlineKeyboardButton(
                "Белое полусладкое", callback_data="BOOKING-WINE_white-semi-sweet"
            )
        ],
        [InlineKeyboardButton("Белое сухое", callback_data="BOOKING-WINE_white-dry")],
        [
            InlineKeyboardButton(
                "Белое полусухое", callback_data="BOOKING-WINE_white-semi-dry"
            )
        ],
        [
            InlineKeyboardButton(
                "Красное сладкое", callback_data="BOOKING-WINE_red-sweet"
            )
        ],
        [
            InlineKeyboardButton(
                "Красное полусладкое", callback_data="BOOKING-WINE_red-semi-sweet"
            )
        ],
        [InlineKeyboardButton("Красное сухое", callback_data="BOOKING-WINE_red-dry")],
        [
            InlineKeyboardButton(
                "Красное полусухое", callback_data="BOOKING-WINE_red-semi-dry"
            )
        ],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-WINE_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "🍷 <b>Мы бесплатно подготавливаем вино и легкие закуски для тарифа Инкогнито.</b>\n\n"
        "Какое вино вы предпочитаете?"
    )

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

    return INCOGNITO_WINE


@safe_callback_query()
async def handle_wine_preference(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle wine preference button click.
    Stores selection in Redis and transitions to transfer question.
    """
    await update.callback_query.answer()

    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    wine_preference = data  # "none", "sweet", "semi_sweet", "dry", "semi_dry"
    redis_service.update_booking_field(update, "wine_preference", wine_preference)

    LoggerService.info(
        __name__,
        "Wine preference selected",
        update,
        kwargs={"wine_preference": wine_preference},
    )

    return await transfer_message(update, context)


async def transfer_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display transfer service question for Incognito tariffs.
    User can click skip button or type address.
    """
    redis_service.update_booking_field(
        update, "navigation_step", BookingStep.TRANSFER_ADDRESS
    )

    keyboard = [
        [InlineKeyboardButton("Не нужно", callback_data=f"BOOKING-TRANSFER_{SKIP}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-TRANSFER_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "🚗 <b>Мы бесплатно предлагаем трансфер из дома и в дом на авто бизнес класса.</b>\n\n"
        "Введите Ваш адрес или нажмите 'Не нужно':"
    )

    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text=message,
        reply_markup=reply_markup,
    )

    return INCOGNITO_TRANSFER


@safe_callback_query()
async def handle_transfer_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle "Не нужно" button click for transfer.
    Stores None for transfer_address and proceeds to payment.
    """
    await update.callback_query.answer()

    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    redis_service.update_booking_field(update, "transfer_address", None)
    LoggerService.info(__name__, "Transfer service declined", update)

    return await confirm_pay(update, context)


async def handle_transfer_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle text input for transfer address.
    Validates address length and stores in Redis.
    """
    if update.message and update.message.text:
        address = update.message.text.strip()

        # Validate address length (min 5 chars, max 500 chars)
        if not address or len(address) < 5:
            LoggerService.warning(__name__, "Transfer address too short", update)
            await update.message.reply_text(
                "❌ <b>Ошибка!</b>\n"
                "Адрес слишком короткий. Пожалуйста, введите полный адрес.\n\n"
                "Или нажмите 'Не нужно', если трансфер не требуется.",
                parse_mode="HTML",
            )
            return INCOGNITO_TRANSFER

        if len(address) > 500:
            LoggerService.warning(__name__, "Transfer address too long", update)
            await update.message.reply_text(
                "❌ <b>Ошибка!</b>\n"
                "Адрес слишком длинный. Пожалуйста, введите адрес короче 500 символов.",
                parse_mode="HTML",
            )
            return INCOGNITO_TRANSFER

        redis_service.update_booking_field(update, "transfer_address", address)

        LoggerService.info(
            __name__,
            "Transfer address saved",
            update,
            kwargs={"address": address[:50]},  # Log first 50 chars only
        )

        return await confirm_pay(update, context)

    return INCOGNITO_TRANSFER


async def bedroom_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(
        update, "navigation_step", BookingStep.FIRST_BEDROOM
    )
    keyboard = [
        [
            InlineKeyboardButton(
                "🛏 Белая спальня",
                callback_data=f"BOOKING-BEDROOM_{Bedroom.WHITE.value}",
            )
        ],
        [
            InlineKeyboardButton(
                "🌿 Зеленая спальня",
                callback_data=f"BOOKING-BEDROOM_{Bedroom.GREEN.value}",
            )
        ],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-BEDROOM_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = "🛏 <b>Выберите спальную комнату:</b>"
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
    return BOOKING


async def additional_bedroom_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    redis_service.update_booking_field(
        update, "navigation_step", BookingStep.SECOND_BEDROOM
    )
    booking = redis_service.get_booking(update)

    keyboard = [
        [InlineKeyboardButton("Да", callback_data=f"BOOKING-ADD-BEDROOM_{str(True)}")],
        [
            InlineKeyboardButton(
                "Нет", callback_data=f"BOOKING-ADD-BEDROOM_{str(False)}"
            )
        ],
        [
            InlineKeyboardButton(
                "Назад в меню", callback_data=f"BOOKING-ADD-BEDROOM_{END}"
            )
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text=(
            "🛏 <b>Нужна ли вам вторая спальная комната?</b>\n\n"
            f"💰 <b>Стоимость:</b> {booking.rental_rate.second_bedroom_price} руб.\n"
            f"📌 <b>Для тарифа:</b> {tariff_helper.get_name(booking.tariff)}"
        ),
        reply_markup=reply_markup,
    )
    return BOOKING


def is_any_additional_payment(update: Update) -> bool:
    booking = redis_service.get_booking(update)

    if booking.gift_id:
        gift = database_service.get_gift_by_id(booking.gift_id)
        if gift.has_secret_room != booking.is_secret_room_included:
            return True
        elif gift.has_sauna != booking.is_sauna_included:
            return True
        elif gift.has_additional_bedroom != booking.is_additional_bedroom_included:
            return True
        elif booking.number_of_guests > booking.rental_rate.max_people:
            return True
        else:
            return False

    return False


async def navigate_next_step_for_gift(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    booking = redis_service.get_booking(update)
    if not booking.gift_id:
        return

    if (
        booking.tariff == Tariff.DAY_FOR_COUPLE
        or booking.tariff == Tariff.INCOGNITA_DAY
    ):
        return await photoshoot_message(update, context)
    elif booking.tariff == Tariff.INCOGNITA_HOURS or booking.tariff == Tariff.DAY:
        return await count_of_people_message(update, context)

    gift = database_service.get_gift_by_id(booking.gift_id)
    if (
        booking.is_white_room_included == False
        and booking.is_green_room_included == False
        and gift.has_additional_bedroom == False
    ):
        return await bedroom_message(update, context)
    elif booking.is_additional_bedroom_included == None:
        return await additional_bedroom_message(update, context)
    elif booking.is_secret_room_included == None:
        return await secret_room_message(update, context)
    elif booking.is_sauna_included == None:
        return await sauna_message(update, context)

    return await count_of_people_message(update, context)


def init_fields_for_gift(update: Update):
    booking = redis_service.get_booking(update)
    if not booking.gift_id:
        return

    gift = database_service.get_gift_by_id(booking.gift_id)
    if gift.has_secret_room:
        redis_service.update_booking_field(update, "is_secret_room_included", True)
    if gift.has_sauna:
        redis_service.update_booking_field(update, "is_sauna_included", True)
    if gift.has_additional_bedroom:
        redis_service.update_booking_field(
            update, "is_additional_bedroom_included", True
        )
        redis_service.update_booking_field(update, "is_white_room_included", True)
        redis_service.update_booking_field(update, "is_green_room_included", True)


async def init_gift_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return await write_code_message(update, context, True)

    gift = database_service.get_gift_by_code(update.message.text)
    if not gift:
        return await write_code_message(update, context, True)

    redis_service.update_booking_field(update, "gift_id", gift.id)
    redis_service.update_booking_field(update, "tariff", gift.tariff)

    rental_rate = rate_service.get_by_tariff(gift.tariff)
    redis_service.update_booking_field(update, "rental_rate", rental_rate)

    categories = rate_service.get_price_categories(
        rental_rate, gift.has_sauna, gift.has_secret_room, gift.has_additional_bedroom
    )
    await update.message.reply_text(
        f"🎉 <b>Поздравляем!</b> Вы успешно активировали сертификат!\n\n"
        f"📜 <b>Содержимое сертификата:</b> {categories}",
        parse_mode="HTML",
    )

    init_fields_for_gift(update)
    return await navigate_next_step_for_gift(update, context)


def save_booking_information(
    update: Update, chat_id: int, is_cash=False
) -> BookingBase:
    # booking = database_service.get_booking_by_id(1)
    # booking.start_date = datetime.today()
    # booking.end_date = datetime.today()
    # booking = database_service.add_booking(
    #     "@11111111111",
    #     datetime.today(),
    #     datetime.today(),
    #     booking.tariff,
    #     booking.has_photoshoot,
    #     booking.has_sauna,
    #     booking.has_white_bedroom,
    #     booking.has_green_bedroom,
    #     booking.has_secret_room,
    #     booking.number_of_guests,
    #     booking.price,
    #     booking.comment,
    #     chat_id,
    #     booking.gift_id,
    #     )

    cache_booking = redis_service.get_booking(update)
    booking = database_service.add_booking(
        cache_booking.user_contact,
        cache_booking.start_booking_date,
        cache_booking.finish_booking_date,
        cache_booking.tariff,
        cache_booking.is_photoshoot_included,
        cache_booking.is_sauna_included,
        cache_booking.is_white_room_included,
        cache_booking.is_green_room_included,
        cache_booking.is_secret_room_included,
        cache_booking.number_of_guests,
        cache_booking.price,
        cache_booking.booking_comment,
        cache_booking.gift_id,
        getattr(cache_booking, "promocode_id", None),
        cache_booking.wine_preference,
        cache_booking.transfer_address,
    )

    if booking == None:
        LoggerService.error(
            __name__,
            "Booking is None",
            user_contact=cache_booking.user_contact,
            start_booking_date=cache_booking.start_booking_date,
            finish_booking_date=cache_booking.finish_booking_date,
            tariff=cache_booking.tariff,
            is_photoshoot_included=cache_booking.is_photoshoot_included,
            is_sauna_included=cache_booking.is_sauna_included,
            is_white_room_included=cache_booking.is_white_room_included,
            is_green_room_included=cache_booking.is_green_room_included,
            is_secret_room_included=cache_booking.is_secret_room_included,
            number_of_guests=cache_booking.number_of_guests,
            price=cache_booking.price,
            booking_comment=cache_booking.booking_comment,
            chat_id=chat_id,
            gift_id=cache_booking.gift_id,
        )
        return None

    if is_cash:
        booking = database_service.update_booking(booking.id, prepayment=0)

    return booking


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document: Optional[Document] = None
    photo: Optional[str] = None
    if (
        update.message
        and update.message.document
        and update.message.document.mime_type == "application/pdf"
    ):
        document = update.message.document
    elif update.message and update.message.photo:
        photo = update.message.photo[-1].file_id

    LoggerService.info(__name__, "handle photo", update)
    return await send_approving_to_admin(update, context, photo, document)


async def cash_pay_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await send_approving_to_admin(update, context, is_cash=True)


async def send_approving_to_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    photo=None,
    document=None,
    is_cash=False,
):
    chat_id = navigation_service.get_chat_id(update)
    booking = save_booking_information(update, chat_id, is_cash)
    if not booking and update.message:
        await update.message.reply_text(
            text="❌ <b>Ошибка!</b>\n\n"
            "Не удалось сохранить информацию о бронировании.\n"
            "Пожалуйста, попробуйте ещё раз или свяжитесь с администратором.\n"
            "Нажмите на синюю кнопку 'Меню' и выберите 'Открыть Главное меню'. Далее выберите пункт меню 'Связаться с администратором'.\n\n"
            "🙏 Спасибо за понимание!",
            parse_mode="HTML",
        )
        return BOOKING

    await admin_handler.accept_booking_payment(
        update, context, booking, chat_id, photo, document, is_cash
    )
    return await confirm_booking(update, context)
