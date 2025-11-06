import re
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.models.gift import GiftBase
from db.models.booking import BookingBase
from db.models.user import UserBase
from src.helpers import tariff_helper
from datetime import timedelta
from random import choice
from string import ascii_uppercase
from src.config.config import CLEANING_HOURS


def is_valid_user_contact(user_name: str) -> tuple[bool, str]:
    """
    Validate and clean user contact (Telegram username or phone number).

    Returns:
        tuple[bool, str]: (is_valid, cleaned_contact)
    """
    # Remove spaces and newlines
    cleaned = user_name.replace(" ", "")

    if "\n" in cleaned:
        return False, user_name

    # Telegram username validation
    if cleaned.startswith("@"):
        pattern = r"^@[A-Za-z0-9_]{5,32}$"
        is_valid = bool(re.match(pattern, cleaned))
        return is_valid, cleaned

    # Phone number validation and cleaning
    # Remove formatting characters: -, (, )
    cleaned_phone = cleaned.replace("-", "").replace("(", "").replace(")", "")

    # Check if valid Belarus phone number (+375XXXXXXXXX = 13 chars)
    is_valid = cleaned_phone.startswith("+375") and len(cleaned_phone) == 13

    return is_valid, cleaned_phone


def separate_callback_data(data):
    return data.split("_")


def get_callback_data(data):
    return data.split("_")[-1]


def convert_hours_to_time_string(hour: int) -> str:
    if 0 <= hour <= 23:
        return f"{hour:02}:00"
    else:
        raise ValueError("Hour must be between 0 and 23.")


def get_generated_code() -> str:
    return "".join(choice(ascii_uppercase) for i in range(15))


def bool_to_str(value: bool) -> str:
    return "Да" if value else "Нет"


def generate_available_slots(
    bookings,
    from_datetime,
    to_datetime,
    cleaning_time=timedelta(hours=CLEANING_HOURS),
    time_step=timedelta(hours=1),
):
    if len(bookings) == 0:
        return "Весь месяц свободен."

    all_slots = []
    current_time = from_datetime

    while current_time < to_datetime:
        all_slots.append(current_time)
        current_time += time_step

    extended_busy_slots = [
        {
            "start": booking.start_date - cleaning_time,
            "end": booking.end_date + cleaning_time,
        }
        for booking in bookings
    ]

    available_slots = [
        slot
        for slot in all_slots
        if all(
            not (busy["start"] <= slot < busy["end"]) for busy in extended_busy_slots
        )
    ]

    grouped_slots = {}
    for slot in available_slots:
        date_str = slot.strftime("%d-%m")
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
                    time_ranges.append(
                        f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
                    )
                start_time = times[i]

        end_time = times[-1]
        if start_time == end_time:
            time_ranges.append(start_time.strftime("%H:%M"))
        else:
            end_str = (
                "23:59"
                if end_time.hour == 23 and end_time.minute == 0
                else end_time.strftime("%H:%M")
            )
            time_ranges.append(f"{start_time.strftime('%H:%M')} - {end_str}")

        message += f"📍 <b>{date}</b>\n{', '.join(time_ranges)}\n\n"

    return message


def generate_booking_info_message(
    booking: BookingBase,
    user: UserBase,
    is_additional_payment_by_cash=False,
) -> str:
    message = (
        f"Пользователь: {user.contact}\n"
        f"Дата начала: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"Дата завершения: {booking.end_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"Тариф: {tariff_helper.get_name(booking.tariff)}\n"
        f"Стоимость: {booking.price} руб.\n"
        f"Фотосессия: {bool_to_str(booking.has_photoshoot)}\n"
        f"Сауна: {bool_to_str(booking.has_sauna)}\n"
        f"Белая спальня: {bool_to_str(booking.has_white_bedroom)}\n"
        f"Зеленая спальня: {bool_to_str(booking.has_green_bedroom)}\n"
        f"Секретная комната: {bool_to_str(booking.has_secret_room)}\n"
        f"Количество гостей: {booking.number_of_guests}\n"
        f"Комментарий: {booking.comment if booking.comment else ''}\n"
        f"Всего бронирований: {user.total_bookings}\n"
        f"Завершенных бронирований: {user.completed_bookings}\n"
    )

    # Add incognito questionnaire info for incognito tariffs
    from src.models.enum.tariff import Tariff

    is_incognito = booking.tariff in (
        Tariff.INCOGNITA_DAY,
        Tariff.INCOGNITA_HOURS,
        Tariff.INCOGNITA_WORKER,
    )

    if is_incognito:
        wine_labels = {
            "none": "Не нужно вино",
            "white-sweet": "Белое сладкое",
            "white-semi-sweet": "Белое полусладкое",
            "white-dry": "Белое сухое",
            "white-semi-dry": "Белое полусухое",
            "red-sweet": "Красное сладкое",
            "red-semi-sweet": "Красное полусладкое",
            "red-dry": "Красное сухое",
            "red-semi-dry": "Красное полусухое",
        }
        wine_text = (
            wine_labels.get(booking.wine_preference, booking.wine_preference)
            if booking.wine_preference
            else "Не указано"
        )
        message += f"🍷 Вино: {wine_text}\n"

        transfer_text = (
            booking.transfer_address if booking.transfer_address else "Не нужно"
        )
        message += f"🚗 Трансфер: {transfer_text}\n"
        
        # Add transfer time information if transfer is requested
        if booking.transfer_address:
            # Transfer time is 30 minutes before check-in time
            from datetime import timedelta
            transfer_time = booking.start_date - timedelta(minutes=30)
            message += f"🕐 Время трансфера: {transfer_time.strftime('%d.%m.%Y %H:%M')}\n"

    if booking.gift_id:
        message += (
            f"Подарочный сертификат: Да\n"
            f"Подарочный сертификат: {booking.gift_id}\n"
            f"Доплата наличкой: {bool_to_str(is_additional_payment_by_cash)}\n"
        )
    else:
        message += f"Предоплата: {booking.prepayment_price}\n"
    return message


def generate_gift_info_message(gift: GiftBase) -> str:
    return (
        f"Подарочный сертификат!\n"
        f"Покупатель: {gift.buyer_contact}\n"
        f"Дата окончания: {gift.date_expired.strftime('%d.%m.%Y %H:%M')}\n"
        f"Тариф: {tariff_helper.get_name(gift.tariff)}\n"
        f"Стоимость: {gift.price} руб.\n"
        f"Сауна: {bool_to_str(gift.has_sauna)}\n"
        f"Дополнительная спальня: {bool_to_str(gift.has_additional_bedroom)}\n"
        f"Секретная комната: {bool_to_str(gift.has_secret_room)}\n"
        f"Код: {gift.code}\n"
    )


def parse_booking_callback_data(callback_data: str):
    pattern = r"booking_(\d+)_chatid_(\d+)_bookingid_(\d+)_cash_(True|False)"
    match = re.match(pattern, callback_data)
    if match:
        menu_index = match.group(1)
        user_chat_id = match.group(2)
        booking_id = match.group(3)
        is_payment_by_cash = match.group(4)
        return {
            "user_chat_id": user_chat_id,
            "booking_id": booking_id,
            "menu_index": menu_index,
            "is_payment_by_cash": is_payment_by_cash,
        }
    else:
        return None


def parse_change_price_callback_data(callback_data: str, pattern: str):
    match = re.match(pattern, callback_data)
    if match:
        price = match.group(1)
        user_chat_id = match.group(2)
        booking_id = match.group(3)
        is_payment_by_cash = match.group(4)
        return {
            "user_chat_id": user_chat_id,
            "booking_id": booking_id,
            "price": price,
            "is_payment_by_cash": is_payment_by_cash,
        }
    else:
        return None


def parse_gift_callback_data(callback_data: str):
    pattern = r"gift_(\d+)_chatid_(\d+)_giftid_(\d+)"
    match = re.match(pattern, callback_data)
    if match:
        menu_index = match.group(1)
        user_chat_id = match.group(2)
        gift_id = match.group(3)
        return {
            "user_chat_id": user_chat_id,
            "gift_id": gift_id,
            "menu_index": menu_index,
        }
    else:
        return None
