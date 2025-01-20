from src.models.enum.subscription_type import SubscriptionType

def get_name(tariff: SubscriptionType) -> str:
    if (tariff == SubscriptionType.VISITS_3):
        return "3 посещения"
    elif (tariff == SubscriptionType.VISITS_5):
        return "5 посещений"
    elif (tariff == SubscriptionType.VISITS_8):
        return "8 посещений"

def get_by_value(value: int) -> SubscriptionType:
    if (value == SubscriptionType.VISITS_3.value):
        return SubscriptionType.VISITS_3
    elif (value == SubscriptionType.VISITS_5.value):
        return SubscriptionType.VISITS_5
    elif (value == SubscriptionType.VISITS_8.value):
        return SubscriptionType.VISITS_8

def get_by_str(value_str: str) -> SubscriptionType:
    value = int(value_str)
    return get_by_value(value)