def is_valid_user_name(text: str):
    return text.startswith("+375") or text.startswith("@")