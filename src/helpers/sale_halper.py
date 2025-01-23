from src.models.enum.sale import Sale

def get_name(sale: Sale) -> str:
    if (sale == Sale.FROM_FEEDBACK):
        return "Ранее бронировал(а) и заполнил(а) форму обратно связи"
    elif (sale == Sale.RECOMMENDATION_FROM_FRIEND):
        return "По рекомендации от друга."
    elif (sale == Sale.OTHER):
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

def get_percentage_sale(sale: Sale) -> int:
    if (sale == Sale.FROM_FEEDBACK):
        return 10
    elif (sale == Sale.RECOMMENDATION_FROM_FRIEND):
        return 5
    elif (sale == Sale.OTHER):
        return 10
    return 0