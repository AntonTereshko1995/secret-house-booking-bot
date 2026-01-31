from io import BytesIO
import os
import json
from telegram import InputMediaPhoto
from typing import List
from singleton_decorator import singleton
from src.models.rental_price import RentalPrice
from src.models.date_pricing_rule import DatePricingRule
from src.models.holiday_prepayment_rule import HolidayPrepaymentRule


@singleton
class FileService:
    _IMAGE_FOLDER = "assets/images/"
    _TARIFF_JSON = "src/config/tariff_rate.json"
    # _TARIFF_JSON = "src/config/tariff_rate_sale.json"
    _DATE_PRICING_RULES_JSON = "src/config/date_pricing_rules.json"
    _HOLIDAY_PREPAYMENT_RULES_JSON = "src/config/holiday_prepayment_rules.json"

    def get_price_media(self) -> List[InputMediaPhoto]:
        if not os.path.exists(self._IMAGE_FOLDER):
            raise FileNotFoundError(f"Папка {self._IMAGE_FOLDER} не существует.")

        image_files = [
            f for f in os.listdir(self._IMAGE_FOLDER) if f.endswith((".jpg", ".png"))
        ]
        if not image_files:
            return "Нет изображений для загрузки."

        media_list = []
        for image_name in image_files:
            image_path = os.path.join(self._IMAGE_FOLDER, image_name)
            with open(image_path, "rb") as image_file:
                media = InputMediaPhoto(image_file)
                media_list.append(media)
        return media_list

    def get_tariff_rates(self) -> List[RentalPrice]:
        if not os.path.exists(self._TARIFF_JSON):
            raise FileNotFoundError(f"Файл {self._TARIFF_JSON} не существует.")

        tariff_list = []
        with open(self._TARIFF_JSON, "r", encoding="utf-8") as file:
            data = json.load(file)
            tariff_list = [RentalPrice(**item) for item in data["rental_prices"]]
        return tariff_list

    def get_image(self, image_name: str):
        image_path = os.path.join(self._IMAGE_FOLDER, image_name)
        if not os.path.exists(image_path):
            return None

        with open(image_path, "rb") as image_file:
            image_bytes = BytesIO(image_file.read())
            image_bytes.seek(0)
            return image_bytes

    def get_date_pricing_rules(self) -> List[DatePricingRule]:
        if not os.path.exists(self._DATE_PRICING_RULES_JSON):
            raise FileNotFoundError(
                f"Файл {self._DATE_PRICING_RULES_JSON} не существует."
            )

        rules_list = []
        with open(self._DATE_PRICING_RULES_JSON, "r", encoding="utf-8") as file:
            data = json.load(file)
            rules_list = [DatePricingRule(**item) for item in data["pricing_rules"]]
        return rules_list

    def get_holiday_prepayment_rules(self) -> List[HolidayPrepaymentRule]:
        """Загрузить правила предоплаты для праздничных дней из JSON конфигурации."""
        if not os.path.exists(self._HOLIDAY_PREPAYMENT_RULES_JSON):
            raise FileNotFoundError(
                f"Файл {self._HOLIDAY_PREPAYMENT_RULES_JSON} не существует."
            )

        rules_list = []
        with open(self._HOLIDAY_PREPAYMENT_RULES_JSON, "r", encoding="utf-8") as file:
            data = json.load(file)
            rules_list = [
                HolidayPrepaymentRule(**item) for item in data["prepayment_rules"]
            ]
        return rules_list
