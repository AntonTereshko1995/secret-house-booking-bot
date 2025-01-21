from src.models.enum.bedroom import Bedroom

def get_by_value(value: int) -> Bedroom:
    if (value == Bedroom.WHITE.value):
        return Bedroom.WHITE
    elif (value == Bedroom.GREEN.value):
        return Bedroom.GREEN

def get_by_str(value_str: str) -> Bedroom:
    value = int(value_str)
    return get_by_value(value)