"""
GPT Service - Stub for compatibility
Service for OpenAI GPT integration for customer support.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GptService:
    """Service for GPT-based customer support."""

    def __init__(self):
        """Initialize the GPT service."""
        logger.info("GptService stub initialized")

    async def get_answer(self, question: str, context: Optional[str] = None) -> str:
        """
        Get an AI-generated answer to a question.

        Args:
            question: User's question
            context: Optional context for the question

        Returns:
            str: AI-generated answer
        """
        logger.info(f"GPT query stub: {question}")
        return "Извините, AI-помощник временно недоступен. Пожалуйста, свяжитесь с администратором."
