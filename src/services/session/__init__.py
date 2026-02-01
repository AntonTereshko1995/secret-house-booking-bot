"""Session storage module - replaces Redis."""
from .persistence import CustomPersistence

__all__ = ["CustomPersistence"]
