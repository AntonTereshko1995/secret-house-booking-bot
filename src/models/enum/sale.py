from enum import Enum

class Sale(Enum):
    NONE = 0
    RECOMMENDATION_FROM_FRIEND = 1
    FROM_FEEDBACK = 2
    OTHER = 3