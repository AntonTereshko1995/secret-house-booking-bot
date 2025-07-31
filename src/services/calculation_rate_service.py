import sys
import os
from src.models.enum.subscription_type import SubscriptionType
from src.models.enum.tariff import Tariff
from src.models.rental_price import RentalPrice
from src.services.file_service import FileService
from typing import List
from singleton_decorator import singleton
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@singleton
class CalculationRateService:
    _rates = List[RentalPrice]

    def get_by_tariff(self, tariff: Tariff) -> RentalPrice:
        if tariff == Tariff.SUBSCRIPTION or tariff == Tariff.GIFT:
            return None
        
        tariffs = self._try_load_tariffs()
        selected_tariff = next((rate for rate in tariffs if rate.tariff == tariff.value), None)
        if selected_tariff is None:
            raise ValueError(f"No RentalPrice found for tariff: {tariff}")
        return selected_tariff
    
    def get_by_subscription(self, subscription_type: SubscriptionType) -> RentalPrice:
        tariffs = self._try_load_tariffs()
        selected_subscription = next((tariff for tariff in tariffs if tariff.subscription_type == subscription_type.value), None)
        if selected_subscription is None:
            raise ValueError(f"No RentalPrice found for subscription type: {subscription_type}")
        return selected_subscription

    def get_price(self, tariff: Tariff = None, subscription_type: SubscriptionType = None) -> int:
        tariffs = self._try_load_tariffs()
        if tariff is not None:
            price = next((rate.price for rate in tariffs if rate.tariff == tariff.value), None)
            if price is None:
                raise ValueError(f"No price found for tariff: {tariff}")
            return price

        if subscription_type != None:
            return next((tariff.price for tariff in tariffs if tariff.subscription_type == subscription_type.value), None)

        return 0

    def calculate_price(
            self,
            rental_price: RentalPrice, 
            is_sauna: bool, 
            is_secret_room: bool, 
            is_second_room: bool,
            is_photoshoot: bool = False,
            count_people: int = 0,
            duration_hours: int = 0) -> int:
        price = 0
        extra_hours = duration_hours - rental_price.duration_hours
        if extra_hours > 0:
            if rental_price.tariff in [Tariff.DAY.value, Tariff.DAY_FOR_COUPLE.value, Tariff.INCOGNITA_DAY.value]:
                total_days = duration_hours // 24
                remainder_hours = duration_hours % 24

                if remainder_hours > 15 and remainder_hours < 24:
                    total_days += 1
                    remainder_hours = 0

                if str(total_days) in rental_price.multi_day_prices:
                    price += rental_price.multi_day_prices[str(total_days)]

                if remainder_hours > 0:
                    price += remainder_hours * rental_price.extra_hour_price
            else:
                price = rental_price.price
                price += extra_hours * rental_price.extra_hour_price
        else:
            price = rental_price.price

        if is_sauna and rental_price.sauna_price > 0:
            price += rental_price.sauna_price
        if is_secret_room and rental_price.secret_room_price > 0:
            price += rental_price.secret_room_price
        if is_second_room and rental_price.second_bedroom_price > 0:
            price += rental_price.second_bedroom_price
        if is_photoshoot:
            price += rental_price.photoshoot_price
        if count_people > rental_price.max_people:
            price += (count_people - rental_price.max_people) * rental_price.extra_people_price

        
        return price
    
    def get_price_categories(
            self,
            rental_price: RentalPrice, 
            is_sauna: bool, 
            is_secret_room: bool, 
            is_second_room: bool,
            count_people: int = 0,
            extra_hours: int = 0) -> str:
        categories = f"{rental_price.name}, спальная комната"
        if is_sauna:
            categories += f", сауна"
        if is_secret_room:
            categories += f", секретная комната"
        if is_second_room:
            categories += f", дополнительная спальная комната"
        if count_people > rental_price.max_people:
            additional_people = count_people - rental_price.max_people
            categories += f", дополнительно {additional_people} чел."
        if extra_hours > 0:
            categories += f", дополнительное время {extra_hours} ч."

        return categories

    def _try_load_tariffs(self) -> List[RentalPrice]:
        if not self._rates:
            return self._rates
        
        file_service = FileService()
        self._rates = file_service.get_tariff_rates()
        return self._rates