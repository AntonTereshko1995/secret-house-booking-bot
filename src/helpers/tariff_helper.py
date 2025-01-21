from src.models.enum.tariff import Tariff

def get_name(tariff: Tariff) -> str:
    if (tariff == Tariff.DAY):
        return "Суточно"
    elif (tariff == Tariff.HOURS_12):
        return "12 часов"
    elif (tariff == Tariff.WORKER):
        return "Рабочий"
    elif (tariff == Tariff.INCOGNITA_DAY):
        return "Инкогнито на 12 часов"
    elif (tariff == Tariff.INCOGNITA_HOURS):
        return "Инкогнито на сутки"
    elif (tariff == Tariff.SUBSCRIPTION):
        return "Абонемент на сутки"

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

def get_by_str(value_str: str) -> Tariff:
    value = int(value_str)
    return get_by_value(value)