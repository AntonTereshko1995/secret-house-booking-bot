import sys
import os
from datetime import datetime
from src.models.enum.subscription_type import SubscriptionType
from src.models.enum.tariff import Tariff
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class RentalPrice:
    tariff: Tariff
    name: str
    duration_hours: int
    price: int
    sauna_price: int
    secret_room_price: int
    second_bedroom_price: int
    extra_hour_price: int
    max_people: int
    is_check_in_time_limit: bool
    is_photoshoot: bool
    is_transfer: bool
    subscription_type: SubscriptionType
    # def __init__(
    #         self, 
    #         tariff: Tariff, 
    #         name: str,
    #         duration_hours: int,
    #         price: int,
    #         sauna_price: int,
    #         secret_room_price: int,
    #         second_bedroom_price: int,
    #         extra_hour_price: int,
    #         max_people: int,
    #         is_check_in_time_limit: bool,
    #         is_photoshoot: bool,
    #         is_transfer: bool,
    #         subscription_type: SubscriptionType):
    #     self.tariff = tariff
    #     self.name = name
    #     self.duration_hours = duration_hours
    #     self.price = price
    #     self.sauna_price = sauna_price
    #     self.secret_room_price = secret_room_price
    #     self.second_bedroom_price = second_bedroom_price
    #     self.second_bedroom_price = second_bedroom_price
    #     self.extra_hour_price = extra_hour_price
    #     self.max_people = max_people
    #     self.is_check_in_time_limit = is_check_in_time_limit
    #     self.is_photoshoot = is_photoshoot
    #     self.is_transfer = is_transfer
    #     self.subscription_type = subscription_type