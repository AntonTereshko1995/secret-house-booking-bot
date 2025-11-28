from dataclasses import dataclass
from typing import Optional
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Feedback:
    """
    Pydantic model for feedback data during conversation.

    IMPORTANT: This is ONLY used for temporary storage in Redis during
    the conversation. Feedback is NOT saved to database - only sent to
    admin chat and then cleared from Redis.
    """

    booking_id: Optional[int] = None
    chat_id: Optional[int] = None
    current_question: Optional[int] = None

    # Rating questions (1-10)
    expectations_rating: Optional[int] = None
    comfort_rating: Optional[int] = None
    cleanliness_rating: Optional[int] = None
    host_support_rating: Optional[int] = None
    location_rating: Optional[int] = None
    recommendation_rating: Optional[int] = None

    # Text questions
    liked_most: Optional[str] = None
    improvements: Optional[str] = None
    public_review: Optional[str] = None
