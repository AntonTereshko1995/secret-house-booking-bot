import sys
import os
from typing import List, Optional
from singleton_decorator import singleton

import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models.rental_price import RentalPrice
from src.services.logger_service import LoggerService
from src.config.config import BACKEND_API_URL


TARIFF_METADATA: dict[str, dict] = {
    "12h-standard": {
        "tariff": 0,
        "name": "тариф '12 часов'",
        "duration_hours": 12,
        "max_people": 2,
        "is_check_in_time_limit": False,
        "is_photoshoot": False,
        "is_transfer": False,
    },
    "daily-3plus": {
        "tariff": 1,
        "name": "тариф 'Суточно' от 3 человек",
        "duration_hours": 24,
        "max_people": 6,
        "is_check_in_time_limit": False,
        "is_photoshoot": True,
        "is_transfer": False,
    },
    "work-standard": {
        "tariff": 2,
        "name": "тариф 'Рабочий'",
        "duration_hours": 11,
        "max_people": 2,
        "is_check_in_time_limit": True,
        "is_photoshoot": False,
        "is_transfer": False,
    },
    "incognito-daily": {
        "tariff": 3,
        "name": "тариф 'Инкогнито на день'",
        "duration_hours": 24,
        "max_people": 6,
        "is_check_in_time_limit": False,
        "is_photoshoot": True,
        "is_transfer": True,
    },
    "incognito-12h": {
        "tariff": 4,
        "name": "тариф 'Инкогнито на 12 часов'",
        "duration_hours": 12,
        "max_people": 6,
        "is_check_in_time_limit": False,
        "is_photoshoot": False,
        "is_transfer": True,
    },
    "incognito-work": {
        "tariff": 5,
        "name": "тариф 'Инкогнито (Рабочий)'",
        "duration_hours": 11,
        "max_people": 6,
        "is_check_in_time_limit": True,
        "is_photoshoot": False,
        "is_transfer": True,
    },
    "daily-couple": {
        "tariff": 7,
        "name": "тариф 'Суточно' для двоих'",
        "duration_hours": 24,
        "max_people": 2,
        "is_check_in_time_limit": False,
        "is_photoshoot": True,
        "is_transfer": False,
    },
}

DEFAULT_RENTAL_PRICES: list[dict] = [
    {
        "tariff_id": "12h-standard",
        "price": 250, "sauna_price": 120, "bath_tub_price": 180,
        "secret_room_price": 70, "second_bedroom_price": 70,
        "extra_hour_price": 30, "extra_people_price": 70,
        "photoshoot_price": 0, "multi_day_prices": {},
    },
    {
        "tariff_id": "daily-3plus",
        "price": 700, "sauna_price": 120, "bath_tub_price": 180,
        "secret_room_price": 0, "second_bedroom_price": 0,
        "extra_hour_price": 30, "extra_people_price": 0,
        "photoshoot_price": 100,
        "multi_day_prices": {
            "1": 700, "2": 1100, "3": 1500, "4": 1900, "5": 2300,
            "6": 2700, "7": 3100, "8": 3500, "9": 3900,
            "10": 4300, "11": 4700, "12": 5100, "13": 5500, "14": 5900,
        },
    },
    {
        "tariff_id": "work-standard",
        "price": 180, "sauna_price": 120, "bath_tub_price": 180,
        "secret_room_price": 50, "second_bedroom_price": 50,
        "extra_hour_price": 30, "extra_people_price": 100,
        "photoshoot_price": 0, "multi_day_prices": {},
    },
    {
        "tariff_id": "incognito-daily",
        "price": 900, "sauna_price": 0, "bath_tub_price": 130,
        "secret_room_price": 0, "second_bedroom_price": 0,
        "extra_hour_price": 30, "extra_people_price": 0,
        "photoshoot_price": 0,
        "multi_day_prices": {
            "1": 900, "2": 1600, "3": 2300, "4": 3000, "5": 3700,
            "6": 4400, "7": 5000, "8": 5500, "9": 6100,
            "10": 6600, "11": 5100, "12": 5600, "13": 6200, "14": 6500,
        },
    },
    {
        "tariff_id": "incognito-12h",
        "price": 600, "sauna_price": 0, "bath_tub_price": 130,
        "secret_room_price": 0, "second_bedroom_price": 0,
        "extra_hour_price": 30, "extra_people_price": 0,
        "photoshoot_price": 100, "multi_day_prices": {},
    },
    {
        "tariff_id": "incognito-work",
        "price": 450, "sauna_price": 0, "bath_tub_price": 130,
        "secret_room_price": 0, "second_bedroom_price": 0,
        "extra_hour_price": 30, "extra_people_price": 0,
        "photoshoot_price": 100, "multi_day_prices": {},
    },
    {
        "tariff_id": "daily-couple",
        "price": 500, "sauna_price": 120, "bath_tub_price": 180,
        "secret_room_price": 0, "second_bedroom_price": 0,
        "extra_hour_price": 30, "extra_people_price": 200,
        "photoshoot_price": 100,
        "multi_day_prices": {
            "1": 500, "2": 900, "3": 1200, "4": 1600, "5": 2000,
            "6": 2400, "7": 2800, "8": 3100, "9": 3500,
            "10": 3900, "11": 4300, "12": 4600, "13": 4900, "14": 5200,
        },
    },
]


@singleton
class PricingApiService:
    """Fetch tariff prices from the backend REST API.

    Singleton with lazy load — prices are fetched once per process startup.
    Falls back to hardcoded defaults if the API is unreachable.
    """

    _cached_rates: List[RentalPrice] = []

    def __init__(self) -> None:
        self._is_sauna_bath_tub_combo_active: bool = False

    @property
    def is_sauna_bath_tub_combo_active(self) -> bool:
        if not self._cached_rates:
            self._cached_rates = self._fetch_from_api()
        return self._is_sauna_bath_tub_combo_active

    def get_rental_prices(self) -> List[RentalPrice]:
        if not self._cached_rates:
            self._cached_rates = self._fetch_from_api()
        return self._cached_rates

    def refresh(self) -> None:
        self._cached_rates = []
        self._is_sauna_bath_tub_combo_active = False

    def _fetch_from_api(self) -> List[RentalPrice]:
        url = f"{BACKEND_API_URL}/api/pricing"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            is_sale = data.get("isSaleActive", False)
            self._is_sauna_bath_tub_combo_active = data.get("isSaunaBathTubComboActive", False)
            rates = []
            for record in data.get("tariffs", []):
                rate = self._api_record_to_rental_price(record)
                if rate is not None:
                    rates.append(rate)
            if rates:
                LoggerService.info(
                    __name__,
                    f"Loaded {len(rates)} tariff prices from API "
                    f"(isSaleActive={is_sale}, isSaunaBathTubComboActive={self._is_sauna_bath_tub_combo_active})",
                )
                return rates
            LoggerService.warning(__name__, "API returned empty tariffs list, using fallback")
            return self._get_default_rates()
        except Exception as e:
            LoggerService.error(__name__, f"Failed to fetch pricing from API ({url})", e)
            return self._get_default_rates()

    def _api_record_to_rental_price(self, record: dict) -> Optional[RentalPrice]:
        tariff_id = record.get("tariffId", "")
        meta = TARIFF_METADATA.get(tariff_id)
        if meta is None:
            return None

        # Backend always returns the effective price (sale or standard, decided server-side)
        price = int(record.get("price", 0))
        sauna_price = int(record.get("saunaPrice", 0))
        bath_tub_price = int(record.get("bathTubPrice", 0))
        secret_room_price = int(record.get("secretRoomPrice", 0))
        second_bedroom_price = int(record.get("extraBedroomPrice", 0))
        extra_hour_price = int(record.get("extraHourPrice", 0))
        extra_people_price = int(record.get("extraPeoplePrice", 0))
        photoshoot_price = int(record.get("photoshootPrice", 0))
        combined_sauna_bath_tub_price = int(record.get("combinedSaunaBathTubPrice", 0))
        raw_multi = record.get("multiDayPrices", {})

        # API uses int keys in JSON, RentalPrice.multi_day_prices needs str keys
        # because calculate_price() does: multi_day_prices[str(total_days)]
        multi_day_prices = {str(k): int(v) for k, v in raw_multi.items()}

        return RentalPrice(
            tariff=meta["tariff"],
            name=meta["name"],
            duration_hours=meta["duration_hours"],
            price=price,
            sauna_price=sauna_price,
            bath_tub_price=bath_tub_price,
            secret_room_price=secret_room_price,
            second_bedroom_price=second_bedroom_price,
            extra_hour_price=extra_hour_price,
            extra_people_price=extra_people_price,
            photoshoot_price=photoshoot_price,
            max_people=meta["max_people"],
            is_check_in_time_limit=meta["is_check_in_time_limit"],
            is_photoshoot=meta["is_photoshoot"],
            is_transfer=meta["is_transfer"],
            multi_day_prices=multi_day_prices,
            combined_sauna_bath_tub_price=combined_sauna_bath_tub_price,
        )

    def _get_default_rates(self) -> List[RentalPrice]:
        rates = []
        for item in DEFAULT_RENTAL_PRICES:
            tariff_id = item["tariff_id"]
            meta = TARIFF_METADATA[tariff_id]
            rates.append(
                RentalPrice(
                    tariff=meta["tariff"],
                    name=meta["name"],
                    duration_hours=meta["duration_hours"],
                    price=item["price"],
                    sauna_price=item["sauna_price"],
                    bath_tub_price=item["bath_tub_price"],
                    secret_room_price=item["secret_room_price"],
                    second_bedroom_price=item["second_bedroom_price"],
                    extra_hour_price=item["extra_hour_price"],
                    extra_people_price=item["extra_people_price"],
                    photoshoot_price=item["photoshoot_price"],
                    max_people=meta["max_people"],
                    is_check_in_time_limit=meta["is_check_in_time_limit"],
                    is_photoshoot=meta["is_photoshoot"],
                    is_transfer=meta["is_transfer"],
                    multi_day_prices=item["multi_day_prices"],
                )
            )
        return rates
