"""
Calendar Service - Stub for compatibility
Service for Google Calendar integration.
In the refactored architecture, calendar operations should be handled by the Backend API.
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class CalendarService:
    """Service for Google Calendar operations."""

    def __init__(self):
        """Initialize the calendar service."""
        logger.info("CalendarService stub initialized")

    async def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a calendar event.

        Args:
            summary: Event title
            start_time: Event start time
            end_time: Event end time
            description: Event description

        Returns:
            str: Event ID or None
        """
        logger.info(f"Calendar event creation stub: {summary} from {start_time} to {end_time}")
        return "stub_event_id"

    async def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Update a calendar event.

        Args:
            event_id: Event ID
            summary: New event title
            start_time: New start time
            end_time: New end time
            description: New description

        Returns:
            bool: Success status
        """
        logger.info(f"Calendar event update stub: {event_id}")
        return True

    async def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event.

        Args:
            event_id: Event ID

        Returns:
            bool: Success status
        """
        logger.info(f"Calendar event deletion stub: {event_id}")
        return True

    async def get_events(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """
        Get calendar events in a time range.

        Args:
            start_time: Range start
            end_time: Range end

        Returns:
            List[Dict]: List of events
        """
        logger.info(f"Calendar events query stub: {start_time} to {end_time}")
        return []
