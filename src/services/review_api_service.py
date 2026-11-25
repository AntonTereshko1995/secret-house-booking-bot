"""Client for the secret-house-api review endpoint.

The bot no longer creates reward promocodes itself and no longer sends the
review text to the admin chat: it posts the nine answers to
``POST {BACKEND_API_URL}/api/reviews`` and shows the code returned by the API.
"""
import sys
import os
from typing import Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
from singleton_decorator import singleton

from src.services.logger_service import LoggerService
from src.config.config import BACKEND_API_URL

REVIEW_REQUEST_TIMEOUT = 10


@singleton
class ReviewApiService:
    """Submit guest reviews to the backend REST API."""

    def submit_review(self, payload: dict) -> Optional[dict]:
        """POST the review payload; return the parsed JSON response or None on failure."""
        url = f"{BACKEND_API_URL}/api/reviews"
        try:
            response = requests.post(url, json=payload, timeout=REVIEW_REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            LoggerService.error(
                __name__,
                f"Failed to submit review to API ({url})",
                exception=e,
            )
            return None
