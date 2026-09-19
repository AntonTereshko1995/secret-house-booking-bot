import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from services.api_service import PricingApiService
from models.rental_price import RentalPrice


def _make_api_response(is_sale: bool = False) -> dict:
    return {
        "isSaleActive": is_sale,
        "tariffs": [
            {
                "tariffId": "12h-standard",
                "price": 250,
                "saunaPrice": 120,
                "bathTubPrice": 180,
                "secretRoomPrice": 70,
                "extraBedroomPrice": 70,
                "extraHourPrice": 30,
                "extraPeoplePrice": 70,
                "photoshootPrice": 0,
                "multiDayPrices": {},
                "salePrice": 200,
                "saleSaunaPrice": 100,
                "saleBathTubPrice": 150,
                "saleSecretRoomPrice": 60,
                "saleExtraBedroomPrice": 60,
                "saleExtraHourPrice": 25,
                "saleExtraPeoplePrice": 60,
                "salePhotoshootPrice": 0,
                "saleMultiDayPrices": {},
            },
            {
                "tariffId": "daily-3plus",
                "price": 700,
                "saunaPrice": 120,
                "bathTubPrice": 180,
                "secretRoomPrice": 0,
                "extraBedroomPrice": 0,
                "extraHourPrice": 30,
                "extraPeoplePrice": 0,
                "photoshootPrice": 100,
                "multiDayPrices": {1: 700, 2: 1100, 3: 1500},
                "salePrice": 600,
                "saleSaunaPrice": 100,
                "saleBathTubPrice": 150,
                "saleSecretRoomPrice": 0,
                "saleExtraBedroomPrice": 0,
                "saleExtraHourPrice": 25,
                "saleExtraPeoplePrice": 0,
                "salePhotoshootPrice": 80,
                "saleMultiDayPrices": {1: 600, 2: 1000, 3: 1400},
            },
        ],
    }


class TestPricingApiServiceHappyPath:
    def setup_method(self):
        service = PricingApiService()
        service._cached_rates = []

    def test_loads_standard_prices(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = _make_api_response(is_sale=False)
        mock_resp.raise_for_status.return_value = None

        with patch("services.api_service.requests.get", return_value=mock_resp):
            service = PricingApiService()
            rates = service.get_rental_prices()

        assert len(rates) == 2
        rate_12h = next(r for r in rates if r.tariff == 0)
        assert rate_12h.price == 250
        assert rate_12h.sauna_price == 120

    def test_loads_sale_prices_when_sale_active(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = _make_api_response(is_sale=True)
        mock_resp.raise_for_status.return_value = None

        with patch("services.api_service.requests.get", return_value=mock_resp):
            service = PricingApiService()
            rates = service.get_rental_prices()

        rate_12h = next(r for r in rates if r.tariff == 0)
        assert rate_12h.price == 200
        assert rate_12h.sauna_price == 100

    def test_multi_day_prices_converted_to_string_keys(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = _make_api_response(is_sale=False)
        mock_resp.raise_for_status.return_value = None

        with patch("services.api_service.requests.get", return_value=mock_resp):
            service = PricingApiService()
            rates = service.get_rental_prices()

        daily = next(r for r in rates if r.tariff == 1)
        assert "1" in daily.multi_day_prices
        assert "2" in daily.multi_day_prices
        assert daily.multi_day_prices["1"] == 700

    def test_unknown_tariff_id_is_skipped(self):
        data = _make_api_response(is_sale=False)
        data["tariffs"].append({"tariffId": "unknown-tariff", "price": 999})
        mock_resp = MagicMock()
        mock_resp.json.return_value = data
        mock_resp.raise_for_status.return_value = None

        with patch("services.api_service.requests.get", return_value=mock_resp):
            service = PricingApiService()
            rates = service.get_rental_prices()

        tariff_ids = [r.tariff for r in rates]
        assert len(rates) == 2
        assert all(tid in (0, 1) for tid in tariff_ids)

    def test_result_is_cached(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = _make_api_response(is_sale=False)
        mock_resp.raise_for_status.return_value = None

        with patch("services.api_service.requests.get", return_value=mock_resp) as mock_get:
            service = PricingApiService()
            service.get_rental_prices()
            service.get_rental_prices()

        mock_get.assert_called_once()


class TestPricingApiServiceFallback:
    def setup_method(self):
        service = PricingApiService()
        service._cached_rates = []

    def test_falls_back_on_connection_error(self):
        with patch("services.api_service.requests.get", side_effect=ConnectionError("timeout")):
            service = PricingApiService()
            rates = service.get_rental_prices()

        assert len(rates) == 7
        assert all(hasattr(r, "price") and hasattr(r, "tariff") for r in rates)

    def test_falls_back_on_http_error(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("500 Server Error")

        with patch("services.api_service.requests.get", return_value=mock_resp):
            service = PricingApiService()
            rates = service.get_rental_prices()

        assert len(rates) == 7

    def test_falls_back_on_empty_tariff_list(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"isSaleActive": False, "tariffs": []}
        mock_resp.raise_for_status.return_value = None

        with patch("services.api_service.requests.get", return_value=mock_resp):
            service = PricingApiService()
            rates = service.get_rental_prices()

        assert len(rates) == 7

    def test_fallback_default_prices_have_string_keys(self):
        with patch("services.api_service.requests.get", side_effect=ConnectionError):
            service = PricingApiService()
            rates = service.get_rental_prices()

        daily = next(r for r in rates if r.tariff == 1)
        assert "1" in daily.multi_day_prices
        assert daily.multi_day_prices["1"] == 700
