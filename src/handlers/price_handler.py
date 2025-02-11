import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (ContextTypes, ConversationHandler, CallbackQueryHandler, CallbackContext)
from src.handlers import menu_handler
from src.services.file_service import FileService
from src.constants import END, MENU, PRICE, STOPPING

def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(send_prices, pattern=f"^{str(PRICE)}$")],
        states={ },
        fallbacks=[CallbackQueryHandler(back_navigation, pattern=f"^{END}$")],
        map_to_parent={
            END: MENU,
            STOPPING: END,
        })
    return handler

async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_handler.show_menu(update, context)
    return END

async def send_prices(update: Update, context: CallbackContext):
    tariffs = (
            "🏡 <b>ТАРИФ 'СУТОЧНЫЙ'</b>\n"
            "✔ <b>1 день</b> — 750 BYN\n"
            "✔ <b>2 дня</b> — 1400 BYN\n"
            "✔ <b>3 дня</b> — 2050 BYN\n"
            "🎁 <b>Бонус:</b> При бронировании от 2 дней — дарим 12 часов в подарок при повторном бронировании!\n\n"
            "🔹 Включает <b>весь дом</b>:\n"
            "✅ Доступ к <b>двум спальням</b>\n"
            "✅ <b>Секретная комната</b>\n"
            "✅ <b>Сауна</b>\n"
            "✅ Просторная <b>гостиная</b> с камином\n"
            "✅ Полностью <b>оборудованная кухня</b>\n\n"
            "💡 <b>Преимущества:</b>\n"
            "🔹 Максимальное количество гостей — <b>6 человек</b>\n"
            "🔹 Свободный <b>выбор времени заезда</b>\n"
            "📸 <b>Бесплатная фотосессия</b> при первом бронировании (2 часа, бронь за неделю)\n\n\n\n"

            "⏳ <b>ТАРИФ '12 ЧАСОВ'</b>\n"
            "✔ <b>Одна спальня</b> — 300 BYN\n"
            "✔ <b>Дополнительно:</b>\n"
            "➕ Вторая спальня — 70 BYN\n"
            "➕ <b>Секретная комната</b> — 70 BYN\n"
            "➕ <b>Сауна</b> — 70 BYN\n"
            "➕ Дополнительный 1 час — 40 BYN\n\n"
            "🔹 <b>Максимальное количество гостей</b> — 3 человека\n"
            "🔹 Свободный <b>выбор времени заезда</b>\n\n"
            "💡 <b>Идеально для краткосрочного отдыха в особенной атмосфере</b>\n\n\n\n"

            "💼 <b>ТАРИФ 'РАБОЧИЙ' (с понедельника по четверг)</b>\n"
            "✔ <b>Одна спальня</b> — 200 BYN\n"
            "✔ <b>Дополнительно:</b>\n"
            "➕ Вторая спальня — 50 BYN\n"
            "➕ <b>Секретная комната</b> — 50 BYN\n"
            "➕ <b>Сауна</b> — 70 BYN\n"
            "➕ Дополнительный 1 час — 40 BYN\n\n"
            "🔹 Включает <b>одну спальню на выбор</b>\n"
            "🔹 Максимальное количество гостей — <b>2 человека</b>\n"
            "🔹 Бронирование доступно <b>в двух временных промежутках:</b>\n"
            "📌 <b>с 11:00 до 20:00</b>\n"
            "🌙 <b>с 22:00 до 09:00</b>\n\n"
            "💡 <b>Отличный вариант для дневного отдыха или ночного релакса!</b>\n\n\n\n"

            "🔥 <b>ТАРИФ 'ИНКОГНИТО' (VIP-опция)</b>\n"
            "✔ <b>Сутки</b> — 1000 BYN\n"
            "✔ <b>12 часов</b> — 650 BYN\n\n"
            "🔹 Включает <b>весь дом</b>, <b>все комнаты</b>, <b>секретную комнату</b> и <b>сауну</b>\n"
            "🔹 <b>Без заключения договора</b>\n"
            "🔹 <b>Отключение внешних камер наблюдения по периметру дома</b>\n\n"
            "🎁 <b>Подарки:</b>\n"
            "🚘 <b>Трансфер</b> от/до дома на автомобиле бизнес-класса\n"
            "🍷 <b>Бутылка вина и лёгкие закуски</b>\n"
            "📸 <b>Бесплатная фотосессия</b> при аренде на сутки (2 часа, бронь за неделю)\n\n"
            "💡 <b>Идеально для приватного отдыха без компромиссов</b>")
    
    keyboard = [[InlineKeyboardButton("Отмена", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=tariffs,
        parse_mode='HTML',
        reply_markup=reply_markup)
    return MENU

