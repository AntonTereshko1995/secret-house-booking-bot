from enum import Enum


class PromocodeType(Enum):
    """Type of promocode application"""
    BOOKING_DATES = 1  # Бронирование на конкретные даты
    USAGE_PERIOD = 2   # Действие промокода в период, бронирование на любую дату
