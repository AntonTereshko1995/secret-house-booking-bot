import re
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.models.gift import GiftBase
from db.models.booking import BookingBase
from db.models.user import UserBase
from src.helpers import tariff_helper
from datetime import datetime, time, timedelta
from random import choice
from string import ascii_uppercase
from src.config.config import CLEANING_HOURS, CLEANING_HOURS_BATH_TUB, MIN_BOOKING_HOURS


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

    # Build extended busy intervals (booking ± cleaning), sort and merge overlapping ones
    raw_busy = sorted(
        (
            booking.start_date - (timedelta(hours=CLEANING_HOURS_BATH_TUB) if getattr(booking, "has_bath_tub", False) else cleaning_time),
            booking.end_date + (timedelta(hours=CLEANING_HOURS_BATH_TUB) if getattr(booking, "has_bath_tub", False) else cleaning_time),
        )
        for booking in bookings
    )
    merged_busy: list[list] = []
    for start, end in raw_busy:
        if not merged_busy or start > merged_busy[-1][1]:
            merged_busy.append([start, end])
        else:
            merged_busy[-1][1] = max(merged_busy[-1][1], end)

    # Iterate day by day; free windows are exact gaps between busy intervals
    message = ""
    current_day = from_datetime.date()
    last_day = (to_datetime - timedelta(days=1)).date()

    while current_day <= last_day:
        day_start = datetime.combine(current_day, time(0, 0))
        day_end = datetime.combine(current_day, time(23, 59))
        window_start = max(day_start, from_datetime) if current_day == from_datetime.date() else day_start

        free_windows = _compute_free_windows(window_start, day_end, merged_busy)
        if free_windows:
            date_str = current_day.strftime("%d-%m")
            ranges = [_format_window(ws, we) for ws, we in free_windows]
            message += f"📍 <b>{date_str}</b>\n{', '.join(ranges)}\n\n"

        current_day += timedelta(days=1)

    return message


def _compute_free_windows(
    day_start: datetime,
    day_end: datetime,
    merged_busy: list,
) -> list:
    """Return list of (start, end) free windows within [day_start, day_end]."""
    free = []
    cursor = day_start
    for bstart, bend in merged_busy:
        if bend <= cursor:
            continue
        if bstart >= day_end:
            break
        if cursor < bstart:
            free.append((cursor, min(bstart, day_end)))
        cursor = max(cursor, bend)
    if cursor < day_end:
        free.append((cursor, day_end))
    return free


def _format_window(start: datetime, end: datetime) -> str:
    end_str = "23:59" if end.hour == 23 else end.strftime("%H:%M")
    return f"{start.strftime('%H:%M')} - {end_str}"


def generate_booking_info_message(
    booking: BookingBase,
    user: UserBase,
    is_additional_payment_by_cash=False,
) -> str:
    # Handle case when user is None
    # For web bookings user.contact lacks '@'; user_name was set from data.telegram (with '@')
    # For bot bookings user.contact is what the user typed; user_name is their Telegram account name
    if booking.source == "web":
        raw_contact = (user.user_name or user.contact) if user else None
    else:
        raw_contact = user.contact if user else None
    user_contact = raw_contact if raw_contact else "N/A"
    user_total_bookings = user.total_bookings if user else 0
    user_completed_bookings = user.completed_bookings if user else 0
    
    source_label = "🌐 Веб" if booking.source == "web" else "📱 Телеграм"
    message = (
        f"Пользователь: {user_contact}\n"
        f"Дата начала: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"Дата завершения: {booking.end_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"Тариф: {tariff_helper.get_name(booking.tariff)}\n"
        f"Стоимость: {booking.price} руб.\n"
        f"Количество гостей: {booking.number_of_guests}\n"
        f"Всего бронирований: {user_total_bookings}\n"
        f"Завершенных бронирований: {user_completed_bookings}\n"
    )

    if booking.has_photoshoot:
        message += "Фотосессия: Да\n"
    if booking.has_sauna:
        message += "Сауна: Да\n"
    if booking.has_bath_tub:
        message += "Банный чан: Да\n"
    if booking.has_white_bedroom:
        message += "Белая спальня: Да\n"
    if booking.has_green_bedroom:
        message += "Зеленая спальня: Да\n"
    if booking.has_secret_room:
        message += "Секретная комната: Да\n"

    if booking.wine_preference and booking.wine_preference != "none":
        wine_labels = {
            "white-sweet": "Белое сладкое",
            "white-semi-sweet": "Белое полусладкое",
            "white-dry": "Белое сухое",
            "white-semi-dry": "Белое полусухое",
            "red-sweet": "Красное сладкое",
            "red-semi-sweet": "Красное полусладкое",
            "red-dry": "Красное сухое",
            "red-semi-dry": "Красное полусухое",
        }
        wine_text = wine_labels.get(booking.wine_preference, booking.wine_preference)
        message += f"Вино: {wine_text}\n"

    if booking.transfer_address:
        message += f"Трансфер: {booking.transfer_address}\n"
        from datetime import timedelta
        transfer_time = booking.start_date - timedelta(minutes=30)
        message += f"🕐 Время трансфера: {transfer_time.strftime('%d.%m.%Y %H:%M')}\n"

    if booking.comment:
        message += f"Комментарий: {booking.comment}\n"

    # Add promocode info if used
    if booking.promocode_id:
        from src.services.database_service import DatabaseService
        database_service = DatabaseService()
        promocode = database_service.get_promocode_by_id(booking.promocode_id)
        if promocode:
            message += f"Промокод: {promocode.name} (-{promocode.discount_percentage}%)\n"

    if booking.gift_id:
        message += (
            f"Подарочный сертификат: Да\n"
            f"Подарочный сертификат: {booking.gift_id}\n"
            f"Доплата наличкой: {bool_to_str(is_additional_payment_by_cash)}\n"
        )
    else:
        message += f"Предоплата: {booking.prepayment_price}\n"
    message += f"Источник: {source_label}\n"
    return message


def generate_gift_info_message(gift: GiftBase) -> str:
    return (
        f"Подарочный сертификат!\n"
        f"Покупатель: {gift.buyer_contact}\n"
        f"Дата окончания: {gift.date_expired.strftime('%d.%m.%Y %H:%M')}\n"
        f"Тариф: {tariff_helper.get_name(gift.tariff)}\n"
        f"Стоимость: {gift.price} руб.\n"
        f"Сауна: {bool_to_str(gift.has_sauna)}\n"
        f"Банный чан: {bool_to_str(gift.has_bath_tub)}\n"
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


def parse_manage_booking_callback(data: str) -> dict:
    """Parse callback data from booking management buttons

    Formats:
      - MBL: Back to list
      - MBD_{booking_id}: View detail
      - MBA_{action}_{booking_id}: Action
      - MBT_{tariff}_{booking_id}: Tariff selection
      - MBB_{booking_id}: Back to detail
    """
    parts = data.split("_")

    if data == "MBL":
        return {"type": "list"}
    elif parts[0] == "MBD":
        return {"type": "detail", "booking_id": int(parts[1])}
    elif parts[0] == "MBA":
        return {"type": "action", "action": parts[1], "booking_id": int(parts[2])}
    elif parts[0] == "MBT":
        return {"type": "tariff_select", "tariff": int(parts[1]), "booking_id": int(parts[2])}
    elif parts[0] == "MBB":
        return {"type": "back_detail", "booking_id": int(parts[1])}
    else:
        raise ValueError(f"Unknown callback format: {data}")


def format_booking_button_label(booking: BookingBase) -> str:
    """Format booking for button label: 'DD.MM.YYYY HH:MM'"""
    return booking.start_date.strftime("%d.%m.%Y %H:%M")
