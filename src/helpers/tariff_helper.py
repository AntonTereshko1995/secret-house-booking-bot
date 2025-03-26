from datetime import date
from src.models.enum.tariff import Tariff

def get_name(tariff: Tariff) -> str:
    if (tariff == Tariff.DAY):
        return "Суточно"
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
    lol = start_date.weekday()
    if start_date.weekday() == 4 or start_date.weekday() == 5 or start_date.weekday() == 6:
        return False
    
    return True