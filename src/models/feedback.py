"""
Feedback model for user feedback data.
"""
import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Feedback:
    """Model for storing user feedback information."""

    message: Optional[str] = None
    rating: Optional[int] = None
    contact: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert Feedback to dictionary."""
        return {
            "message": self.message,
            "rating": self.rating,
            "contact": self.contact,
        }

    def to_json(self) -> str:
        """Serialize Feedback to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "Feedback":
        """Create Feedback from dictionary."""
        return cls(
            message=data.get("message"),
            rating=data.get("rating"),
            contact=data.get("contact"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Feedback":
        """Deserialize Feedback from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
