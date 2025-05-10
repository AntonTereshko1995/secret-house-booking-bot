import sys
import os

from src.services.navigation_service import safe_edit_message_text
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.logger_service import LoggerService
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, CallbackQueryHandler, CallbackContext)
from src.handlers import menu_handler
from src.constants import END, MENU, PRICE

def get_handler():
    return [
        CallbackQueryHandler(back_navigation, pattern=f"^{END}$")
    ]

async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, f"Back to menu", update)
    await menu_handler.show_menu(update, context)
    return MENU

async def send_prices(update: Update, context: CallbackContext):
    LoggerService.info(__name__, f"send prices", update)
    tariffs = (
        "🏡 <b>ТАРИФ 'СУТОЧНЫЙ ОТ 3 ЧЕЛОВЕК'</b>\n"
        "✔ <b>1 день</b> — 700 BYN\n"
        "✔ <b>2 дня</b> — 1300 BYN\n"
        "✔ <b>3 дня</b> — 1800 BYN\n"
        "<b>Дополнительно:</b>\n"
        "➕ <b>Сауна</b> — 100 BYN\n"
        "➕ <b>Фотосессия</b> — 100 BYN\n"
        "➕ Дополнительный 1 час — 30 BYN\n"
        "<b>Условия:</b>\n"
        "🔹 Доступ к <b>Секретной комнате</b>\n"
        "🔹 Доступ к <b>двум спальням</b>\n"
        "🔹 Максимальное количество гостей — <b>6 человек</b>\n"
        "🔹 Свободный <b>выбор времени заезда</b>\n"
        "🎁 <b>Бонус:\n"
        "</b> При бронировании от 2 дней — дарим 12 часов в подарок при повторном бронировании!\n\n\n"

        "🏡 <b>ТАРИФ 'СУТОЧНЫЙ ДЛЯ ПАР'</b>\n"
        "✔ <b>1 день</b> — 500 BYN\n"
        "✔ <b>2 дня</b> — 900 BYN\n"
        "✔ <b>3 дня</b> — 1200 BYN\n"
        "<b>Дополнительно:</b>\n"
        "➕ <b>Сауна</b> — 100 BYN\n"
        "➕ <b>Фотосессия</b> — 100 BYN\n"
        "➕ Дополнительный 1 час — 30 BYN\n"
        "<b>Условия:</b>\n"
        "🔹 Доступ к <b>Секретной комнате</b>\n"
        "🔹 Доступ к <b>двум спальням</b>\n"
        "🔹 Максимальное количество гостей — <b>2 человека</b>\n"
        "🔹 Свободный <b>выбор времени заезда</b>\n"
        "🎁 <b>Бонус:\n"
        "</b> При бронировании от 2 дней — дарим 12 часов в подарок при повторном бронировании!\n\n\n"

        "⏳ <b>ТАРИФ '12 ЧАСОВ'</b>\n"
        "✔ <b>Одна спальня</b> — 250 BYN\n"
        "<b>Дополнительно:</b>\n"
        "➕ <b>Вторая спальня</b> — 70 BYN\n"
        "➕ <b>Секретная комната</b> — 70 BYN\n"
        "➕ <b>Сауна</b> — 100 BYN\n"
        "➕ Дополнительный 1 час — 30 BYN\n"
        "<b>Условия:</b>\n"
         "🔹 Включает <b>одну спальню на выбор</b>\n"
        "🔹 Максимальное количество гостей — <b>2 человека</b>\n"
        "🔹 Свободный <b>выбор времени заезда</b>\n\n\n"


        "💼 <b>ТАРИФ 'РАБОЧИЙ' (с понедельника по четверг)</b>\n"
        "✔ <b>Одна спальня</b> — 180 BYN\n"
        "<b>Дополнительно:</b>\n"
        "➕ Вторая спальня — 50 BYN\n"
        "➕ <b>Секретная комната</b> — 50 BYN\n"
        "➕ <b>Сауна</b> — 100 BYN\n"
        "➕ Дополнительный 1 час — 30 BYN\n"
        "<b>Условия:</b>\n"
         "🔹 Включает <b>одну спальню на выбор</b>\n"
        "🔹 Максимальное количество гостей — <b>2 человека</b>\n"
        "🔹 Бронирование доступно <b>в двух временных промежутках:</b>\n"
        "📌 <b>с 11:00 до 20:00</b>\n"
        "🌙 <b>с 22:00 до 09:00</b>\n\n\n"

        "🔥 <b>ТАРИФ 'ИНКОГНИТО'</b>\n"
        "✔ <b>Сутки</b> — 900 BYN\n"
        "✔ <b>12 часов</b> — 600 BYN\n"
        "🔹 Включает <b>весь дом</b>, <b>все комнаты</b>, <b>секретную комнату</b> и <b>сауну</b>\n"
        "🔹 <b>Без заключения договора</b>\n"
        "🔹 <b>Отключение внешних камер наблюдения по периметру дома</b>\n"
        "🎁 <b>Подарки:</b>\n"
        "🚘 <b>Трансфер</b> от/до дома на автомобиле бизнес-класса\n"
        "🍷 <b>Бутылка вина и лёгкие закуски</b>\n"
        "📸 <b>Бесплатная фотосессия</b> при аренде на сутки (2 часа, бронь за неделю)\n")
    
    keyboard = [[InlineKeyboardButton("Отмена", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await safe_edit_message_text(
            callback_query=update.callback_query,
            text=tariffs,
            reply_markup=reply_markup)
    return PRICE