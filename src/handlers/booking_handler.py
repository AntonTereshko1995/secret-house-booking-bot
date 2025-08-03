import sys
import os
from src.models.enum.booking_step import BookingStep
from src.services.navigation_service import NavigatonService
from src.services.redis_service import RedisService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.logger_service import LoggerService
from matplotlib.dates import relativedelta
from db.models.booking import BookingBase
from src.date_time_picker import calendar_picker, hours_picker
from src.services.database_service import DatabaseService
from src.config.config import MIN_BOOKING_HOURS, PERIOD_IN_MONTHS, PREPAYMENT, CLEANING_HOURS, BANK_PHONE_NUMBER, BANK_CARD_NUMBER
from src.services.calculation_rate_service import CalculationRateService
from datetime import date, time, timedelta
from telegram import (Document, InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, CallbackQueryHandler)
from src.handlers import menu_handler
from src.helpers import date_time_helper, string_helper, string_helper, tariff_helper, bedroom_halper
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
    CASH_PAY)

MAX_PEOPLE = 6

rate_service = CalculationRateService()
database_service = DatabaseService()
redis_service = RedisService()
navigation_service = NavigatonService()

def get_handler():
    return [
        CallbackQueryHandler(select_tariff, pattern=f"^BOOKING-TARIFF_(\d+|{END})$"),
        CallbackQueryHandler(include_photoshoot, pattern=f"^BOOKING-PHOTO_(?i:true|false|{END})$"),
        CallbackQueryHandler(include_secret_room, pattern=f"^BOOKING-SECRET_(?i:true|false|{END})$"),
        CallbackQueryHandler(include_sauna, pattern=f"^BOOKING-SAUNA_(?i:true|false|{END})$"),
        CallbackQueryHandler(select_bedroom, pattern=f"^BOOKING-BEDROOM_(\d+|{END})$"),
        CallbackQueryHandler(select_additional_bedroom, pattern=f"^BOOKING-ADD-BEDROOM_(?i:true|false|{END})$"),
        CallbackQueryHandler(select_number_of_people, pattern=f"^BOOKING-PEOPLE_(\d+|{END})$"),
        CallbackQueryHandler(enter_start_date, pattern=f"^CALENDAR-CALLBACK-START_(.+|{BACK})$"),
        CallbackQueryHandler(enter_start_time, pattern=f"^HOURS-CALLBACK-START_(.+|{BACK})$"),
        CallbackQueryHandler(enter_finish_date, pattern=f"^CALENDAR-CALLBACK-FINISH_(.+|{BACK})$"),
        CallbackQueryHandler(enter_finish_time, pattern=f"^HOURS-CALLBACK-FINISH_(.+|{BACK})$"),
        CallbackQueryHandler(write_secret_code, pattern=f"^BOOKING-CODE_({END})$"),
        CallbackQueryHandler(pay, pattern=f"^BOOKING-PAY_({CASH_PAY}|{END})$"),
        CallbackQueryHandler(enter_user_contact, pattern=SET_USER),
        CallbackQueryHandler(confirm_booking, pattern=f"^BOOKING-CONFIRM_({CONFIRM}|{END})$"),
        CallbackQueryHandler(back_navigation, pattern=f"^BOOKING-BACK_{BACK}$"),
    ]

async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler.show_menu(update, context)
    LoggerService.info(__name__, f"Back to menu", update)
    redis_service.clear_booking(update)
    return MENU

async def generate_tariff_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # await update.callback_query.answer()
    # return await send_approving_to_admin(update, context, None, is_cash=True)
    LoggerService.info(__name__, f"Generate tariff", update)

    redis_service.init_booking(update)
    redis_service.update_booking_field(update, "navigation_step", BookingStep.TARIFF)

    keyboard = [
        [InlineKeyboardButton(
            f"🔹 {tariff_helper.get_name(Tariff.INCOGNITA_DAY)} — {rate_service.get_price(Tariff.INCOGNITA_DAY)} руб", 
            callback_data=f"BOOKING-TARIFF_{Tariff.INCOGNITA_DAY.value}")],
        [InlineKeyboardButton(
            f"🔹 {tariff_helper.get_name(Tariff.INCOGNITA_HOURS)} — {rate_service.get_price(Tariff.INCOGNITA_HOURS)} руб",
            callback_data=f"BOOKING-TARIFF_{Tariff.INCOGNITA_HOURS.value}")],
        [InlineKeyboardButton(
            f"🔹 {tariff_helper.get_name(Tariff.DAY)} — {rate_service.get_price(Tariff.DAY)} руб",
            callback_data=f"BOOKING-TARIFF_{Tariff.DAY.value}")],
        [InlineKeyboardButton(
            f"🔹 {tariff_helper.get_name(Tariff.DAY_FOR_COUPLE)} — {rate_service.get_price(Tariff.DAY_FOR_COUPLE)} руб",
            callback_data=f"BOOKING-TARIFF_{Tariff.DAY_FOR_COUPLE.value}")],
        [InlineKeyboardButton(
            f"🔹 {tariff_helper.get_name(Tariff.HOURS_12)} — от {rate_service.get_price(Tariff.HOURS_12)} руб",
            callback_data=f"BOOKING-TARIFF_{Tariff.HOURS_12.value}")],
        [InlineKeyboardButton(
            f"🔹 {tariff_helper.get_name(Tariff.WORKER)} — от {rate_service.get_price(Tariff.WORKER)} руб",
            callback_data=f"BOOKING-TARIFF_{Tariff.WORKER.value}")],
        [InlineKeyboardButton(
            f"🔹 {tariff_helper.get_name(Tariff.SUBSCRIPTION)} 🎟", 
            callback_data=f"BOOKING-TARIFF_{Tariff.SUBSCRIPTION.value}")],
        [InlineKeyboardButton(
            f"🔹 {tariff_helper.get_name(Tariff.GIFT)}", 
            callback_data=f"BOOKING-TARIFF_{Tariff.GIFT.value}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-TARIFF_{END}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text="<b>Выберите тариф для бронирования:</b>",
            reply_markup=reply_markup)
            
    return BOOKING

async def select_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        data = string_helper.get_callback_data(update.callback_query.data)
        if (data == str(END)):
            return await back_navigation(update, context)

    tariff = tariff_helper.get_by_str(data)
    redis_service.update_booking_field(update, "tariff", tariff)
    LoggerService.info(__name__, f"Select tariff", update, kwargs={'tariff': tariff})

    if tariff != Tariff.GIFT or tariff != Tariff.SUBSCRIPTION:
        rental_rate = rate_service.get_by_tariff(tariff)
        redis_service.update_booking_field(update, "rental_rate", rental_rate)

    if tariff == Tariff.INCOGNITA_DAY or tariff == Tariff.INCOGNITA_HOURS:
        redis_service.update_booking_field(update, "is_photoshoot_included", True)
        redis_service.update_booking_field(update, "is_sauna_included", True)
        redis_service.update_booking_field(update, "is_secret_room_included", True)
        redis_service.update_booking_field(update, "is_white_room_included", True)
        redis_service.update_booking_field(update, "is_green_room_included", True)
        redis_service.update_booking_field(update, "is_additional_bedroom_included", True)
        return await photoshoot_message(update, context)
    elif tariff == Tariff.DAY or tariff == Tariff.DAY_FOR_COUPLE:
        redis_service.update_booking_field(update, "is_photoshoot_included", False)
        redis_service.update_booking_field(update, "is_sauna_included", False)
        redis_service.update_booking_field(update, "is_secret_room_included", True)
        redis_service.update_booking_field(update, "is_white_room_included", True)
        redis_service.update_booking_field(update, "is_green_room_included", True)
        redis_service.update_booking_field(update, "is_additional_bedroom_included", True)
        return await sauna_message(update, context)
    elif tariff == Tariff.HOURS_12 or tariff == Tariff.WORKER:
        return await bedroom_message(update, context)
    elif tariff == Tariff.GIFT or tariff == Tariff.SUBSCRIPTION:
        return await write_code_message(update, context)
    elif tariff == Tariff.INCOGNITA_HOURS:
        return await count_of_people_message(update, context)

async def enter_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, f"Enter user contact", update)
    redis_service.update_booking_field(update, "navigation_step", BookingStep.CONTACT)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = ("📲 Укажите ваш <b>Telegram</b> или номер телефона:\n\n"
            "🔹 <b>Telegram:</b> @username (начинайте с @)\n"
            "или\n"
            "🔹 <b>Телефон:</b> +375XXXXXXXXX (обязательно с +375)\n"
            "❗️ Пожалуйста, вводите данные строго в указанном формате.")
    if (update.message == None):
        if update.callback_query:
            await update.callback_query.answer()
            await navigation_service.safe_edit_message_text(
                callback_query=update.callback_query,
                text=message,
                reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup)
        
    return BOOKING_VALIDATE_USER

async def check_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user_input = update.message.text
        is_valid = string_helper.is_valid_user_contact(user_input)
        if is_valid:
            booking = redis_service.get_booking(update)
            redis_service.update_booking_field(update, "user_contact", user_input)
            LoggerService.info(__name__, f"User name is valid", update, kwargs={'user_name': user_input})
            if booking.gift_id or booking.subscription_id:
                if is_any_additional_payment(update):
                    return await pay(update, context)
                else:
                    return await send_approving_to_admin(update, context, is_cash=True)
            else:
                return await pay(update, context)
        else:
            LoggerService.warning(__name__, f"User name is invalid", update)
            await update.message.reply_text(
                "❌ <b>Ошибка!</b>\n"
                "Имя пользователя в Telegram или номер телефона введены некорректно.\n\n"
                "🔄 Пожалуйста, попробуйте еще раз.\n\n"
                "🔹 <b>Telegram:</b> @username (начинайте с @)\n"
                "или\n"
                "🔹 <b>Телефон:</b> +375XXXXXXXXX (обязательно с +375)\n",
                parse_mode='HTML')
    return BOOKING_VALIDATE_USER

async def include_photoshoot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if (data == str(END)):
        return await back_navigation(update, context)

    is_photoshoot_included = eval(data)
    redis_service.update_booking_field(update, "is_photoshoot_included", is_photoshoot_included)
    LoggerService.info(__name__, f"Include photoshoot", update, kwargs={'is_photoshoot_included': is_photoshoot_included})
    return await count_of_people_message(update, context)

async def include_sauna(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if (data == str(END)):
        return await back_navigation(update, context)

    is_sauna_included = eval(data)
    redis_service.update_booking_field(update, "is_sauna_included", is_sauna_included)
    LoggerService.info(__name__, f"Include sauna", update, kwargs={'is_sauna_included': is_sauna_included})

    booking = redis_service.get_booking(update)
    if booking.gift_id:
        return await navigate_next_step_for_gift(update, context)
    elif booking.subscription_id:
        return await navigate_next_step_for_subscription(update, context)
    elif booking.tariff == Tariff.DAY or booking.tariff == Tariff.DAY_FOR_COUPLE:
        return await photoshoot_message(update, context)

    return await count_of_people_message(update, context)

async def include_secret_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if (data == str(END)):
        return await back_navigation(update, context)

    is_secret_room_included = eval(data)
    redis_service.update_booking_field(update, "is_secret_room_included", is_secret_room_included)
    LoggerService.info(__name__, f"Include secret room", update, kwargs={'is_secret_room_included': is_secret_room_included})
    booking = redis_service.get_booking(update)
    if booking.gift_id:
        return await navigate_next_step_for_gift(update, context)

    return await sauna_message(update, context)

async def select_bedroom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if (data == str(END)):
        return await back_navigation(update, context)

    bedroom = bedroom_halper.get_by_str(data)
    LoggerService.info(__name__, f"Select bedroom", update, kwargs={'bedroom': bedroom})

    if (bedroom == Bedroom.GREEN):
        redis_service.update_booking_field(update, "is_white_room_included", False)
        redis_service.update_booking_field(update, "is_green_room_included", True)
    else:
        redis_service.update_booking_field(update, "is_white_room_included", True)
        redis_service.update_booking_field(update, "is_green_room_included", False)

    booking = redis_service.get_booking(update)
    if booking.gift_id:
        return await navigate_next_step_for_gift(update, context)

    return await additional_bedroom_message(update, context)

async def select_additional_bedroom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if (data == str(END)):
        return await back_navigation(update, context)

    is_added = eval(data)
    LoggerService.info(__name__, f"Select additional bedroom", update, kwargs={'is_added': is_added})
    if is_added:
        redis_service.update_booking_field(update, "is_additional_bedroom_included", True)
        redis_service.update_booking_field(update, "is_white_room_included", True)
        redis_service.update_booking_field(update, "is_green_room_included", True)
    else:
        redis_service.update_booking_field(update, "is_additional_bedroom_included", False)

    booking = redis_service.get_booking(update)
    if booking.gift_id:
        return await navigate_next_step_for_gift(update, context)

    return await secret_room_message(update, context)

async def select_number_of_people(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if (data == str(END)):
        return await back_navigation(update, context)

    number_of_guests = int(data)
    redis_service.update_booking_field(update, "number_of_guests", number_of_guests)
    LoggerService.info(__name__, f"Select number of people", update, kwargs={'number_of_guests': number_of_guests})
    return await start_date_message(update, context)

async def write_secret_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message == None:
        await update.callback_query.answer()
        data = string_helper.get_callback_data(update.callback_query.data)
        if (data == str(END)):
            return await back_navigation(update, context)

    LoggerService.info(__name__, f"Write secret code", update)

    booking = redis_service.get_booking(update)
    if (booking.tariff == Tariff.GIFT):
        return await init_gift_code(update, context)
    else:
        return await init_subscription_code(update, context)

async def enter_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = date.today()
    selected, selected_date, is_action = await calendar_picker.process_calendar_selection(update, context, min_date=min_date_booking, max_date=max_date_booking, action_text="Назад в меню", callback_prefix="-START")
    if selected:
        booking = redis_service.get_booking(update)

        if not tariff_helper.is_booking_available(booking.tariff, selected_date):
            LoggerService.warning(__name__, f"start date is incorrect for {booking.tariff}", update)
            error_message = ("❌ <b>Ошибка!</b>\n\n"
                "⏳ <b>Тариф 'Рабочий' доступен только с понедельника по четверг.</b>\n"
                "🔄 Пожалуйста, выберите новую дату начала бронирования.")
            LoggerService.warning(__name__, f"there are bookings between the selected dates", update)
            return await start_date_message(update, context, error_message=error_message)
        
        redis_service.update_booking_field(update, "start_booking_date", selected_date)
        LoggerService.info(__name__, f"select start date", update, kwargs={'start_date': selected_date.date()})
        return await start_time_message(update, context)
    elif is_action:
        LoggerService.info(__name__, f"select start date", update, kwargs={'start_date': 'back'})
        return await back_navigation(update, context)
    return BOOKING

async def enter_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    selected, time, is_action = await hours_picker.process_hours_selection(update, context)
    if selected:
        booking = redis_service.get_booking(update)
        start_booking_date = booking.start_booking_date.replace(hour=time.hour, minute=time.minute)
        redis_service.update_booking_field(update, "start_booking_date", start_booking_date)
        LoggerService.info(__name__, f"select start time", update, kwargs={'start_time': start_booking_date.time()})
        return await finish_date_message(update, context)
    elif is_action:
        LoggerService.info(__name__, f"select start time", update, kwargs={'start_time': 'back'})
        return await start_date_message(update, context)
    return BOOKING

async def enter_finish_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    booking = redis_service.get_booking(update)
    max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = (booking.start_booking_date + timedelta(hours=MIN_BOOKING_HOURS)).date()
    selected, selected_date, is_action = await calendar_picker.process_calendar_selection(update, context, min_date=min_date_booking, max_date=max_date_booking, action_text="Назад", callback_prefix="-FINISH")
    if selected:
        redis_service.update_booking_field(update, "finish_booking_date", selected_date)
        LoggerService.info(__name__, f"select finish date", update, kwargs={'finish_date': selected_date.date()})
        return await finish_time_message(update, context)
    elif is_action:
        LoggerService.info(__name__, f"select finish date", update, kwargs={'finish_date': 'back'})
        return await start_time_message(update, context)
    return BOOKING

async def enter_finish_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    selected, time, is_action = await hours_picker.process_hours_selection(update, context)
    if selected:
        booking = redis_service.get_booking(update)
        finish_booking_date = booking.finish_booking_date.replace(hour=time.hour, minute=time.minute)
        redis_service.update_booking_field(update, "finish_booking_date", finish_booking_date)
        LoggerService.info(__name__, f"select finish time", update, kwargs={'finish_time': finish_booking_date.time()})

        if booking.tariff == Tariff.WORKER and tariff_helper.is_interval_in_allowed_ranges(booking.start_booking_date.time(), finish_booking_date.time()) == False:
            error_message = ("❌ <b>Ошибка!</b>\n\n"
                "⏳ <b>Выбранные дата и время не соответствуют условиям тарифа 'Рабочий'.</b>\n"
                "⚠️ В рамках этого тарифа бронирование возможно только с 11:00 до 20:00 или с 22:00 до 9:00.\n\n"
                "🔄 Пожалуйста, выберите другое время начала бронирования.\n\n"
                "ℹ️ Если вы планируете забронировать в другое время — выберите, пожалуйста, тариф '12 часов', 'Суточно' или 'Инкогнито'.")
            LoggerService.warning(__name__, f"incorect time for tariff Worker", update)
            return await start_date_message(update, context, error_message=error_message)

        is_any_booking = database_service.is_booking_between_dates(booking.start_booking_date - timedelta(hours=CLEANING_HOURS), finish_booking_date + timedelta(hours=CLEANING_HOURS))
        if is_any_booking:
            error_message = ("❌ <b>Ошибка!</b>\n\n"
                "⏳ <b>Выбранные дата и время недоступны.</b>\n"
                "⚠️ Дата начала и конца бронирования пересекается с другим бронированием.\n\n"
                "🔄 Пожалуйста, выберите новую дату начала бронирования.")
            LoggerService.warning(__name__, f"there are bookings between the selected dates", update)
            return await start_date_message(update, context, error_message=error_message)

        return await comment_message(update, context)
    elif is_action:
        LoggerService.info(__name__, f"select finish time", update, kwargs={'finish_time': "cancel"})
        return await finish_date_message(update, context)
    return BOOKING

async def write_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.COMMENT)

    if update.message == None:
        if update.callback_query:
            await update.callback_query.answer()
            data = string_helper.get_callback_data(update.callback_query.data)
            if (data == str(END)):
                return await back_navigation(update, context)
    else:
        booking_comment = update.message.text
        redis_service.update_booking_field(update, "booking_comment", booking_comment)
        LoggerService.info(__name__, f"Write comment", update, kwargs={'comment': booking_comment})

    return await confirm_pay(update, context)

async def confirm_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.CONFIRM_BOOKING)
    booking = redis_service.get_booking(update)
    
    keyboard = [
        [InlineKeyboardButton("Перейти к оплате.", callback_data=SET_USER)],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-BACK_{BACK}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    selected_duration = booking.finish_booking_date - booking.start_booking_date
    duration_booking_hours = round(date_time_helper.seconds_to_hours(int(selected_duration.total_seconds())))
    price = rate_service.calculate_price(booking.rental_rate, booking.is_sauna_included, booking.is_secret_room_included, booking.is_additional_bedroom_included, booking.is_photoshoot_included, booking.number_of_guests, duration_booking_hours)
    extra_hours = duration_booking_hours - booking.rental_rate.duration_hours
    categories = rate_service.get_price_categories(booking.rental_rate, booking.is_sauna_included, booking.is_secret_room_included, booking.is_additional_bedroom_included,booking.number_of_guests, extra_hours)
    photoshoot_text = ", фото сессия" if booking.is_photoshoot_included else ""

    LoggerService.info(__name__, f"Confirm pay", update, kwargs={'price': price})

    if booking.gift_id or booking.subscription_id:
        gift = database_service.get_gift_by_id(booking.gift_id)
        payed_price = gift.price if gift else booking.rental_rate.price
        price = int(price - payed_price)
        message = (
            f"💰 <b>Доплата: {price} руб.</b>\n\n"
            f"📌 <b>Что включено:</b> {categories}{photoshoot_text}\n"
            f"📅 <b>Заезд:</b> {booking.start_booking_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"📅 <b>Выезд:</b> {booking.finish_booking_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"💬 <b>Комментарий:</b> {booking.booking_comment if booking.booking_comment else ''}\n\n"
            "✅ <b>Подтвердите бронирование дома</b>")
    else:
        message = (
            f"💰 <b>Итоговая сумма:</b> {price} руб.\n\n"
            f"📌 <b>Включено:</b> {categories}{photoshoot_text}.\n"
            f"📅 <b>Заезд:</b> {booking.start_booking_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"📅 <b>Выезд:</b> {booking.finish_booking_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"💬 <b>Комментарий:</b> {booking.booking_comment if booking.booking_comment else ''}\n\n"
            "✅ <b>Подтвердить бронирование?</b>")

    if update.message == None:
        await update.callback_query.answer()
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
            reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup)

    redis_service.update_booking_field(update, "price", price)
    return BOOKING

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.PAY)
    booking = redis_service.get_booking(update)

    if update.callback_query and update.callback_query.data:
        await update.callback_query.answer()
        if (update.callback_query.data == str(END)):
            return await back_navigation(update, context)
    
    LoggerService.info(__name__, f"Pay", update)
    keyboard = [[InlineKeyboardButton("Отмена", callback_data=f"BOOKING-PAY_{END}")]]
    if booking.gift_id or booking.subscription_id:
        keyboard.append([InlineKeyboardButton("Оплата наличкой", callback_data=f"BOOKING-PAY_{CASH_PAY}")])
        message = (f"💰 <b>Сумма доплаты:</b> {booking.price} руб.\n\n"
            "📌 <b>Доступные способы оплаты (Альфа-Банк):</b>\n"
            f"📱 По номеру телефона: <b>{BANK_PHONE_NUMBER}</b>\n"
            f"💳 По номеру карты: <b>{BANK_CARD_NUMBER}</b>\n"
            "💵 Наличными при заселении.\n\n"
            "❗️ <b>Важно!</b>\n"
            "После оплаты отправьте скриншот или PDF документ с чеком.\n"
            "📩 Только так мы сможем подтвердить получение предоплаты.\n\n"
            "🙏 Спасибо за понимание!")
    else:
        message = (
            f"💰 <b>Общая сумма оплаты:</b> {booking.price} руб.\n\n"
            f"🔹 <b>Предоплата:</b> {PREPAYMENT} руб.\n"
            "💡 Предоплата не возвращается при отмене бронирования, но вы можете перенести бронь на другую дату.\n\n"
            "📌 <b>Способы оплаты (Альфа-Банк):</b>\n"
            f"📱 По номеру телефона: <b>{BANK_PHONE_NUMBER}</b>\n"
            f"💳 По номеру карты: <b>{BANK_CARD_NUMBER}</b>\n\n"
            "❗ <b>Важно!</b>\n"
            "После оплаты отправьте скриншот или PDF документ с чеком.\n"
            "📩 Это необходимо для подтверждения вашей предоплаты.\n\n"
            "🙏 Спасибо за понимание!")
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup)
    else:
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
            reply_markup=reply_markup)
    return BOOKING_PHOTO_UPLOAD

async def cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, f"Cancel booking", update)
    await update.callback_query.answer()

    booking = redis_service.get_booking(update)
    if booking:
        database_service.update_booking(booking.id, is_canceled=True)
    return await back_navigation(update, context)

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, f"Confirm booking", update)

    redis_service.update_booking_field(update, "navigation_step", BookingStep.FINISH)
    booking = redis_service.get_booking(update)

    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-BACK_{BACK}")]]
    message = (
        "✨ <b>Спасибо за доверие к The Secret House!</b> ✨\n"
        "📩 Мы скоро отправим вам сообщение с подтверждением бронирования.\n\n"
        f"📅 <b>Дата заезда:</b> {booking.start_booking_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"🏁 <b>Дата выезда:</b> {booking.finish_booking_date.strftime('%d.%m.%Y %H:%M')}\n\n"
        "🛎 <i>Если у вас есть вопросы, напишите нам — мы всегда на связи!</i>")
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message == None:
        await update.callback_query.answer()
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
            reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup)
    return BOOKING

async def photoshoot_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.PHOTOSHOOT)
    booking = redis_service.get_booking(update)

    keyboard = [
        [InlineKeyboardButton("Да", callback_data=f"BOOKING-PHOTO_{str(True)}")],
        [InlineKeyboardButton("Нет", callback_data=f"BOOKING-PHOTO_{str(False)}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-PHOTO_{END}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (f"📸 <b>Хотите заказать фотосессию?</b>\n"
        "✨ Она уже включена в стоимость выбранного тарифа!\n"
        "Фотосессия длится 2 часа.\n"
        "Instagram фотографа: https://www.instagram.com/eugenechulitskyphoto/\n\n"
        f"💰 <b>Стоимость:</b> {booking.rental_rate.photoshoot_price} руб.\n")
    if update.message == None:
        await update.callback_query.answer()
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
            reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup)
    return BOOKING

async def secret_room_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.SECRET_ROOM)
    booking = redis_service.get_booking(update)

    keyboard = [
        [InlineKeyboardButton("Да", callback_data=f"BOOKING-SECRET_{str(True)}")],
        [InlineKeyboardButton("Нет", callback_data=f"BOOKING-SECRET_{str(False)}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-SECRET_{END}")]]
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
            reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup)
    return BOOKING

async def write_code_message(update: Update, context: ContextTypes.DEFAULT_TYPE, is_error: bool = False):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.COMMENT)
    booking = redis_service.get_booking(update)

    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-CODE_{END}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_error:
        message = "❌ <b>Ошибка:</b> код введён некорректно или устарел.\n🔄 Пожалуйста, введите код ещё раз."
    elif booking.tariff == Tariff.GIFT:
        message = "🎁 <b>Введите проверочный код подарочного сертификата.</b>\n🔢 Длина кода — 15 символов."
    elif booking.tariff == Tariff.SUBSCRIPTION:
        message = "🎟 <b>Введите проверочный код абонемента.</b>\n🔢 Длина кода — 15 символов."

    if update.message == None:
        await update.callback_query.answer()
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
            reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup)
    return BOOKING_WRITE_CODE

async def count_of_people_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.NUMBER_GUESTS)
    booking = redis_service.get_booking(update)

    keyboard = [
        [InlineKeyboardButton("1 гость", callback_data="BOOKING-PEOPLE_1")],
        [InlineKeyboardButton("2 гостя", callback_data="BOOKING-PEOPLE_2")],
        [InlineKeyboardButton("3 гостя", callback_data="BOOKING-PEOPLE_3")],
        [InlineKeyboardButton("4 гостя", callback_data="BOOKING-PEOPLE_4")],
        [InlineKeyboardButton("5 гостей", callback_data="BOOKING-PEOPLE_5")],
        [InlineKeyboardButton("6 гостей", callback_data="BOOKING-PEOPLE_6")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-BACK_{BACK}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    additional_people_text = (
        f"💰 <b>Доплата за каждого дополнительного гостя:</b> {booking.rental_rate.extra_people_price} руб."
        if booking.rental_rate.max_people != MAX_PEOPLE else "")
    message = (
        "👥 <b>Сколько гостей будет присутствовать?</b>\n\n"
        f"📌 <b>Максимальное количество гостей для '{booking.rental_rate.name}':</b> {booking.rental_rate.max_people} чел.\n"
        f"{additional_people_text}")

    if update.message == None:
        await update.callback_query.answer()
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
            reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup) 
    return BOOKING

async def start_date_message(update: Update, context: ContextTypes.DEFAULT_TYPE, error_message: Optional[str] = None):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.START_DATE)

    if error_message:
        message = error_message
    else:
        message = ("📅 <b>Выберите дату начала бронирования.</b>\n"
                   "Укажите день, когда хотите заселиться в дом.")

    today = date.today()
    max_date_booking = today + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = today
    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text=message,
        reply_markup=calendar_picker.create_calendar(today, min_date=min_date_booking, max_date=max_date_booking, action_text="Назад в меню", callback_prefix="-START"))
    return BOOKING

async def start_time_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.START_TIME)
    booking = redis_service.get_booking(update)

    feature_booking = database_service.get_booking_by_day(booking.start_booking_date.date())
    available_slots = date_time_helper.get_free_time_slots(feature_booking, booking.start_booking_date.date(), minus_time_from_start=True, add_time_to_end=True)
    message = ("⏳ <b>Выберите время начала бронирования.</b>\n"
                f"Вы выбрали дату заезда: {booking.start_booking_date.strftime('%d.%m.%Y')}.\n"
                "Теперь укажите удобное время заезда.\n")
    if booking.tariff == Tariff.WORKER:
        message += (
            "\n📌 <b>Для тарифа 'Рабочий' доступны интервалы:</b>\n"
            "🕚 11:00 – 20:00\n"
            "🌙 22:00 – 09:00")
    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text=message,
        reply_markup=hours_picker.create_hours_picker(action_text="Назад", free_slots=available_slots, date=booking.start_booking_date.date(), callback_prefix="-START"))
    return BOOKING

async def finish_date_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.FINISH_DATE)
    booking = redis_service.get_booking(update)
    
    today = date.today()
    max_date_booking = today + relativedelta(months=PERIOD_IN_MONTHS)
    min_date_booking = (booking.start_booking_date + timedelta(hours=MIN_BOOKING_HOURS)).date()
    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="📅 <b>Выберите дату завершения бронирования.</b>\n"
            f"Вы выбрали дату и время заезда: {booking.start_booking_date.strftime('%d.%m.%Y %H:%M')}.\n"
            "Теперь укажите день, когда планируете выехать.\n"
            "📌 Выезд должен быть позже времени заезда.",
        reply_markup=calendar_picker.create_calendar(min_date_booking, min_date=min_date_booking, max_date=max_date_booking, action_text="Назад", callback_prefix="-FINISH"))
    return BOOKING

async def finish_time_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.FINISH_TIME)
    booking = redis_service.get_booking(update)

    feature_booking = database_service.get_booking_by_day(booking.finish_booking_date.date())
    start_time = time(0, 0) if booking.start_booking_date.date() != booking.finish_booking_date.date() else (booking.start_booking_date + timedelta(hours=MIN_BOOKING_HOURS)).time()
    available_slots = date_time_helper.get_free_time_slots(feature_booking, booking.finish_booking_date.date(), start_time=start_time, minus_time_from_start=True, add_time_to_end=True)
    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="⏳ <b>Выберите времня завершения бронирования.</b>\n"
            f"Вы выбрали заезд: {booking.start_booking_date.strftime('%d.%m.%Y %H:%M')}.\n"
            f"Вы выбрали дату выезда: {booking.finish_booking_date.strftime('%d.%m.%Y')}.\n"
            "Теперь укажите время, когда хотите освободить дом.\n\n"
            "📌 Обратите внимание:\n"
            "🔹 Выезд должен быть позже времени заезда.\n"
            f"🔹 После каждого бронирования требуется {CLEANING_HOURS} часа на уборку.\n",
        reply_markup=hours_picker.create_hours_picker(action_text="Назад", free_slots=available_slots, date=booking.finish_booking_date.date(), callback_prefix="-FINISH"))
    return BOOKING

async def sauna_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.SAUNA)
    booking = redis_service.get_booking(update)

    keyboard = [
        [InlineKeyboardButton("Да", callback_data=f"BOOKING-SAUNA_{str(True)}")],
        [InlineKeyboardButton("Нет", callback_data=f"BOOKING-SAUNA_{str(False)}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-SAUNA_{END}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "🧖‍♂️ <b>Хотите воспользоваться сауной?</b>\n\n"
        f"💰 <b>Стоимость:</b> {booking.rental_rate.sauna_price} руб.\n"
        f"📌 <b>Для тарифа:</b> {tariff_helper.get_name(booking.tariff)}")

    if update.message == None:
        await update.callback_query.answer()
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
            reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup)
    return BOOKING

async def comment_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.COMMENT)
    keyboard = [
        [InlineKeyboardButton("Пропустить", callback_data=f"BOOKING-COMMENT_{SKIP}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-COMMENT_{END}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="💬 <b>Хотите оставить комментарий?</b>\n"
            "Если у вас есть пожелания или дополнительная информация, напишите их здесь.", 
        reply_markup=reply_markup)
    return BOOKING_COMMENT

async def bedroom_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.FIRST_BEDROOM)
    keyboard = [
        [InlineKeyboardButton("🛏 Белая спальня", callback_data=f"BOOKING-BEDROOM_{Bedroom.WHITE.value}")],
        [InlineKeyboardButton("🌿 Зеленая спальня", callback_data=f"BOOKING-BEDROOM_{Bedroom.GREEN.value}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-BEDROOM_{END}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = "🛏 <b>Выберите спальную комнату:</b>"
    if update.message == None:
        await update.callback_query.answer()
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
            reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup)
    return BOOKING

async def additional_bedroom_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.SECOND_BEDROOM)
    booking = redis_service.get_booking(update)

    keyboard = [
        [InlineKeyboardButton("Да", callback_data=f"BOOKING-ADD-BEDROOM_{str(True)}")],
        [InlineKeyboardButton("Нет", callback_data=f"BOOKING-ADD-BEDROOM_{str(False)}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-ADD-BEDROOM_{END}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text = (
            "🛏 <b>Нужна ли вам вторая спальная комната?</b>\n\n"
            f"💰 <b>Стоимость:</b> {booking.rental_rate.second_bedroom_price} руб.\n"
            f"📌 <b>Для тарифа:</b> {tariff_helper.get_name(booking.tariff)}"),
        reply_markup=reply_markup)
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
    
    if booking.subscription_id:
        if booking.is_sauna_included:
            return True
        elif booking.number_of_guests > booking.rental_rate.max_people:
            return True

    return False
    
async def navigate_next_step_for_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    booking = redis_service.get_booking(update)
    if not booking.gift_id:
        return

    if booking.tariff == Tariff.DAY_FOR_COUPLE or booking.tariff == Tariff.INCOGNITA_DAY:
        return await photoshoot_message(update, context)
    elif booking.tariff == Tariff.INCOGNITA_HOURS or booking.tariff == Tariff.DAY:
        return await count_of_people_message(update, context)

    gift = database_service.get_gift_by_id(booking.gift_id)
    if booking.is_white_room_included == False and booking.is_green_room_included == False and gift.has_additional_bedroom == False:
        return await bedroom_message(update, context)
    elif booking.is_additional_bedroom_included == None:
        return await additional_bedroom_message(update, context)
    elif booking.is_secret_room_included == None:
        return await secret_room_message(update, context)
    elif booking.is_sauna_included == None:
        return await sauna_message(update, context)
    
    return await count_of_people_message(update, context)

async def navigate_next_step_for_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    booking = redis_service.get_booking(update)
    if not booking.subscription_id:
        return

    if booking.is_sauna_included == None:
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
        redis_service.update_booking_field(update, "is_additional_bedroom_included", True)
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

    categories = rate_service.get_price_categories(rental_rate, gift.has_sauna, gift.has_secret_room, gift.has_additional_bedroom)
    await update.message.reply_text(
        f"🎉 <b>Поздравляем!</b> Вы успешно активировали сертификат!\n\n"
        f"📜 <b>Содержимое сертификата:</b> {categories}",
        parse_mode='HTML')
    
    init_fields_for_gift(update)
    return await navigate_next_step_for_gift(update, context)

async def init_subscription_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return await write_code_message(update, context, True)
    
    subscription = database_service.get_subscription_by_code(update.message.text)
    if not subscription:
        return await write_code_message(update, context, True)

    redis_service.update_booking_field(update, "subscription_id", subscription.id)
    rental_rate = rate_service.get_by_subscription(subscription.subscription_type)
    redis_service.update_booking_field(update, "rental_rate", rental_rate)

    await update.message.reply_text(
        f"✅ <b>Отличные новости!</b> Мы нашли ваш тариф '<b>{rental_rate.name}</b>'!\n\n"
        f"📅 <b>Осталось посещений:</b> {subscription.subscription_type.value - subscription.number_of_visits} из {subscription.subscription_type.value}.",
        parse_mode='HTML')
    
    redis_service.update_booking_field(update, "is_secret_room_included", True)
    redis_service.update_booking_field(update, "is_additional_bedroom_included", True)
    redis_service.update_booking_field(update, "is_white_room_included", True)
    redis_service.update_booking_field(update, "is_green_room_included", True)
    return await navigate_next_step_for_subscription(update, context)

def save_booking_information(update: Update, chat_id: int, is_cash = False) -> BookingBase:
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
    #     booking.sale,
    #     booking.sale_comment,
    #     chat_id,
    #     booking.gift_id,
    #     booking.subscription_id)

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
        chat_id,
        cache_booking.gift_id,
        cache_booking.subscription_id)
    
    if is_cash:
        booking = database_service.update_booking(booking.id, prepayment=0)

    if booking == None:
        LoggerService.error(
            __name__, 
            f"Booking is None", 
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
            subscription_id=cache_booking.subscription_id)
        
    return booking

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document: Optional[Document] = None
    photo: Optional[str] = None
    if update.message and update.message.document and update.message.document.mime_type == 'application/pdf':
        document = update.message.document
    elif update.message and update.message.photo:
        photo = update.message.photo[-1].file_id

    LoggerService.info(__name__, f"handle photo", update)
    return await send_approving_to_admin(update, context, photo, document)

async def cash_pay_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await send_approving_to_admin(update, context, is_cash=True)

async def send_approving_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, photo = None, document = None, is_cash = False):
    chat_id = navigation_service.get_chat_id(update)
    booking = save_booking_information(update, chat_id, is_cash)
    if not booking and update.message:
        await update.message.reply_text(
            text="❌ <b>Ошибка!</b>\n\n"
                "Не удалось сохранить информацию о бронировании.\n"
                "Пожалуйста, попробуйте ещё раз или свяжитесь с администратором.\n"
                "Нажмите на синюю кнопку 'Меню' и выберите 'Открыть Главное меню'.\n\n"
                "🙏 Спасибо за понимание!",
            parse_mode='HTML')
        return BOOKING
    
    await admin_handler.accept_booking_payment(update, context, booking, chat_id, photo, document, is_cash)
    return await confirm_booking(update, context)
