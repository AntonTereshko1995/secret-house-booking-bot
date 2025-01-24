import sys
import os
from matplotlib.dates import relativedelta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.date_time_picker import calendar_picker, hours_picker
from src.services.database_service import DatabaseService
from src.config.config import PERIOD_IN_MONTHS
from src.models.rental_price import RentalPrice
from src.services.calculation_rate_service import CalculationRateService
from datetime import date, datetime
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters)
from src.handlers import menu_handler
from src.helpers import string_helper, string_helper, tariff_helper, sale_halper, bedroom_halper
from src.models.enum.sale import Sale
from src.models.enum.bedroom import Bedroom
from src.models.enum.tariff import Tariff
from src.constants import (
    BACK, 
    END,
    MENU, 
    STOPPING, 
    BOOKING,
    SET_USER,
    SELECT_TARIFF,
    INCLUDE_SAUNA,
    VALIDATE_USER, 
    INCLUDE_PHOTOSHOOT,
    INCLUDE_SECRET_ROOM,
    SELECT_BEDROOM, 
    ADDITIONAL_BEDROOM,
    NUMBER_OF_PEOPLE,
    COMMENT,
    SALE,
    PAY,
    SKIP,
    WRITE_CODE,
    SET_START_DATE, 
    SET_START_TIME, 
    SET_FINISH_DATE,
    SET_FINISH_TIME,
    CONFIRM_PAY,
    CONFIRM)

MAX_PEOPLE = 6

user_contact: str
tariff: Tariff
is_sauna_included = False
is_secret_room_included = False
is_photoshoot_included = False
is_white_room_included = False
is_green_room_included = False
comment: str
sale: Sale
customer_sale_comment: str
number_of_customers: int
start_booking_date: datetime
finish_booking_date: datetime
rate_service = CalculationRateService()
database_service = DatabaseService()
rental_rate: RentalPrice
price: int

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(generate_tariff_menu, pattern=f"^{str(BOOKING)}$")],
        states={
            SET_USER: [CallbackQueryHandler(enter_user_contact)],
            VALIDATE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_user_contact)],
            SELECT_TARIFF: [CallbackQueryHandler(select_tariff)],
            INCLUDE_PHOTOSHOOT: [CallbackQueryHandler(include_photoshoot)],
            INCLUDE_SECRET_ROOM: [CallbackQueryHandler(include_secret_room)],
            INCLUDE_SAUNA: [CallbackQueryHandler(include_sauna)],
            SELECT_BEDROOM: [CallbackQueryHandler(select_bedroom)],
            ADDITIONAL_BEDROOM: [CallbackQueryHandler(select_additional_bedroom)],
            NUMBER_OF_PEOPLE: [CallbackQueryHandler(select_number_of_people)],
            SET_START_DATE: [CallbackQueryHandler(enter_start_date)], 
            SET_START_TIME: [CallbackQueryHandler(enter_start_time)], 
            SET_FINISH_DATE: [CallbackQueryHandler(enter_finish_date)], 
            SET_FINISH_TIME: [CallbackQueryHandler(enter_finish_time)],
            WRITE_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, write_secret_code)],
            COMMENT: [
                CallbackQueryHandler(write_comment),
                MessageHandler(filters.TEXT & ~filters.COMMAND, write_comment)],
            SALE: [
                CallbackQueryHandler(select_sale),
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_sale)],
            PAY: [CallbackQueryHandler(pay)],
            CONFIRM_PAY: [CallbackQueryHandler(confirm_pay)],
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

async def generate_tariff_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        [InlineKeyboardButton(
            tariff_helper.get_name(Tariff.SUBSCRIPTION), 
            callback_data=f"{Tariff.SUBSCRIPTION.value}")],
        [InlineKeyboardButton(
            tariff_helper.get_name(Tariff.GIFT), 
            callback_data=f"{Tariff.GIFT.value}")],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Выберете тариф для бронирования.\n",
        reply_markup=reply_markup)
    return SELECT_TARIFF   

async def select_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = update.callback_query.data
    if (data == str(END)):
        return await back_navigation(update, context)

    global tariff, rental_rate, is_sauna_included, is_secret_room_included, is_secret_room_included, is_white_room_included, is_green_room_included
    tariff = tariff_helper.get_by_str(data)
    rental_rate  = rate_service.get_tariff(tariff)

    if tariff == Tariff.DAY or tariff == Tariff.INCOGNITA_DAY:
        is_sauna_included = True
        is_secret_room_included = True
        is_white_room_included = True
        is_green_room_included = True
        return await photoshoot_message(update, context)
    elif tariff == Tariff.HOURS_12 or tariff == Tariff.WORKER:
        return await bedroom_message(update, context)
    elif tariff == Tariff.GIFT or tariff == Tariff.SUBSCRIPTION:
        return await write_code_message(update, context)
    elif tariff == Tariff.INCOGNITA_HOURS:
        return await count_of_people_message(update, context)

async def enter_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "Напишите Ваш <b>Telegram</b>.\nФормат ввода @user_name (обязательно начинайте ввод с @).\nФормат ввода номера телефона +375251111111 (обязательно начинайте ввод с +375).\n"

    if (update.message == None):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            text=message,
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
            return await confirm_pay(update)
        else:
            await update.message.reply_text("Ошибка: имя пользователя в Telegram или номер телефона введены не коректно.\n"
                                            "Повторите ввод еще раз.")
    else:
        await update.message.reply_text("Ошибка: Пустая строка.\n"
                                        "Повторите ввод еще раз.")

    return VALIDATE_USER

async def include_photoshoot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    if (update.callback_query.data == str(END)):
        return await back_navigation(update, context)

    global is_photoshoot_included
    is_photoshoot_included = eval(update.callback_query.data)
    return await count_of_people_message(update, context)

async def include_sauna(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    if (update.callback_query.data == str(END)):
        return await back_navigation(update, context)

    data = update.callback_query.data
    if (data == str(END)):
        return await back_navigation(update, context)

    global is_sauna_included
    is_sauna_included = eval(update.callback_query.data)
    return await count_of_people_message(update, context)

async def include_secret_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = update.callback_query.data
    if (data == str(END)):
        return await back_navigation(update, context)

    global is_secret_room_included
    is_secret_room_included = eval(data)

    return await sauna_message(update, context)

async def select_bedroom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    if (update.callback_query.data == str(END)):
        return await back_navigation(update, context)

    bedroom = bedroom_halper.get_by_str(update.callback_query.data)

    if (bedroom == Bedroom.GREEN):
        global is_green_room_included
        is_green_room_included = True
    else:
        global is_white_room_included
        is_white_room_included = True

    return await additional_bedroom_message(update, context)

async def select_additional_bedroom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    if (update.callback_query.data == str(END)):
        return await back_navigation(update, context)

    is_added = eval(update.callback_query.data)
    if is_added:
        global is_green_room_included, is_white_room_included
        if is_green_room_included:
            is_white_room_included = True
        else:
            is_green_room_included = True

    return await secret_room_message(update, context)

async def select_number_of_people(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    if (update.callback_query.data == str(END)):
        return await back_navigation(update, context)

    global number_of_customers
    number_of_customers = int(update.callback_query.data)
    return await start_date_message(update, context)

async def write_secret_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global tariff, rental_rate, is_sauna_included, is_secret_room_included, is_secret_room_included, is_white_room_included, is_green_room_included
# JXVGPDSBOYLAELJ
    gift = database_service.get_gift_by_code(update.message.text)
    if not gift:
        return await write_code_message(update, context, True)

    global tariff
    tariff = gift.tariff
    if tariff == Tariff.DAY or tariff == Tariff.INCOGNITA_DAY:
        is_sauna_included = True
        is_secret_room_included = True
        is_white_room_included = True
        is_green_room_included = True
        return await photoshoot_message(update, context)
    elif tariff == Tariff.HOURS_12 or tariff == Tariff.WORKER:
        return await secret_room_message(update, context)
    elif tariff == Tariff.GIFT or tariff == Tariff.SUBSCRIPTION:
        return await write_code_message(update, context)
    elif tariff == Tariff.INCOGNITA_HOURS:
        return await count_of_people_message(update, context)

async def enter_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
    selected, selected_date, is_action = await calendar_picker.process_calendar_selection(update, context, max_date=max_date_booking, action_text="Назад в меню")
    if selected:
        global new_booking_date
        new_booking_date = selected_date
        return await start_time_message(update, context)
    elif is_action:
        return await back_navigation(update, context)
    return SET_START_DATE

async def enter_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    selected, time, is_action = await hours_picker.process_hours_selection(update, context)
    if selected:
        global new_booking_date
        new_booking_date = new_booking_date.replace(hour=time.hour)
        return await finish_date_message(update, context)
    elif is_action:
        return await back_navigation(update, context)
    return SET_START_TIME

async def enter_finish_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
    selected, selected_date, is_action = await calendar_picker.process_calendar_selection(update, context, max_date=max_date_booking, action_text="Назад в меню")
    if selected:
        global finish_booking_date
        finish_booking_date = selected_date
        return await finish_time_message(update, context)
    elif is_action:
        return await back_navigation(update, context)
    return SET_FINISH_DATE

async def enter_finish_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    selected, time, is_action = await hours_picker.process_hours_selection(update, context)
    if selected:
        global finish_booking_date
        finish_booking_date = finish_booking_date.replace(hour=time.hour)
        return await comment_message(update, context)
    elif is_action:
        return await back_navigation(update, context)
    return SET_FINISH_TIME

async def write_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message == None:
        await update.callback_query.answer()
        if (update.callback_query.data == str(END)):
            return await back_navigation(update, context)
        return await sale_message(update, context)

    global comment
    comment = update.message.text
    return await sale_message(update, context)

async def select_sale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (update.callback_query.data == str(END)):
        await update.callback_query.answer()
        return await back_navigation(update, context)
    
    global sale

    if update.message == None:
        await update.callback_query.answer()
        data = update.callback_query.data
        if (data == str(END)):
            return await back_navigation(update, context)
        
        sale = sale_halper.get_by_str(data)
        return await enter_user_contact(update, context)

    sale = Sale.OTHER
    global customer_sale_comment
    customer_sale_comment = update.message.text
    return await enter_user_contact(update, context)

async def confirm_pay(update: Update):
    keyboard = [
        [InlineKeyboardButton("Перейти к оплате.", callback_data=PAY)],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    global price
    is_additional_bedroom_included = is_white_room_included and is_white_room_included
    price = rate_service.calculate_price(rental_rate, is_sauna_included, is_secret_room_included, is_additional_bedroom_included, number_of_customers, sale)
    categories = rate_service.get_price_categories(rental_rate, is_sauna_included, is_secret_room_included, is_additional_bedroom_included, number_of_customers)
    photoshoot_text = ", фото сессия" if is_photoshoot_included else ""
    await update.message.reply_text(
    text=f"Общая сумма оплаты {price} руб.\n"
        f"В стоимость входит: {categories}{photoshoot_text}.\n"
        "\n"
        "Подтверждаете покупку бронирования дома?\n",
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

    sale_text = "Скидка применена." if sale != Sale.NONE else ""
    await update.callback_query.edit_message_text(
    text=f"Общая сумма оплаты {price} руб. {sale_text}\n"
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

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Спасибо Вам за доверие к The Secret House.\n"
            "Скоро мы отправим Вам сообщение с подтверждением о бронировании.\n",
        reply_markup=reply_markup)
    return MENU

async def photoshoot_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("Да", callback_data=str(True))],
        [InlineKeyboardButton("Нет", callback_data=str(False))],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text="Нужна ли Вам фото сессия?\n"
            f"Входит в стоимость для выбранного тарифа.",
    reply_markup=reply_markup)
    return INCLUDE_PHOTOSHOOT

async def secret_room_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    
    keyboard = [
        [InlineKeyboardButton("Да", callback_data=str(True))],
        [InlineKeyboardButton("Нет", callback_data=str(False))],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text="Планируете ли Вы пользоваться 'Секретной комнатой'?\n"
            f"Стоимость {rental_rate.secret_room_price} руб для тарифа '{tariff_helper.get_name(tariff)}'.",
    reply_markup=reply_markup)
    return INCLUDE_SECRET_ROOM

async def write_code_message(update: Update, context: ContextTypes.DEFAULT_TYPE, is_error: bool = False):
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_error:
        message = "Ошибка: код введет не правильно или код устарел.\n"
        "Введите код еще раз."
    elif tariff == Tariff.GIFT:
        message = "Введите проверочный код от подарочного сертификата. Длинна кода 15 символов."
    elif tariff == Tariff.SUBSCRIPTION:
        message = "Введите проверочный код от абонемента. Длинна кода 15 символов."

    if update.message:
        await update.message.reply_text(
            text=message, 
            reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(
            text=message, 
            reply_markup=reply_markup)
    return WRITE_CODE

async def count_of_people_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1 гость", callback_data=str(1))],
        [InlineKeyboardButton("2 гостя", callback_data=str(2))],
        [InlineKeyboardButton("3 гостя", callback_data=str(3))],
        [InlineKeyboardButton("4 гостя", callback_data=str(4))],
        [InlineKeyboardButton("5 гостей", callback_data=str(5))],
        [InlineKeyboardButton("6 гостей", callback_data=str(6))],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    additional_people_text = "" if rental_rate.max_people == MAX_PEOPLE else f"Дополнительная оплата за челоаека {rental_rate.extra_people_price} руб."
    await update.callback_query.edit_message_text(
        text="Какое колличество гостей будет присуствовать?\n"
            f"Для {rental_rate.name} максимальное колличество гостей {rental_rate.max_people} чел.\n"
            f"{additional_people_text}", 
        reply_markup=reply_markup)
    return NUMBER_OF_PEOPLE

async def start_time_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        text="Выберете время заезда.\n", 
        reply_markup = hours_picker.create_hours_picker(action_text="Назад в меню"))
    return SET_START_TIME

async def finish_date_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = date.today()
    max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
    await update.callback_query.edit_message_text(
        text="Выберете дату завершения бронирования.\n", 
        reply_markup=calendar_picker.create_calendar(today.year, today.month, max_date=max_date_booking, action_text="Назад в меню"))
    return SET_FINISH_DATE

async def finish_time_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        text="Выберете время заезда.\n", 
        reply_markup=hours_picker.create_hours_picker())
    return SET_FINISH_TIME

async def start_date_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = date.today()
    max_date_booking = date.today() + relativedelta(months=PERIOD_IN_MONTHS)
    await update.callback_query.edit_message_text(
        text="Нашли Ваше бронирование.\n"
            "Введите дату на которую Вы хотите перенести бронирование.\n", 
        reply_markup=calendar_picker.create_calendar(today.year, today.month, max_date=max_date_booking, action_text="Назад в меню"))
    return SET_START_DATE

async def sauna_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Да", callback_data=str(True))],
        [InlineKeyboardButton("Нет", callback_data=str(False))],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
    text="Планируете ли Вы пользоваться сауной?\n"
        f"Стоимость {rental_rate.sauna_price} руб для тарифа '{tariff_helper.get_name(tariff)}'.",
    reply_markup=reply_markup)
    return INCLUDE_SAUNA

async def comment_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Пропустить", callback_data=str(SKIP))],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        text=f"Введите комментарий:", 
        reply_markup=reply_markup)
    return COMMENT

async def sale_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(sale_halper.get_name(Sale.RECOMMENDATION_FROM_FRIEND), callback_data=Sale.RECOMMENDATION_FROM_FRIEND.value)],
        [InlineKeyboardButton(sale_halper.get_name(Sale.FROM_FEEDBACK), callback_data=Sale.FROM_FEEDBACK.value)],
        [InlineKeyboardButton("Пропустить", callback_data=Sale.NONE.value)],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "Выберете скидку или введите вручную:"

    if (update.message == None):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=message, 
            reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            text=message, 
            reply_markup=reply_markup)
    return SALE

async def bedroom_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Белая спальная комната", callback_data=Bedroom.WHITE.value)],
        [InlineKeyboardButton("Зеленая спальная комната", callback_data=Bedroom.GREEN.value)],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Выберете спальную комнату.", 
        reply_markup=reply_markup)
    return SELECT_BEDROOM

async def additional_bedroom_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Да", callback_data=str(True))],
        [InlineKeyboardButton("Нет", callback_data=str(False))],
        [InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="Нужна ли Вам вторая спальная комната?\n"
            f"Стоимость {rental_rate.second_bedroom_price} руб для тарифа '{tariff_helper.get_name(tariff)}'.",
        reply_markup=reply_markup)
    return ADDITIONAL_BEDROOM