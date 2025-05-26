from datetime import date, time
from src.models.enum.tariff import Tariff

def get_name(tariff: Tariff) -> str:
    if (tariff == Tariff.DAY):
        return "Суточно от 3 человек"
    elif (tariff == Tariff.DAY_FOR_COUPLE):
        return "Суточно для двоих"
    elif (tariff == Tariff.HOURS_12):
        return "12 часов"
    elif (tariff == Tariff.WORKER):
        return "Рабочий"
    elif (tariff == Tariff.INCOGNITA_DAY):
        return "Инкогнито на сутки"
    elif (tariff == Tariff.INCOGNITA_HOURS):
        return "Инкогнито на 12 часов"
    elif (tariff == Tariff.SUBSCRIPTION):
        return "Абонемент"
    elif (tariff == Tariff.GIFT):
        return "Подарочный сертификат"

def get_by_value(value: int) -> Tariff:
    if (value == Tariff.DAY.value):
        return Tariff.DAY
    elif (value == Tariff.DAY_FOR_COUPLE.value):
        return Tariff.DAY_FOR_COUPLE
    elif (value == Tariff.HOURS_12.value):
        return Tariff.HOURS_12
    elif (value == Tariff.WORKER.value):
        return Tariff.WORKER
    elif (value == Tariff.INCOGNITA_HOURS.value):
        return Tariff.INCOGNITA_HOURS
    elif (value == Tariff.INCOGNITA_DAY.value):
        return Tariff.INCOGNITA_DAY
    elif (value == Tariff.SUBSCRIPTION.value):
        return Tariff.SUBSCRIPTION    
    elif (value == Tariff.GIFT.value):
        return Tariff.GIFT 

def get_by_str(value_str: str) -> Tariff:
    # TODO exception
    value = int(value_str) 
    return get_by_value(value)

def is_booking_available(tariff: Tariff, start_date: date) -> bool:
    if tariff != Tariff.WORKER:
        return True
    
    if start_date.weekday() == 4 or start_date.weekday() == 5 or start_date.weekday() == 6:
        return False
    
    return True

def is_interval_in_allowed_ranges(check_start: time, check_end: time) -> bool:
    daytime_start = time(11, 0)
    daytime_end = time(20, 0)

    night_start = time(22, 0)
    night_end = time(9, 0)

    def is_in_range(start: time, end: time, range_start: time, range_end: time) -> bool:
        if range_start <= range_end:
            return range_start <= start and end <= range_end
        else:
            return (start >= range_start or start <= range_end) and (end >= range_start or end <= range_end)

    return (
        is_in_range(check_start, check_end, daytime_start, daytime_end)
        or
        is_in_range(check_start, check_end, night_start, night_end)
    )