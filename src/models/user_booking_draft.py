from dataclasses import dataclass
from typing import Optional
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class UserBookingDraft:
    """Draft data for user booking flow to avoid global variables"""
    user_contact: Optional[str] = None
