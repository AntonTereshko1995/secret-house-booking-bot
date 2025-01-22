import sys
import os
from datetime import datetime
from src.models.enum.subscription_type import SubscriptionType
from src.models.enum.tariff import Tariff
from src.models.rental_price import RentalPrice
from src.services import file_service
from typing import List
from singleton_decorator import singleton
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@singleton
class CalculationRateService:
    _rates = List[RentalPrice]

    def get_tariff(self, tariff: Tariff) -> RentalPrice:
        rates = self._get_tariffs()
        selected_tariff = next((rate for rate in rates if rate.tariff == tariff), None)
        return selected_tariff
    
    def get_subscription(self, subscription_type: SubscriptionType) -> RentalPrice:
        tariffs = self._get_tariffs()
        selected_subscription = next((tariff for tariff in tariffs if tariff.subscription_type == subscription_type), None)
        return selected_subscription

    def _get_tariffs(self) -> List[RentalPrice]:
        if len(self._rates) != 0:
            return self._rates
        self._rates = file_service.get_tariff_rates()
        return self._rates