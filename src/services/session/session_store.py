"""
Core in-memory key-value storage with JSON persistence.
Replaces Redis with lightweight file-based storage.
"""
import asyncio
import json
import time
from typing import Optional, Dict
from pathlib import Path
from src.services.logger_service import LoggerService


class SessionStore:
    """
    Thread-safe in-memory key-value storage with automatic cleanup.

    Features:
    - TTL-based expiration
    - JSON file persistence
    - Automatic cleanup task
    - asyncio.Lock for concurrency safety
    """

    def __init__(self, storage_file: str, cleanup_interval_days: int = 5):
        """
        Initialize storage.

        Args:
            storage_file: Path to JSON persistence file
            cleanup_interval_days: How often to run cleanup (default: 5 days)
        """
        self._storage: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
        self._storage_file = Path(storage_file)
        self._cleanup_interval = cleanup_interval_days * 86400
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """
        Start the storage service.
        Loads data from disk and starts cleanup task.
        """
        await self._load_from_disk()
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        LoggerService.info(__name__, f"SessionStore started with file: {self._storage_file}")

    async def stop(self) -> None:
        """Stop the storage service and cancel cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        await self._save_to_disk()
        LoggerService.info(__name__, "SessionStore stopped")

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """
        Store a value with TTL.

        Args:
            key: Storage key (e.g., "booking:123456")
            value: JSON string value
            ttl_seconds: Time-to-live in seconds
        """
        async with self._lock:
            self._storage[key] = {
                "value": value,
                "created_at": time.time(),
                "ttl_seconds": ttl_seconds
            }
            await self._save_to_disk()

    async def get(self, key: str) -> Optional[str]:
        """
        Retrieve a value if not expired.

        Returns:
            Value string or None if not found/expired
        """
        async with self._lock:
            if key not in self._storage:
                return None

            entry = self._storage[key]
            age = time.time() - entry["created_at"]

            if age > entry["ttl_seconds"]:
                del self._storage[key]
                await self._save_to_disk()
                return None

            return entry["value"]

    async def delete(self, key: str) -> None:
        """Delete a key from storage."""
        async with self._lock:
            if key in self._storage:
                del self._storage[key]
                await self._save_to_disk()

    async def _load_from_disk(self) -> None:
        """
        Load storage from JSON file.
        Handles corrupt files gracefully.
        """
        if not self._storage_file.exists():
            LoggerService.info(__name__, "No existing storage file, starting fresh")
            return

        try:
            with open(self._storage_file, 'r', encoding='utf-8') as f:
                self._storage = json.load(f)
            LoggerService.info(__name__, f"Loaded {len(self._storage)} entries from disk")
        except json.JSONDecodeError as e:
            LoggerService.error(__name__, "Corrupt storage file, starting fresh", exception=e)
            self._storage = {}
        except Exception as e:
            LoggerService.error(__name__, "Failed to load storage", exception=e)
            self._storage = {}

    async def _save_to_disk(self) -> None:
        """
        Save storage to JSON file atomically.
        Uses temp file + rename for atomic write.
        """
        try:
            temp_file = self._storage_file.with_suffix('.tmp')

            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._storage, f, ensure_ascii=False, indent=2)

            temp_file.replace(self._storage_file)

        except Exception as e:
            LoggerService.error(__name__, "Failed to save storage", exception=e)

    async def _cleanup_expired(self) -> None:
        """Remove all expired entries."""
        async with self._lock:
            current_time = time.time()
            keys_to_delete = []

            for key, entry in self._storage.items():
                age = current_time - entry["created_at"]
                if age > entry["ttl_seconds"]:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._storage[key]

            if keys_to_delete:
                await self._save_to_disk()
                LoggerService.info(
                    __name__,
                    f"Cleaned up {len(keys_to_delete)} expired entries"
                )

    async def _cleanup_loop(self) -> None:
        """
        Background task that runs cleanup periodically.
        Runs on startup + every N days.
        """
        await self._cleanup_expired()

        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                LoggerService.error(__name__, "Error in cleanup loop", exception=e)
