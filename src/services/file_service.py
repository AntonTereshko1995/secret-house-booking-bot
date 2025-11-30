"""
File Service - Stub for compatibility
Service for file operations (upload/download).
"""
import logging

logger = logging.getLogger(__name__)


class FileService:
    """Service for handling file operations."""

    def __init__(self):
        """Initialize the file service."""
        pass

    async def upload_file(self, file_data, filename: str) -> str:
        """
        Upload a file.

        Args:
            file_data: File data
            filename: Name of the file

        Returns:
            str: URL or path to uploaded file
        """
        logger.info(f"File upload stub called for: {filename}")
        return f"/uploads/{filename}"

    async def download_file(self, file_url: str) -> bytes:
        """
        Download a file.

        Args:
            file_url: URL of the file

        Returns:
            bytes: File content
        """
        logger.info(f"File download stub called for: {file_url}")
        return b""
