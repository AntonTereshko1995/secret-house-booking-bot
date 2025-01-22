def is_valid_user_contact(text: str) -> bool:
    return (text.startswith("+375") and len(text) == 13) or (text.startswith("@") and len(text) > 1)

def extract_data(text):
    return int(text.split("_")[1])