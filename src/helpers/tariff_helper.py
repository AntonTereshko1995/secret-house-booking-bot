from src.models.enum.tariff import Tariff

def get_name(tariff: Tariff) -> str:
    if (tariff == Tariff.DAY):
        return "Суточно"
    elif (tariff == Tariff.HOURS_12):
        return "12 часов"
    elif (tariff == Tariff.WORKER):
        return "Рабочий"
    elif (tariff == Tariff.INCOGNITA):
        return "Инкогнито"
    elif (tariff == Tariff.SUBSCRIPTION):
        return "Абонемент"

def get_by_value(value: int) -> Tariff:
    if (value == Tariff.DAY.value):
        return Tariff.DAY
    elif (value == Tariff.HOURS_12.value):
        return Tariff.HOURS_12
    elif (value == Tariff.WORKER.value):
        return Tariff.WORKER
    elif (value == Tariff.INCOGNITA.value):
        return Tariff.INCOGNITA
    elif (value == Tariff.SUBSCRIPTION.value):
        return Tariff.SUBSCRIPTION    

def get_by_str(value_str: str) -> Tariff:
    value = int(value_str)
    return get_by_value(value)