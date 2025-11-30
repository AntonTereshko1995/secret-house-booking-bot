"""
Backend API Client for Telegram Bot
Async HTTP client to communicate with the FastAPI backend.
"""
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import sys
import os

# Add parent path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.config import config

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API Error {status_code}: {detail}")


class BackendAPIClient:
    """
    Async HTTP client for Backend API.
    All bot-backend communication goes through this client.
    """

    def __init__(self):
        self.base_url = config.BACKEND_API_URL
        self.api_key = config.BACKEND_API_KEY
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Any:
        """
        Make HTTP request to backend API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (e.g., "/api/v1/bookings")
            data: Request body (for POST, PATCH)
            params: Query parameters (for GET)

        Returns:
            Response JSON data

        Raises:
            APIError: If API returns error status
        """
        url = f"{self.base_url}{endpoint}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    # Log request
                    logger.info(f"API Request: {method} {endpoint} -> {response.status}")

                    # Handle different status codes
                    if response.status == 204:
                        # No content
                        return None

                    response_data = await response.json()

                    if response.status >= 400:
                        # API error
                        detail = response_data.get("detail", "Unknown error")
                        raise APIError(response.status, detail)

                    return response_data

        except aiohttp.ClientError as e:
            logger.error(f"HTTP Client Error: {e}")
            raise APIError(500, f"Connection error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in API request: {e}")
            raise APIError(500, f"Unexpected error: {str(e)}")

    async def _get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """GET request"""
        return await self._request("GET", endpoint, params=params)

    async def _post(self, endpoint: str, data: Dict) -> Any:
        """POST request"""
        return await self._request("POST", endpoint, data=data)

    async def _patch(self, endpoint: str, data: Dict) -> Any:
        """PATCH request"""
        return await self._request("PATCH", endpoint, data=data)

    async def _delete(self, endpoint: str) -> Any:
        """DELETE request"""
        return await self._request("DELETE", endpoint)

    # ============================================
    # BOOKING ENDPOINTS
    # ============================================

    async def create_booking(self, booking_data: Dict) -> Dict:
        """
        Create a new booking.

        Args:
            booking_data: Dict with booking details
                - user_contact: str
                - start_date: datetime (will be converted to ISO format)
                - end_date: datetime
                - tariff: str (e.g., "DAY", "NIGHT")
                - number_of_guests: int
                - has_sauna: bool
                - has_photoshoot: bool
                - has_white_bedroom: bool
                - has_green_bedroom: bool
                - has_secret_room: bool
                - comment: str (optional)
                - wine_preference: str (optional)
                - transfer_address: str (optional)
                - chat_id: int
                - gift_id: int (optional)
                - promocode_id: int (optional)
                - price: float (optional)

        Returns:
            Created booking dict
        """
        # Convert datetime objects to ISO format strings
        data = booking_data.copy()
        if isinstance(data.get("start_date"), datetime):
            data["start_date"] = data["start_date"].isoformat()
        if isinstance(data.get("end_date"), datetime):
            data["end_date"] = data["end_date"].isoformat()

        return await self._post("/api/v1/bookings", data)

    async def get_bookings(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_contact: Optional[str] = None,
        is_admin: bool = False
    ) -> List[Dict]:
        """
        List bookings with filters.

        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            user_contact: Filter by user contact
            is_admin: Include all bookings (admin view)

        Returns:
            List of booking dicts
        """
        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        if user_contact:
            params["user_contact"] = user_contact
        if is_admin:
            params["is_admin"] = "true"

        return await self._get("/api/v1/bookings", params=params)

    async def get_booking(self, booking_id: int) -> Dict:
        """Get booking by ID"""
        return await self._get(f"/api/v1/bookings/{booking_id}")

    async def update_booking(self, booking_id: int, updates: Dict) -> Dict:
        """
        Update a booking.

        Args:
            booking_id: Booking ID
            updates: Dict with fields to update
                - start_date: datetime (optional)
                - end_date: datetime (optional)
                - is_canceled: bool (optional)
                - is_prepaymented: bool (optional)
                - is_done: bool (optional)
                - price: float (optional)
                - prepayment_price: float (optional)

        Returns:
            Updated booking dict
        """
        # Convert datetime objects to ISO format
        data = updates.copy()
        if isinstance(data.get("start_date"), datetime):
            data["start_date"] = data["start_date"].isoformat()
        if isinstance(data.get("end_date"), datetime):
            data["end_date"] = data["end_date"].isoformat()

        return await self._patch(f"/api/v1/bookings/{booking_id}", data)

    async def cancel_booking(self, booking_id: int) -> None:
        """Cancel a booking (soft delete)"""
        await self._delete(f"/api/v1/bookings/{booking_id}")

    async def get_user_bookings(self, user_contact: str) -> List[Dict]:
        """Get all bookings for a user"""
        return await self._get(f"/api/v1/bookings/user/{user_contact}")

    # ============================================
    # AVAILABILITY ENDPOINTS
    # ============================================

    async def check_availability(
        self,
        start_date: datetime,
        end_date: datetime,
        except_booking_id: Optional[int] = None
    ) -> Dict:
        """
        Check if dates are available.

        Returns:
            {
                "available": bool,
                "conflicting_bookings": [...]
            }
        """
        data = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        if except_booking_id:
            data["except_booking_id"] = except_booking_id

        return await self._post("/api/v1/availability/check", data)

    async def get_month_availability(self, year: int, month: int) -> Dict:
        """
        Get availability for a specific month.

        Returns:
            {
                "year": int,
                "month": int,
                "occupied_dates": ["2025-12-01", ...],
                "bookings": [...]
            }
        """
        return await self._get(f"/api/v1/availability/month/{year}/{month}")

    async def get_available_dates(self, start_date: date, end_date: date) -> Dict:
        """
        Get occupied dates in a range.

        Returns:
            {
                "start_date": "2025-12-01",
                "end_date": "2025-12-31",
                "occupied_dates": [...]
            }
        """
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        return await self._get("/api/v1/availability/dates", params=params)

    # ============================================
    # PRICING ENDPOINTS
    # ============================================

    async def calculate_price(self, calculation_data: Dict) -> Dict:
        """
        Calculate price for a booking.

        Args:
            calculation_data: Dict with:
                - tariff: str
                - start_date: datetime
                - end_date: datetime
                - has_sauna: bool
                - has_secret_room: bool
                - has_second_bedroom: bool
                - has_photoshoot: bool
                - number_of_guests: int

        Returns:
            {
                "base_price": float,
                "sauna_price": float,
                "secret_room_price": float,
                "second_bedroom_price": float,
                "photoshoot_price": float,
                "extra_people_price": float,
                "extra_hours_price": float,
                "total_price": float,
                "duration_hours": int,
                "currency": "BYN"
            }
        """
        # Convert datetime to ISO format
        data = calculation_data.copy()
        if isinstance(data.get("start_date"), datetime):
            data["start_date"] = data["start_date"].isoformat()
        if isinstance(data.get("end_date"), datetime):
            data["end_date"] = data["end_date"].isoformat()

        return await self._post("/api/v1/pricing/calculate", data)

    async def get_tariffs(self) -> List[Dict]:
        """Get all available tariffs"""
        return await self._get("/api/v1/pricing/tariffs")

    # ============================================
    # USER ENDPOINTS
    # ============================================

    async def create_or_update_user(self, user_data: Dict) -> Dict:
        """
        Create or update a user.

        Args:
            user_data: Dict with:
                - contact: str (optional)
                - user_name: str (optional)
                - chat_id: int (optional)

        Returns:
            User dict
        """
        return await self._post("/api/v1/users", user_data)

    async def get_user(self, user_contact: str) -> Dict:
        """Get user by contact"""
        return await self._get(f"/api/v1/users/{user_contact}")

    async def get_user_by_chat_id(self, chat_id: int) -> Dict:
        """Get user by Telegram chat ID"""
        return await self._get(f"/api/v1/users/chat/{chat_id}")

    async def list_users(self) -> List[Dict]:
        """List all users (admin only)"""
        return await self._get("/api/v1/users")

    # ============================================
    # GIFT CERTIFICATE ENDPOINTS
    # ============================================

    async def create_gift(self, gift_data: Dict) -> Dict:
        """
        Create a gift certificate.

        Args:
            gift_data: Dict with:
                - contact: str
                - number: str
                - tariff: str
                - chat_id: int

        Returns:
            Gift dict
        """
        return await self._post("/api/v1/gifts", gift_data)

    async def get_gift(self, gift_id: int) -> Dict:
        """Get gift certificate by ID"""
        return await self._get(f"/api/v1/gifts/{gift_id}")

    async def validate_gift(self, certificate_number: str) -> Dict:
        """
        Validate a gift certificate.

        Returns:
            {
                "valid": bool,
                "gift": Dict or None,
                "message": str
            }
        """
        data = {"certificate_number": certificate_number}
        return await self._post("/api/v1/gifts/validate", data)

    async def redeem_gift(self, gift_id: int) -> Dict:
        """Mark gift certificate as used"""
        return await self._patch(f"/api/v1/gifts/{gift_id}/redeem", {})

    # ============================================
    # PROMOCODE ENDPOINTS
    # ============================================

    async def create_promocode(self, promocode_data: Dict) -> Dict:
        """
        Create a promocode (admin only).

        Args:
            promocode_data: Dict with:
                - code: str
                - discount_percentage: float
                - promocode_type: str
                - is_active: bool (optional, default True)

        Returns:
            Promocode dict
        """
        return await self._post("/api/v1/promocodes", promocode_data)

    async def list_promocodes(self, is_active: Optional[bool] = None) -> List[Dict]:
        """List all promocodes (admin only)"""
        params = {}
        if is_active is not None:
            params["is_active"] = "true" if is_active else "false"
        return await self._get("/api/v1/promocodes", params=params)

    async def validate_promocode(self, code: str) -> Dict:
        """
        Validate a promocode.

        Returns:
            {
                "valid": bool,
                "discount_percentage": float or None,
                "promocode": Dict or None,
                "message": str
            }
        """
        data = {"code": code}
        return await self._post("/api/v1/promocodes/validate", data)

    async def delete_promocode(self, promocode_id: int) -> None:
        """Delete a promocode (admin only, soft delete)"""
        await self._delete(f"/api/v1/promocodes/{promocode_id}")

    async def get_promocode_by_name(self, name: str) -> Optional[Dict]:
        """Get promocode by name"""
        try:
            promocodes = await self._get("/api/v1/promocodes", params={"name": name})
            return promocodes[0] if promocodes else None
        except:
            return None

    async def list_active_promocodes(self) -> List[Dict]:
        """List all active promocodes"""
        return await self.list_promocodes(is_active=True)

    async def deactivate_promocode(self, promocode_id: int) -> bool:
        """Deactivate a promocode (soft delete)"""
        try:
            await self._patch(f"/api/v1/promocodes/{promocode_id}", {"is_active": False})
            return True
        except:
            return False

    # ============================================
    # USERS EXTENDED
    # ============================================

    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        try:
            return await self._get(f"/api/v1/users/{user_id}")
        except:
            return None

    async def get_all_users(self) -> List[Dict]:
        """Get all users"""
        return await self.list_users()

    async def get_users_without_chat_id(self) -> List[Dict]:
        """Get users without chat_id"""
        users = await self.list_users()
        return [u for u in users if not u.get("chat_id")]

    async def get_total_users_count(self) -> int:
        """Get total count of users"""
        users = await self.list_users()
        return len(users)

    async def get_user_chat_ids_with_bookings(self) -> List[int]:
        """Get chat IDs of users with bookings"""
        bookings = await self.get_bookings()
        user_ids = set(b.get("user_id") for b in bookings if b.get("user_id"))
        users = await self.list_users()
        return [u["chat_id"] for u in users if u.get("chat_id") and u.get("id") in user_ids]

    async def get_user_chat_ids_without_bookings(self) -> List[int]:
        """Get chat IDs of users without bookings"""
        bookings = await self.get_bookings()
        user_ids_with_bookings = set(b.get("user_id") for b in bookings if b.get("user_id"))
        users = await self.list_users()
        return [u["chat_id"] for u in users if u.get("chat_id") and u.get("id") not in user_ids_with_bookings]

    # ============================================
    # BOOKINGS EXTENDED
    # ============================================

    async def get_unpaid_bookings(self) -> List[Dict]:
        """Get all unpaid bookings"""
        bookings = await self.get_bookings()
        return [b for b in bookings if not b.get("is_prepaymented") and not b.get("is_canceled")]

    async def get_bookings_by_date_range(
        self,
        start_date: str,
        end_date: str,
        is_paid: Optional[bool] = None
    ) -> List[Dict]:
        """Get bookings within date range"""
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        if is_paid is not None:
            params["is_paid"] = "true" if is_paid else "false"
        bookings = await self.get_bookings()

        # Filter by date range
        from datetime import datetime
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        result = []
        for b in bookings:
            booking_start = datetime.fromisoformat(b["start_date"])
            booking_end = datetime.fromisoformat(b["end_date"])

            # Check if booking overlaps with range
            if booking_start <= end and booking_end >= start:
                if is_paid is None or b.get("is_prepaymented") == is_paid:
                    result.append(b)

        return result

    # ============================================
    # GIFTS EXTENDED
    # ============================================

    async def get_gift_by_id(self, gift_id: int) -> Optional[Dict]:
        """Get gift by ID"""
        try:
            return await self._get(f"/api/v1/gifts/{gift_id}")
        except:
            return None

    async def update_gift(self, gift_id: int, gift_data: Dict) -> Dict:
        """Update gift details"""
        return await self._patch(f"/api/v1/gifts/{gift_id}", gift_data)

    # ============================================
    # HEALTH CHECK
    # ============================================

    async def health_check(self) -> Dict:
        """Check if backend API is healthy"""
        try:
            return await self._get("/health")
        except Exception as e:
            logger.error(f"Backend health check failed: {e}")
            raise
