import sys
import os
from datetime import date
from src.models.enum.tariff import Tariff
from src.models.rental_price import RentalPrice
from src.services.file_service import FileService
from src.services.date_pricing_service import DatePricingService
from typing import List
from singleton_decorator import singleton
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@singleton
class CalculationRateService:
    _rates: List[RentalPrice] = []

    def get_by_tariff(self, tariff: Tariff) -> RentalPrice:
        if tariff == Tariff.GIFT:
            return None
        
        tariffs = self._try_load_tariffs()
        selected_tariff = next((rate for rate in tariffs if rate.tariff == tariff.value), None)
        if selected_tariff is None:
            raise ValueError(f"No RentalPrice found for tariff: {tariff}")
        return selected_tariff
    

    def get_price(self, tariff: Tariff = None) -> int:
        tariffs = self._try_load_tariffs()
        if tariff is not None:
            price = next((rate.price for rate in tariffs if rate.tariff == tariff.value), None)
            if price is None:
                raise ValueError(f"No price found for tariff: {tariff}")
            return price

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
            categories += ", сауна"
        if is_secret_room:
            categories += ", секретная комната"
        if is_second_room:
            categories += ", дополнительная спальная комната"
        if count_people > rental_price.max_people:
            additional_people = count_people - rental_price.max_people
            categories += f", дополнительно {additional_people} чел."
        if extra_hours > 0:
            categories += f", дополнительное время {extra_hours} ч."

        return categories

    def _try_load_tariffs(self) -> List[RentalPrice]:
        if not self._rates:
            file_service = FileService()
            self._rates = file_service.get_tariff_rates()
        return self._rates

    # Date-aware pricing methods

    def get_effective_price_for_date(
        self,
        booking_date: date,
        tariff: Tariff,
        duration_hours: int
    ) -> int:
        """Get effective price for a booking date, checking date rules first, then fallback to standard calculation."""
        date_service = DatePricingService()
        price_override = date_service.get_price_override(booking_date, duration_hours)

        if price_override is not None:
            return price_override

        # Fallback to standard tariff calculation
        rental_price = self.get_by_tariff(tariff)
        if rental_price is None:
            raise ValueError(f"No RentalPrice found for tariff: {tariff}")

        # Calculate base price using existing logic
        if duration_hours > 24 and rental_price.multi_day_prices:
            total_days = duration_hours // 24
            remainder_hours = duration_hours % 24

            if remainder_hours > 15 and remainder_hours < 24:
                total_days += 1
                remainder_hours = 0

            if str(total_days) in rental_price.multi_day_prices:
                price = rental_price.multi_day_prices[str(total_days)]
                if remainder_hours > 0:
                    price += remainder_hours * rental_price.extra_hour_price
                return price

        # Standard single-day or hourly calculation
        if duration_hours <= rental_price.duration_hours:
            return rental_price.price
        else:
            extra_hours = duration_hours - rental_price.duration_hours
            return rental_price.price + (extra_hours * rental_price.extra_hour_price)

    def calculate_price_for_date(
        self,
        booking_date: date,
        tariff: Tariff,
        duration_hours: int,
        is_sauna: bool = False,
        is_secret_room: bool = False,
        is_second_room: bool = False,
        is_photoshoot: bool = False,
        count_people: int = 0
    ) -> int:
        """Calculate total price including add-ons, considering date-specific rules."""
        # Get base price (considering date rules)
        base_price = self.get_effective_price_for_date(booking_date, tariff, duration_hours)

        # Get rental price for add-on calculations (always use standard tariff for add-on prices)
        rental_price = self.get_by_tariff(tariff)
        if rental_price is None:
            raise ValueError(f"No RentalPrice found for tariff: {tariff}")

        # Add services using standard pricing (date rules only affect base price)
        additional_price = 0
        if is_sauna and rental_price.sauna_price > 0:
            additional_price += rental_price.sauna_price
        if is_secret_room and rental_price.secret_room_price > 0:
            additional_price += rental_price.secret_room_price
        if is_second_room and rental_price.second_bedroom_price > 0:
            additional_price += rental_price.second_bedroom_price
        if is_photoshoot:
            additional_price += rental_price.photoshoot_price
        if count_people > rental_price.max_people:
            additional_price += (count_people - rental_price.max_people) * rental_price.extra_people_price

        return base_price + additional_price



