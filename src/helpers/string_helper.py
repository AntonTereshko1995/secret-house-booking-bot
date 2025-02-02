from random import choice
from string import ascii_uppercase

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
