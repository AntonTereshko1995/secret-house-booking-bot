import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.base_database_service import BaseDatabaseService
from src.services.logger_service import LoggerService
from db.models.gift import GiftBase
from src.models.enum.tariff import Tariff
from matplotlib.dates import relativedelta
from singleton_decorator import singleton
from sqlalchemy import select
from src.config.config import MAX_PERIOD_FOR_GIFT_IN_MONTHS


@singleton
class GiftService(BaseDatabaseService):
    """Service for gift certificate-related database operations."""

    def add_gift(
        self,
        buyer_contact: str,
        tariff: Tariff,
        has_sauna: bool,
        has_secret_room: bool,
        has_additional_bedroom: bool,
        price: float,
        code: str,
    ) -> GiftBase:
        """Add a new gift certificate to the database."""
        with self.Session() as session:
            try:
                date_expired = datetime.today() + relativedelta(
                    months=MAX_PERIOD_FOR_GIFT_IN_MONTHS
                )
                new_gift = GiftBase(
                    buyer_contact=buyer_contact,
                    tariff=tariff,
                    date_expired=date_expired,
                    has_sauna=has_sauna,
                    has_secret_room=has_secret_room,
                    has_additional_bedroom=has_additional_bedroom,
                    price=price,
                    code=code,
                )
                session.add(new_gift)
                session.commit()
                print(f"Gift added: {new_gift}")
                return new_gift
            except Exception as e:
                print(f"Error adding gift: {e}")
                session.rollback()
                LoggerService.error(__name__, "add_gift", e)

    def update_gift(
        self,
        gift_id: int,
        user_id: int = None,
        date_expired: datetime = None,
        is_paymented: bool = None,
        is_done: bool = None,
    ) -> GiftBase:
        """Update gift certificate fields."""
        with self.Session() as session:
            try:
                gift = session.scalar(select(GiftBase).where(GiftBase.id == gift_id))
                if not gift:
                    print(f"Gift with id {gift_id} not found.")
                    return

                if user_id:
                    gift.user_id = user_id
                if date_expired:
                    gift.date_expired = date_expired
                if is_paymented:
                    gift.is_paymented = is_paymented
                if is_done:
                    gift.is_done = is_done

                session.commit()
                print(f"Gift updated: {gift}")
                return gift
            except Exception as e:
                session.rollback()
                print(f"Error updating Gift: {e}")
                LoggerService.error(__name__, "update_gift", e)

    def get_gift_by_code(self, code: str) -> GiftBase:
        """Get valid gift certificate by code (paid and not used)."""
        try:
            with self.Session() as session:
                gift = session.scalar(
                    select(GiftBase).where(
                        (GiftBase.code == code)
                        & (GiftBase.is_paymented == True)
                        & (GiftBase.is_done == False)
                    )
                )
                return gift
        except Exception as e:
            print(f"Error in get_gift_by_code: {e}")
            LoggerService.error(__name__, "get_gift_by_code", e)

    def get_gift_by_id(self, id: int) -> GiftBase:
        """Get gift certificate by ID."""
        try:
            with self.Session() as session:
                gift = session.scalar(select(GiftBase).where(GiftBase.id == id))
                return gift
        except Exception as e:
            print(f"Error in get_gift_by_id: {e}")
            LoggerService.error(__name__, "get_gift_by_id", e)
