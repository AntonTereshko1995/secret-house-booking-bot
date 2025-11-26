import sys
import os
import json
from datetime import date, datetime, timedelta
from typing import Optional
from dateutil.relativedelta import relativedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.database.base import BaseRepository
from src.services.logger_service import LoggerService
from db.models.promocode import PromocodeBase
from src.models.enum.tariff import Tariff
from src.models.enum.promocode_type import PromocodeType
from src.config.config import PERIOD_IN_MONTHS
from singleton_decorator import singleton
from sqlalchemy import select


@singleton
class PromocodeRepository(BaseRepository):
    """Service for promocode-related database operations."""

    def add_promocode(
        self,
        name: str,
        date_from: date,
        date_to: date,
        discount_percentage: float,
        applicable_tariffs: Optional[list[int]] = None,
        promocode_type: int = 1,
    ) -> PromocodeBase:
        """Add a new promocode to the database."""
        with self.Session() as session:
            try:
                # Convert tariff list to JSON string if provided
                tariffs_json = None
                if applicable_tariffs is not None:
                    tariffs_json = json.dumps(applicable_tariffs)

                new_promocode = PromocodeBase(
                    name=name.upper(),  # Always store uppercase
                    promocode_type=promocode_type,
                    date_from=date_from,
                    date_to=date_to,
                    discount_percentage=discount_percentage,
                    applicable_tariffs=tariffs_json,
                    is_active=True,
                )
                session.add(new_promocode)
                session.commit()
                session.refresh(new_promocode)
                # Detach from session to avoid lazy load errors
                session.expunge(new_promocode)
                print(f"Promocode added: {new_promocode}")
                return new_promocode
            except Exception as e:
                print(f"Error adding promocode: {e}")
                session.rollback()
                LoggerService.error(__name__, "add_promocode", e)
                raise

    def get_promocode_by_name(self, name: str) -> Optional[PromocodeBase]:
        """Get promocode by name."""
        try:
            with self.Session() as session:
                promocode = session.scalar(
                    select(PromocodeBase).where(PromocodeBase.name == name.upper())
                )
                if promocode:
                    # Detach from session to avoid lazy load errors
                    session.expunge(promocode)
                return promocode
        except Exception as e:
            print(f"Error in get_promocode_by_name: {e}")
            LoggerService.error(__name__, "get_promocode_by_name", e)
            return None

    def get_promocode_by_id(self, promocode_id: int) -> Optional[PromocodeBase]:
        """Get promocode by ID."""
        try:
            with self.Session() as session:
                promocode = session.scalar(
                    select(PromocodeBase).where(PromocodeBase.id == promocode_id)
                )
                if promocode:
                    # Detach from session to avoid lazy load errors
                    session.expunge(promocode)
                return promocode
        except Exception as e:
            print(f"Error in get_promocode_by_id: {e}")
            LoggerService.error(__name__, "get_promocode_by_id", e)
            return None

    def validate_promocode(
        self, name: str, booking_date: date, tariff: Tariff
    ) -> tuple[bool, str, Optional[PromocodeBase]]:
        """
        Validates promocode against booking parameters.
        Returns: (is_valid, error_message, promocode_object)
        """
        try:
            with self.Session() as session:
                # Case-insensitive name lookup, uppercase before query
                promo = session.scalar(
                    select(PromocodeBase).where(
                        PromocodeBase.name == name.upper(),
                        PromocodeBase.is_active,
                    )
                )

                if not promo:
                    return (False, "❌ Промокод не найден", None)

                today = date.today()

                # Type 1: BOOKING_DATES - booking must be within promo dates
                if promo.promocode_type == PromocodeType.BOOKING_DATES.value:
                    if not (promo.date_from <= booking_date <= promo.date_to):
                        return (False, "❌ Промокод недействителен в выбранную дату бронирования", None)

                # Type 2: USAGE_PERIOD - booking can be any time, but promo must be used within period
                elif promo.promocode_type == PromocodeType.USAGE_PERIOD.value:
                    # Check if TODAY is within the promocode usage period
                    if not (promo.date_from <= today <= promo.date_to):
                        return (False, "❌ Промокод недействителен в данный период", None)

                    # Check if booking date is within allowed future period (PERIOD_IN_MONTHS)
                    max_booking_date = today + relativedelta(months=PERIOD_IN_MONTHS)
                    if booking_date > max_booking_date:
                        return (
                            False,
                            f"❌ Бронирование возможно только на {PERIOD_IN_MONTHS} месяцев вперед",
                            None
                        )

                # Tariff validation - null/empty list means ALL tariffs
                if promo.applicable_tariffs:
                    applicable = json.loads(promo.applicable_tariffs)
                    if tariff.value not in applicable:
                        return (
                            False,
                            "❌ Промокод не применим к выбранному тарифу",
                            None,
                        )

                # Detach from session before returning to avoid lazy load errors
                session.expunge(promo)
                return (True, "✅ Промокод применен!", promo)

        except Exception as e:
            print(f"Error in validate_promocode: {e}")
            LoggerService.error(__name__, "validate_promocode", e)
            return (False, "❌ Ошибка при проверке промокода", None)

    def list_active_promocodes(self) -> list[PromocodeBase]:
        """Get all active promocodes."""
        try:
            with self.Session() as session:
                promocodes = session.scalars(
                    select(PromocodeBase).where(PromocodeBase.is_active)
                ).all()
                # Detach all objects from session to avoid lazy load errors
                for promo in promocodes:
                    session.expunge(promo)
                return list(promocodes)
        except Exception as e:
            print(f"Error in list_active_promocodes: {e}")
            LoggerService.error(__name__, "list_active_promocodes", e)
            return []

    def deactivate_promocode(self, promocode_id: int) -> bool:
        """Deactivate a promocode (soft delete)."""
        try:
            with self.Session() as session:
                promocode = session.scalar(
                    select(PromocodeBase).where(PromocodeBase.id == promocode_id)
                )
                if not promocode:
                    return False

                promocode.is_active = False
                session.commit()
                print(f"Promocode deactivated: {promocode}")
                return True
        except Exception as e:
            print(f"Error in deactivate_promocode: {e}")
            LoggerService.error(__name__, "deactivate_promocode", e)
            return False

    def deactivate_expired_promocodes(self) -> int:
        """
        Deactivate all promocodes where date_to has passed.
        Returns: count of deactivated promocodes
        """
        try:
            with self.Session() as session:
                today = date.today()
                expired_promocodes = session.scalars(
                    select(PromocodeBase).where(
                        PromocodeBase.is_active,
                        PromocodeBase.date_to < today
                    )
                ).all()

                count = 0
                for promo in expired_promocodes:
                    promo.is_active = False
                    count += 1
                    print(f"Expired promocode deactivated: {promo.name} (expired on {promo.date_to})")

                session.commit()
                return count
        except Exception as e:
            print(f"Error in deactivate_expired_promocodes: {e}")
            LoggerService.error(__name__, "deactivate_expired_promocodes", e)
            return 0
