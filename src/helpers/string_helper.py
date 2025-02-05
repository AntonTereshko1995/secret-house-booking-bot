import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.models.booking import BookingBase
from db.models.user import UserBase
from src.helpers import tariff_helper
from datetime import timedelta
from random import choice
from string import ascii_uppercase
from src.config.config import CLEANING_HOURS

def is_valid_user_contact(text: str) -> bool:
    return (text.startswith("+375") and len(text) == 13) or (text.startswith("@") and len(text) > 1)

def extract_data(text):
    return int(text.split("_")[1])

def separate_callback_data(data):
    return data.split("_")

def convert_hours_to_time_string(hour: int) -> str:
    if 0 <= hour <= 23:
        return f"{hour:02}:00"
    else:
        raise ValueError("Hour must be between 0 and 23.")
    
def get_generated_code() -> str:
    return ''.join(choice(ascii_uppercase) for i in range(15))

def bool_to_str(value: bool) -> str:
    return "Да" if bool else "Нет"

def generate_available_slots(bookings, from_datetime, to_datetime, cleaning_time=timedelta(hours=CLEANING_HOURS), time_step=timedelta(hours=1)):
    if (len(bookings) == 0):
        return "Весь месяц свободен."

    all_slots = []
    current_time = from_datetime

    while current_time < to_datetime:
        all_slots.append(current_time)
        current_time += time_step

    extended_busy_slots = [
        {"start": booking.start_date - cleaning_time, "end": booking.end_date + cleaning_time}
        for booking in bookings
    ]

    available_slots = [
        slot for slot in all_slots
        if all(not (busy["start"] <= slot < busy["end"]) for busy in extended_busy_slots)]

    grouped_slots = {}
    for slot in available_slots:
        date_str = slot.strftime("%Y-%m-%d")
        if date_str not in grouped_slots:
            grouped_slots[date_str] = []
        grouped_slots[date_str].append(slot)

    message = ""
    for date, times in grouped_slots.items():
        time_ranges = []
        start_time = times[0]

        for i in range(1, len(times)):
            if (times[i] - times[i - 1]) > time_step:
                end_time = times[i - 1]
                if start_time == end_time:
                    time_ranges.append(start_time.strftime("%H:%M"))
                else:
                    time_ranges.append(f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}")
                start_time = times[i]

        end_time = times[-1]
        if start_time == end_time:
            time_ranges.append(start_time.strftime("%H:%M"))
        else:
            time_ranges.append(f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}")

        message += f"📍 <b>{date}</b>\n{', '.join(time_ranges)}\n\n"

    return message

def generate_info_message(booking: BookingBase, user: UserBase) -> str:
    return (f"Новое бронирование!\n"
            f"Пользователь: {user.contact}\n"
            f"Дата начала: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"Дата завершения: {booking.end_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"Тариф: {tariff_helper.get_name(booking.tariff)}\n"
            f"Стоимость: {booking.price} руб.\n"
            f"Фотосессия: {bool_to_str(booking.has_photoshoot)}\n"
            f"Сауна: {bool_to_str(booking.has_sauna)}\n"
            f"Белая спальня: {bool_to_str(booking.has_white_bedroom)}\n"
            f"Зеленая спальня: {bool_to_str(booking.has_green_bedroom)}\n"
            f"Секретная комната спальня: {bool_to_str(booking.has_secret_room)}\n"
            f"Колличество гостей: {booking.number_of_guests}\n"
            f"Комментарий: {booking.comment}\n"
            f"Подарочный сертификат: {booking.gift_id}\n"
            f"Абонемент: {booking.subscription_id}\n"
            f"Скидка: {booking.sale}\n"
            f"Скидка коммент: {booking.sale_comment}\n")