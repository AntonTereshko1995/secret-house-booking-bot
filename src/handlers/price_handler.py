import sys
import os
from src.services.navigation_service import NavigationService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.logger_service import LoggerService
from src.services.calculation_rate_service import CalculationRateService
from src.models.enum.tariff import Tariff
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CallbackContext
from src.handlers import menu_handler
from src.constants import END, MENU, PRICE

navigation_service = NavigationService()


def get_handler():
    return [CallbackQueryHandler(back_navigation, pattern=f"^{END}$")]


async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, "Back to menu", update)
    await menu_handler.show_menu(update, context)
    return MENU


async def send_prices(update: Update, context: CallbackContext):
    LoggerService.info(__name__, "send prices", update)

    calculation_service = CalculationRateService()
    calculation_service.refresh()

    # Get tariff data for each tariff type
    day_tariff = calculation_service.get_by_tariff(Tariff.DAY)
    couple_tariff = calculation_service.get_by_tariff(Tariff.DAY_FOR_COUPLE)
    hours_12_tariff = calculation_service.get_by_tariff(Tariff.HOURS_12)
    worker_tariff = calculation_service.get_by_tariff(Tariff.WORKER)
    incognita_day_tariff = calculation_service.get_by_tariff(Tariff.INCOGNITA_DAY)
    incognita_hours_tariff = calculation_service.get_by_tariff(Tariff.INCOGNITA_HOURS)
    incognita_worker_tariff = calculation_service.get_by_tariff(Tariff.INCOGNITA_WORKER)

    tariffs = (
        f"🔥 <b>ТАРИФ 'ИНКОГНИТО'</b>\n"
        f"✔ <b>Сутки</b> — {incognita_day_tariff.price} BYN\n"
        f"✔ <b>12 часов</b> — {incognita_hours_tariff.price} BYN\n"
        f"✔ <b>Рабочий</b> — {incognita_worker_tariff.price} BYN\n"
        "🔹 Включает <b>весь дом</b>, <b>все комнаты</b>, <b>секретную комнату</b> и <b>сауну</b>\n"
        "🔹 <b>Без заключения договора</b>\n"
        "🔹 <b>Отключение внешних камер наблюдения по периметру дома</b>\n"
        "<b>Дополнительно:</b>\n"
        f"➕ <b>Банный чан</b> — {incognita_day_tariff.bath_tub_price} BYN\n"
        "🎁 <b>Подарки:</b>\n"
        "🚘 <b>Трансфер</b> от/до дома на автомобиле бизнес-класса\n"
        "🍷 <b>Бутылка вина и лёгкие закуски</b>\n"
        "📸 <b>Бесплатная фотосессия</b> при аренде на сутки (2 часа, бронь за неделю)\n\n\n"
        f"🏡 <b>ТАРИФ 'СУТОЧНЫЙ ОТ 3 ЧЕЛОВЕК'</b>\n"
        f"✔ <b>1 день</b> — {day_tariff.multi_day_prices.get('1', day_tariff.price)} BYN\n"
        f"✔ <b>2 дня</b> — {day_tariff.multi_day_prices.get('2', day_tariff.price * 2)} BYN\n"
        f"✔ <b>3 дня</b> — {day_tariff.multi_day_prices.get('3', day_tariff.price * 3)} BYN\n"
        "<b>Дополнительно:</b>\n"
        f"➕ <b>Сауна</b> — {day_tariff.sauna_price} BYN\n"
        f"➕ <b>Банный чан</b> — {day_tariff.bath_tub_price} BYN\n"
        f"➕ <b>Фотосессия</b> — {day_tariff.photoshoot_price} BYN\n"
        f"➕ Дополнительный 1 час — {day_tariff.extra_hour_price} BYN\n"
        "<b>Условия:</b>\n"
        "🔹 Доступ к <b>Секретной комнате</b>\n"
        "🔹 Доступ к <b>двум спальням</b>\n"
        f"🔹 Максимальное количество гостей — <b>{day_tariff.max_people} человек</b>\n"
        "🔹 Свободный <b>выбор времени заезда</b>\n"
        "🎁 <b>Бонус:\n"
        "</b> При бронировании от 2 дней — дарим 12 часов в подарок при повторном бронировании!\n\n\n"
        f"🏡 <b>ТАРИФ 'СУТОЧНЫЙ ДЛЯ ПАР'</b>\n"
        f"✔ <b>1 день</b> — {couple_tariff.multi_day_prices.get('1', couple_tariff.price)} BYN\n"
        f"✔ <b>2 дня</b> — {couple_tariff.multi_day_prices.get('2', couple_tariff.price * 2)} BYN\n"
        f"✔ <b>3 дня</b> — {couple_tariff.multi_day_prices.get('3', couple_tariff.price * 3)} BYN\n"
        "<b>Дополнительно:</b>\n"
        f"➕ <b>Сауна</b> — {couple_tariff.sauna_price} BYN\n"
        f"➕ <b>Банный чан</b> — {couple_tariff.bath_tub_price} BYN\n"
        f"➕ <b>Фотосессия</b> — {couple_tariff.photoshoot_price} BYN\n"
        f"➕ Дополнительный 1 час — {couple_tariff.extra_hour_price} BYN\n"
        "<b>Условия:</b>\n"
        "🔹 Доступ к <b>Секретной комнате</b>\n"
        "🔹 Доступ к <b>двум спальням</b>\n"
        f"🔹 Максимальное количество гостей — <b>{couple_tariff.max_people} человека</b>\n"
        "🔹 Свободный <b>выбор времени заезда</b>\n"
        "🎁 <b>Бонус:\n"
        "</b> При бронировании от 2 дней — дарим 12 часов в подарок при повторном бронировании!\n\n\n"
        f"⏳ <b>ТАРИФ '12 ЧАСОВ'</b>\n"
        f"✔ <b>Одна спальня</b> — {hours_12_tariff.price} BYN\n"
        "<b>Дополнительно:</b>\n"
        f"➕ <b>Вторая спальня</b> — {hours_12_tariff.second_bedroom_price} BYN\n"
        f"➕ <b>Секретная комната</b> — {hours_12_tariff.secret_room_price} BYN\n"
        f"➕ <b>Сауна</b> — {hours_12_tariff.sauna_price} BYN\n"
        f"➕ <b>Банный чан</b> — {hours_12_tariff.bath_tub_price} BYN\n"
        f"➕ Дополнительный 1 час — {hours_12_tariff.extra_hour_price} BYN\n"
        "<b>Условия:</b>\n"
        "🔹 Включает <b>одну спальню на выбор</b>\n"
        f"🔹 Максимальное количество гостей — <b>{hours_12_tariff.max_people} человека</b>\n"
        "🔹 Свободный <b>выбор времени заезда</b>\n\n\n"
        f"💼 <b>ТАРИФ 'РАБОЧИЙ' (с понедельника по четверг)</b>\n"
        f"✔ <b>Одна спальня</b> — {worker_tariff.price} BYN\n"
        "<b>Дополнительно:</b>\n"
        f"➕ Вторая спальня — {worker_tariff.second_bedroom_price} BYN\n"
        f"➕ <b>Секретная комната</b> — {worker_tariff.secret_room_price} BYN\n"
        f"➕ <b>Сауна</b> — {worker_tariff.sauna_price} BYN\n"
        f"➕ <b>Банный чан</b> — {worker_tariff.bath_tub_price} BYN\n"
        f"➕ Дополнительный 1 час — {worker_tariff.extra_hour_price} BYN\n"
        "<b>Условия:</b>\n"
        "🔹 Включает <b>одну спальню на выбор</b>\n"
        f"🔹 Максимальное количество гостей — <b>{worker_tariff.max_people} человека</b>\n"
        "🔹 Бронирование доступно <b>в двух временных промежутках:</b>\n"
        "📌 <b>с 11:00 до 20:00</b>\n"
        "🌙 <b>с 22:00 до 09:00</b>\n\n\n"
    )

    keyboard = [[InlineKeyboardButton("Отмена", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query, text=tariffs, reply_markup=reply_markup
    )
    return PRICE
