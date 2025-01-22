from src.models.enum.sale import Sale

def get_name(tariff: Sale) -> str:
    if (tariff == Sale.FROM_FEEDBACK):
        return "Ранее бронировал(а) и заполнил(а) форму обратно связи"
    elif (tariff == Sale.RECOMMENDATION_FROM_FRIEND):
        return "По рекомендации от друга."
    elif (tariff == Sale.OTHER):
        return "Другое"

def get_by_value(value: int) -> Sale:
    if (value == Sale.NONE.value):
        return Sale.NONE
    elif (value == Sale.FROM_FEEDBACK.value):
        return Sale.FROM_FEEDBACK
    elif (value == Sale.RECOMMENDATION_FROM_FRIEND.value):
        return Sale.RECOMMENDATION_FROM_FRIEND
    elif (value == Sale.OTHER.value):
        return Sale.OTHER

def get_by_str(value_str: str) -> Sale:
    value = int(value_str)
    return get_by_value(value)