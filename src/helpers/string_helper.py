def is_valid_user_name(text: str) -> bool:
    return (text.startswith("+375") and len(text) == 13) or text.startswith("@")

def is_valid_user_name(text: str):
    return (text.startswith("+375") and len(text) == 13) or text.startswith("@")