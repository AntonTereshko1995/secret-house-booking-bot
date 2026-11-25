"""Unit tests for the review API client (POST /api/reviews)."""
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.review_api_service import ReviewApiService

PAYLOAD = {
    "bookingPublicId": "00000000-0000-0000-0000-000000000001",
    "ratingExpectations": 10,
    "ratingComfort": 10,
    "ratingCleanliness": 10,
    "ratingCommunication": 10,
    "ratingLocation": 10,
    "ratingRecommendation": 10,
    "likedMost": "Всё",
    "improvement": "Ничего",
    "publicReview": "Отлично",
}


def test_submit_review_posts_and_returns_json():
    service = ReviewApiService()
    response = MagicMock()
    response.json.return_value = {
        "ok": True,
        "reviewId": 1,
        "rewardPromoCode": "REV1A2B3C4D",
        "validUntil": "2026-06-01",
    }
    response.raise_for_status.return_value = None

    with patch("requests.post", return_value=response) as mock_post:
        result = service.submit_review(PAYLOAD)

    assert result["rewardPromoCode"] == "REV1A2B3C4D"
    assert result["validUntil"] == "2026-06-01"
    mock_post.assert_called_once()


def test_submit_review_returns_none_on_error():
    service = ReviewApiService()

    with (
        patch("requests.post", side_effect=Exception("connection refused")),
        patch("src.services.review_api_service.LoggerService.error"),
    ):
        result = service.submit_review(PAYLOAD)

    assert result is None
