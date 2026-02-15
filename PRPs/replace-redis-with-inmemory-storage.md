name: "Replace Redis with Custom In-Memory Key-Value Storage"
description: |
  Complete removal of Redis dependency and replacement with lightweight custom in-memory
  key-value storage with JSON persistence and automatic cleanup.

---

## Goal

Remove Redis dependency from the Telegram bot application and replace it with a custom in-memory key-value storage solution that:
- Stores session data in memory with file-based persistence (JSON)
- Automatically cleans up expired records every 5 days (configurable)
- Maintains exact same API interface as RedisSessionService
- Supports async operations with asyncio.Lock for concurrency safety
- Persists data between application restarts

## Why

- **Redis is too heavy**: Overkill for simple key-value storage in a single-instance Telegram bot
- **Simplified deployment**: No need for external Redis server in cloud environments
- **Cost reduction**: Eliminates Redis hosting costs
- **Easier maintenance**: Self-contained storage solution without external dependencies
- **Sufficient for use case**: Bot handles session data for individual users sequentially

## What

Replace all Redis functionality with custom `SessionStore` class that:
1. Stores data in memory as dict with TTL tracking
2. Persists to JSON file on every write operation
3. Loads from JSON file on startup
4. Runs background cleanup task every 5 days (configurable)
5. Maintains thread-safety with asyncio.Lock

### Success Criteria
- [ ] All Redis code removed from project
- [ ] All handlers work identically with new storage
- [ ] Data persists between application restarts
- [ ] Old records are automatically cleaned up
- [ ] No performance degradation
- [ ] All manual tests pass (see MANUAL_TESTING_GUIDE.md)

## All Needed Context

### Documentation & References
```yaml
- file: src/services/redis/redis_session_service.py
  why: Main Redis service to replace - understand all methods and their signatures

- file: src/services/redis/redis_persistence.py
  why: Telegram bot conversation state persistence - must replicate this functionality

- file: src/services/redis/redis_connection.py
  why: Redis connection manager - will be completely removed

- file: src/handlers/booking_handler.py
  why: Largest user of Redis (120+ operations) - primary integration testing target

- file: src/models/booking_draft.py
  why: Example of dataclass_json model - understand serialization pattern

- file: src/main.py
  why: Application entry point - where RedisPersistence is initialized

- file: PRPs/CLAUDE.md
  why: Project coding standards - KISS, YAGNI, file size limits, asyncio patterns

- file: MANUAL_TESTING_GUIDE.md
  why: Manual testing procedures to validate the replacement works correctly
```

### Current Codebase Structure
```bash
secret-house-booking-bot/
├── src/
│   ├── main.py                          # Application entry point
│   ├── config/
│   │   └── config.py                    # REDIS_URL, REDIS_PORT, REDIS_SSL configs
│   ├── services/
│   │   └── redis/
│   │       ├── __init__.py              # Exports RedisPersistence
│   │       ├── redis_connection.py       # Singleton Redis client (DELETE)
│   │       ├── redis_session_service.py  # Main session service (REPLACE)
│   │       └── redis_persistence.py      # Telegram persistence (REPLACE)
│   ├── handlers/
│   │   ├── booking_handler.py           # 120+ Redis operations
│   │   ├── feedback_handler.py          # ~40 Redis operations
│   │   ├── cancel_booking_handler.py
│   │   ├── change_booking_date_handler.py
│   │   └── gift_certificate_handler.py
│   └── models/
│       ├── booking_draft.py             # @dataclass_json models
│       ├── feedback.py
│       └── [other draft models]
├── requirements.txt                     # Contains 'redis' dependency
└── PRPs/
    └── CLAUDE.md                        # Project coding standards
```

### Desired Codebase Structure
```bash
secret-house-booking-bot/
├── src/
│   ├── constants.py                     # ADD: CLEANUP_INTERVAL_DAYS = 5, SESSION_TTL_HOURS = 24
│   ├── services/
│   │   └── session/                     # RENAME: redis/ -> session/
│   │       ├── __init__.py              # MODIFY: Export new classes
│   │       ├── session_store.py         # CREATE: Core storage with persistence
│   │       ├── session_service.py       # CREATE: Replaces redis_session_service.py
│   │       └── persistence.py           # CREATE: Replaces redis_persistence.py
│   └── [rest unchanged]
└── requirements.txt                     # MODIFY: Remove 'redis' line
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: python-telegram-bot uses asyncio
# - All storage operations must be async-safe
# - Use asyncio.Lock() not threading.Lock()
# - Use async with for file I/O operations

# GOTCHA: dataclasses_json serialization
# - All Draft models use .to_json() -> str and .from_json(str) -> obj
# - Must preserve this exact interface
# - datetime objects serialize to ISO format strings

# GOTCHA: Telegram Update object
# - chat_id extraction uses NavigationService.get_chat_id(update)
# - This is already abstracted in current code

# GOTCHA: JSON persistence strategy
# - Must handle concurrent writes safely
# - File write should be atomic (write to temp file, then rename)
# - Must handle corrupt JSON gracefully on startup

# GOTCHA: TTL management
# - OLD: Redis used 24 hours for sessions, 3 days for conversations
# - NEW: Unified TTL = 5 суток (5 days) for ALL records
# - Must track both created_at and TTL per entry

# CRITICAL: Cleanup task scheduling
# - Use asyncio background task, not separate thread
# - Must handle application shutdown gracefully
# - Runs on startup + every 5 days

# GOTCHA: Error handling pattern
# - Current code logs errors but doesn't raise exceptions
# - Must preserve this behavior for backward compatibility
```

## Implementation Blueprint

### Data Structure Design

```python
# Core storage structure in memory
{
    "booking:123456": {
        "value": "{...json...}",      # Serialized dataclass_json
        "created_at": 1706745600.0,   # Unix timestamp
        "ttl_seconds": 432000         # 5 суток = 5 * 24 * 3600
    },
    "feedback:123456": {
        "value": "{...json...}",
        "created_at": 1706745600.0,
        "ttl_seconds": 432000         # 5 суток для всех типов
    },
    "conversation_state:booking_handler": {
        "value": "{...json...}",
        "created_at": 1706745600.0,
        "ttl_seconds": 432000         # 5 суток (единообразно)
    }
}
```

### Task List

```yaml
Task 1: Create constants configuration
  FILE: src/constants.py
  ACTION: ADD new constants at the end of file
  CONTENT: |
    # Session storage configuration
    SESSION_STORAGE_FILE = "session_storage.json"
    SESSION_TTL_DAYS = 5  # Все записи живут 5 суток
    CLEANUP_INTERVAL_DAYS = 5  # Очистка каждые 5 суток

Task 2: Create core SessionStore class
  FILE: src/services/session/session_store.py (NEW)
  ACTION: CREATE new file
  PURPOSE: |
    Core in-memory key-value storage with:
    - Dict-based storage with TTL tracking
    - JSON file persistence
    - Automatic cleanup background task
    - asyncio.Lock for concurrency safety
  METHODS:
    - __init__(storage_file: str, cleanup_interval_days: int)
    - async start() -> None
    - async stop() -> None
    - async set(key: str, value: str, ttl_seconds: int) -> None
    - async get(key: str) -> Optional[str]
    - async delete(key: str) -> None
    - async _load_from_disk() -> None
    - async _save_to_disk() -> None
    - async _cleanup_expired() -> None
    - async _cleanup_loop() -> None

Task 3: Create SessionService (replaces RedisSessionService)
  FILE: src/services/session/session_service.py (NEW)
  ACTION: CREATE new file with EXACT SAME API as redis_session_service.py
  PATTERN: Mirror src/services/redis/redis_session_service.py
  PRESERVE: All method signatures must remain identical
  METHODS: |
    All 30+ methods from RedisSessionService:
    - init_booking(update), set_booking(update, booking), get_booking(update), etc.
    - init_feedback(update), set_feedback(update, feedback), get_feedback(update), etc.
    - init_cancel_booking, init_change_booking, init_gift_certificate, init_user_booking
    - All update_*_field and clear_* methods
  MODIFY: |
    - Replace self._redis.client.setex() with await self._store.set()
    - Replace self._redis.client.get() with await self._store.get()
    - Replace self._redis.client.delete() with await self._store.delete()

Task 4: Create CustomPersistence (replaces RedisPersistence)
  FILE: src/services/session/persistence.py (NEW)
  ACTION: CREATE new file
  PATTERN: Mirror src/services/redis/redis_persistence.py
  PURPOSE: Implement BasePersistence for Telegram conversation states
  PRESERVE: All method signatures from RedisPersistence
  MODIFY: Use SessionStore instead of RedisConnection

Task 5: Update __init__.py exports
  FILE: src/services/session/__init__.py (NEW)
  ACTION: CREATE with exports
  CONTENT: |
    from .persistence import CustomPersistence
    __all__ = ["CustomPersistence"]

Task 6: Update main.py imports
  FILE: src/main.py
  ACTION: MODIFY import statement
  FIND: "from src.services.redis import RedisPersistence"
  REPLACE: "from src.services.session import CustomPersistence"
  FIND: "persistence = RedisPersistence()"
  REPLACE: "persistence = CustomPersistence()"

Task 7: Update all handler imports (6 files)
  FILES:
    - src/handlers/booking_handler.py
    - src/handlers/feedback_handler.py
    - src/handlers/cancel_booking_handler.py
    - src/handlers/change_booking_date_handler.py
    - src/handlers/gift_certificate_handler.py
    - src/handlers/user_booking.py
  ACTION: MODIFY imports
  FIND: "from src.services.redis.redis_session_service import RedisSessionService"
  REPLACE: "from src.services.session.session_service import SessionService"
  FIND: "redis_service = RedisSessionService()"
  REPLACE: "session_service = SessionService()"
  FIND: "redis_service."
  REPLACE: "session_service."

Task 8: Update callback_recovery_service.py
  FILE: src/services/callback_recovery_service.py
  ACTION: MODIFY imports and usage
  FIND: "from src.services.redis.redis_session_service import RedisSessionService"
  REPLACE: "from src.services.session.session_service import SessionService"
  MODIFY: self.redis_service -> self.session_service

Task 9: Remove Redis configuration from config.py
  FILE: src/config/config.py
  ACTION: DELETE Redis-related variables
  DELETE_LINES: |
    Line 33: REDIS_URL = secret_manager_service.get_secret("REDIS_URL")
    Line 34: REDIS_PORT = int(secret_manager_service.get_secret("REDIS_PORT"))
    Line 35: REDIS_SSL = ...
    Line 53-55: Same for debug environment

Task 10: Update requirements.txt
  FILE: requirements.txt
  ACTION: REMOVE line
  FIND: "redis"
  DELETE: Remove this line entirely

Task 11: Delete Redis service files
  FILES_TO_DELETE:
    - src/services/redis/redis_connection.py
    - src/services/redis/redis_session_service.py
    - src/services/redis/redis_persistence.py
    - src/services/redis/__init__.py
  ACTION: DELETE directory
  COMMAND: rm -rf src/services/redis/

Task 12: Add session_storage.json to .gitignore
  FILE: .gitignore
  ACTION: ADD line at end
  CONTENT: |
    # Session storage
    session_storage.json
```

### Task 2 Pseudocode: Core SessionStore

```python
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
        self._storage: Dict[str, Dict] = {}        # In-memory storage
        self._lock = asyncio.Lock()                 # Concurrency control
        self._storage_file = Path(storage_file)
        self._cleanup_interval = cleanup_interval_days * 86400  # Convert to seconds
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
            # CRITICAL: Save to disk after every write for persistence
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

            # Check if expired
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
            # PATTERN: Atomic write - write to temp, then rename
            temp_file = self._storage_file.with_suffix('.tmp')

            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._storage, f, ensure_ascii=False, indent=2)

            # Atomic rename (overwrites existing file)
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
        # Run cleanup on startup
        await self._cleanup_expired()

        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                LoggerService.error(__name__, "Error in cleanup loop", exception=e)
```

### Task 3 Pseudocode: SessionService

```python
"""
Session service for managing bot user session data.
Exact API replacement for RedisSessionService.
"""
from datetime import timedelta
from typing import Optional
from singleton_decorator import singleton
from telegram import Update

from src.models.booking_draft import BookingDraft
from src.models.feedback import Feedback
from src.models.cancel_booking_draft import CancelBookingDraft
from src.models.change_booking_draft import ChangeBookingDraft
from src.models.gift_certificate_draft import GiftCertificateDraft
from src.models.user_booking_draft import UserBookingDraft
from src.services.navigation_service import NavigationService
from src.services.session.session_store import SessionStore
from src.services.logger_service import LoggerService
from src.constants import (
    SESSION_STORAGE_FILE,
    SESSION_TTL_DAYS,
    CLEANUP_INTERVAL_DAYS
)


@singleton
class SessionService:
    """
    Manages session data for Telegram bot users.
    Drop-in replacement for RedisSessionService.
    """

    def __init__(self, ttl_days: int = SESSION_TTL_DAYS):
        """
        Initialize session service.

        Args:
            ttl_days: Time-to-live for stored data in days (default: 5)
        """
        self._store = SessionStore(
            storage_file=SESSION_STORAGE_FILE,
            cleanup_interval_days=CLEANUP_INTERVAL_DAYS
        )
        self._ttl_seconds = int(timedelta(days=ttl_days).total_seconds())
        self._navigation_service = NavigationService()

        # CRITICAL: Start the store (must be called from async context)
        # This will be handled in main.py during application initialization
        LoggerService.info(__name__, f"SessionService initialized with TTL={ttl_days} days")

    async def initialize(self) -> None:
        """Initialize the underlying storage. Call from main.py."""
        await self._store.start()

    async def shutdown(self) -> None:
        """Shutdown the storage. Call from main.py cleanup."""
        await self._store.stop()

    # ============ Booking Operations ============
    # PATTERN: All methods preserve exact same signature as RedisSessionService

    async def init_booking(self, update: Update) -> None:
        """Initialize a new booking session for the user."""
        await self.clear_booking(update)
        await self.set_booking(update, BookingDraft())

    async def set_booking(self, update: Update, booking: BookingDraft) -> None:
        """Store booking object."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"booking:{chat_id}"
            # PATTERN: Use to_json() from dataclass_json
            await self._store.set(key, booking.to_json(), self._ttl_seconds)
        except Exception as e:
            LoggerService.error(__name__, "Failed to save booking", exception=e)

    async def get_booking(self, update: Update) -> Optional[BookingDraft]:
        """Retrieve booking object."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"booking:{chat_id}"
            data = await self._store.get(key)
            if data:
                # PATTERN: Use from_json() from dataclass_json
                return BookingDraft.from_json(data)
            return None
        except Exception as e:
            LoggerService.error(__name__, "Failed to get booking", exception=e)
            return None

    async def update_booking_field(self, update: Update, field: str, value) -> None:
        """Update a single field in booking object."""
        try:
            booking = await self.get_booking(update)
            if not booking:
                booking = BookingDraft()

            value = self._cast_field(field, value)
            setattr(booking, field, value)
            await self.set_booking(update, booking)
        except Exception as e:
            LoggerService.error(__name__, f"Failed to update booking field: {field}", exception=e)

    async def clear_booking(self, update: Update) -> None:
        """Clear booking data."""
        try:
            chat_id = self._get_chat_id(update)
            key = f"booking:{chat_id}"
            await self._store.delete(key)
        except Exception as e:
            LoggerService.error(__name__, "Failed to clear booking", exception=e)

    # ============ Feedback Operations ============
    # PATTERN: Same as booking - init, set, get, update, clear

    async def init_feedback(self, update: Update) -> None:
        await self.clear_feedback(update)
        await self.set_feedback(update, Feedback())

    # ... [Similar methods for feedback, cancel_booking, change_booking,
    #      gift_certificate, user_booking]

    # ============ Helper Methods ============

    def _get_chat_id(self, update: Update) -> int:
        """Extract chat_id from Update object."""
        return self._navigation_service.get_chat_id(update)

    def _cast_field(self, field: str, value):
        """Cast field values to appropriate types."""
        # PRESERVE: Exact same logic as RedisSessionService
        if field in ["start_date", "end_date"]:
            return datetime.fromisoformat(value) if isinstance(value, str) else value
        elif field == "tariff":
            return Tariff[value] if isinstance(value, str) else value
        else:
            return value
```

### Task 4 Pseudocode: CustomPersistence

```python
"""
Custom persistence for Telegram bot conversation states.
Replaces RedisPersistence using SessionStore.
"""
import json
from typing import Dict, Optional, Tuple
from telegram.ext import BasePersistence, PersistenceInput
from telegram.ext._utils.types import ConversationDict, CDCData

from src.services.session.session_store import SessionStore
from src.services.logger_service import LoggerService
from src.constants import SESSION_STORAGE_FILE, CONVERSATION_TTL_DAYS


class CustomPersistence(BasePersistence):
    """
    Stores Telegram conversation states.
    Drop-in replacement for RedisPersistence.
    """

    def __init__(self):
        super().__init__(
            store_data=PersistenceInput(
                user_data=False,
                chat_data=False,
                bot_data=False,
                callback_data=False,
            ),
            update_interval=1.0,
        )
        self._store = SessionStore(
            storage_file=SESSION_STORAGE_FILE,
            cleanup_interval_days=5  # Same cleanup interval
        )
        self._conversations: Dict[str, ConversationDict] = {}
        self._conversation_key_prefix = "conversation_state"
        self._ttl_seconds = SESSION_TTL_DAYS * 86400  # 5 days in seconds

    async def initialize(self) -> None:
        """Initialize storage. Called by telegram.ext."""
        await self._store.start()

    async def get_conversations(self, name: str) -> ConversationDict:
        """Retrieve conversation states."""
        try:
            key = f"{self._conversation_key_prefix}:{name}"
            data = await self._store.get(key)

            if data:
                raw_dict = json.loads(data)
                result = {}

                # PATTERN: Convert "chat_id,user_id" back to (chat_id, user_id)
                for key_str, state in raw_dict.items():
                    parts = key_str.split(",")
                    if len(parts) == 2:
                        conversation_key = (int(parts[0]), int(parts[1]))
                        result[conversation_key] = state

                LoggerService.info(
                    __name__,
                    f"Loaded {len(result)} conversation states for '{name}'"
                )
                return result

            return {}
        except Exception as e:
            LoggerService.error(__name__, f"Failed to load conversations for '{name}'", exception=e)
            return {}

    async def update_conversation(
        self, name: str, key: Tuple[int, ...], new_state: Optional[object]
    ) -> None:
        """Update conversation state."""
        try:
            redis_key = f"{self._conversation_key_prefix}:{name}"

            # Get existing conversations
            existing_data = await self._store.get(redis_key)
            conversations = json.loads(existing_data) if existing_data else {}

            # PATTERN: Convert tuple to string for JSON
            key_str = ",".join(map(str, key))

            if new_state is None:
                conversations.pop(key_str, None)
            else:
                conversations[key_str] = new_state

            # Save back
            await self._store.set(
                redis_key,
                json.dumps(conversations),
                self._ttl_seconds
            )

        except Exception as e:
            LoggerService.error(
                __name__,
                f"Failed to update conversation '{name}'",
                exception=e
            )

    # ... [Other BasePersistence methods that return empty/None]
```

### Integration Points

```yaml
MAIN_APPLICATION:
  file: src/main.py
  changes:
    - "Import CustomPersistence instead of RedisPersistence"
    - "Initialize persistence and call await persistence.initialize()"
    - "Add shutdown handler to call await persistence.shutdown()"

HANDLERS:
  files:
    - src/handlers/booking_handler.py
    - src/handlers/feedback_handler.py
    - src/handlers/cancel_booking_handler.py
    - src/handlers/change_booking_date_handler.py
    - src/handlers/gift_certificate_handler.py
    - src/handlers/user_booking.py
  changes:
    - "Change import from redis_session_service to session_service"
    - "Rename redis_service to session_service"
    - "Add 'await' keyword to all session_service calls"

CONSTANTS:
  file: src/constants.py
  add:
    - SESSION_STORAGE_FILE: "session_storage.json"
    - SESSION_TTL_DAYS: 5  # Все записи живут 5 суток
    - CLEANUP_INTERVAL_DAYS: 5  # Очистка каждые 5 суток

CONFIG:
  file: src/config/config.py
  remove:
    - REDIS_URL, REDIS_PORT, REDIS_SSL variables from both production and debug sections

REQUIREMENTS:
  file: requirements.txt
  remove:
    - "redis" dependency line

GITIGNORE:
  file: .gitignore
  add:
    - "session_storage.json"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# CRITICAL: Run these FIRST before any testing
cd /c/projects/secret-house-booking-bot

# Check syntax and style
ruff check src/services/session/ --fix
ruff check src/handlers/ --fix
ruff check src/main.py --fix

# Expected: No errors. Fix any issues before proceeding.
```

### Level 2: Import Validation
```bash
# Verify no Redis imports remain
rg "import redis" src/
rg "from.*redis" src/
rg "RedisSessionService" src/
rg "RedisPersistence" src/

# Expected: Only historical references in git history, no active imports
```

### Level 3: Application Startup Test
```bash
# Start the application and check for errors
cd /c/projects/secret-house-booking-bot
python src/main.py

# Expected output:
# - "SessionStore started with file: session_storage.json"
# - "SessionService initialized with TTL=5 days"
# - "Application initialized with CustomPersistence for conversation states"
# - No Redis connection errors
# - Bot starts polling successfully

# Check that session_storage.json file is created
ls -la session_storage.json
# Expected: File exists and is valid JSON
```

### Level 4: Manual Integration Tests
```bash
# Follow MANUAL_TESTING_GUIDE.md completely
# Focus on these critical workflows:

1. BOOKING WORKFLOW (booking_handler.py - most complex)
   - Start new booking
   - Select tariff
   - Choose dates
   - Add extras (sauna, photoshoot)
   - Enter contact
   - Confirm booking
   - VERIFY: All data persists between steps

2. RESTART TEST (persistence validation)
   - Start booking workflow, get halfway through
   - Stop application (Ctrl+C)
   - Restart application
   - Continue workflow
   - VERIFY: Session data was restored from JSON file

3. FEEDBACK WORKFLOW (feedback_handler.py)
   - Complete feedback questionnaire
   - VERIFY: All answers persist between questions

4. CONVERSATION STATE TEST (RedisPersistence replacement)
   - Enter conversation handler
   - Check conversation state persists
   - VERIFY: Bot remembers conversation position after restart

5. CLEANUP TEST (automatic expiration)
   - Manually set created_at timestamp to 10 days ago in session_storage.json
   - Wait for cleanup task or restart bot
   - VERIFY: Old records (> 5 суток) are removed from storage
```

### Level 5: Load Test (Optional but Recommended)
```bash
# Simulate multiple concurrent users
# PATTERN: Run multiple telegram interactions simultaneously

# Expected: No race conditions, all data saved correctly
# Verify with:
cat session_storage.json | python -m json.tool
# Should show all user sessions with proper structure
```

## Final Validation Checklist

- [ ] Application starts without Redis connection errors
- [ ] session_storage.json file is created
- [ ] Booking workflow completes successfully
- [ ] Data persists between application restarts
- [ ] Feedback workflow works correctly
- [ ] Conversation states are preserved
- [ ] Old records are cleaned up after 5 days
- [ ] No Redis imports remain in codebase
- [ ] redis dependency removed from requirements.txt
- [ ] All manual tests from MANUAL_TESTING_GUIDE.md pass
- [ ] No performance degradation observed
- [ ] File writes are atomic (no corrupted JSON)
- [ ] Concurrent user sessions don't interfere with each other

## Anti-Patterns to Avoid

- ❌ Don't use threading.Lock() - must use asyncio.Lock()
- ❌ Don't forget 'await' keyword on all async session_service methods
- ❌ Don't skip file persistence on writes - data must survive restarts
- ❌ Don't use blocking file I/O - use async file operations if possible
- ❌ Don't change method signatures - must maintain API compatibility
- ❌ Don't catch all exceptions silently - log errors properly
- ❌ Don't skip atomic file writes - use temp file + rename pattern
- ❌ Don't forget to initialize/shutdown store in main.py
- ❌ Don't skip cleanup task - old data must be removed automatically
- ❌ Don't remove @singleton decorator from SessionService

## Performance Considerations

1. **File I/O on every write**: Current implementation saves to disk on every write
   - This is acceptable for Telegram bot use case (low write frequency)
   - If performance becomes issue, can add write batching later

2. **Lock contention**: asyncio.Lock() is used for all operations
   - Single lock is fine for single-instance bot
   - No need for fine-grained locking

3. **JSON parsing**: Loading/dumping JSON on every operation
   - Acceptable overhead for current data sizes
   - dataclass_json already handles this in current code

4. **Cleanup task**: Runs every 5 days by default
   - Configurable via CLEANUP_INTERVAL_DAYS constant
   - Can be adjusted if needed

## Migration Notes

- **Zero downtime migration**: Not possible - requires application restart
- **Data loss**: All active sessions will be lost on first migration
  - This is acceptable - Redis data has short TTL anyway
  - Users will need to restart their booking workflows
- **TTL change**: Old system had 24h/3d TTL, new system uses unified 5 суток
  - This is BETTER for users - more time to complete workflows
- **Rollback plan**: Keep Redis dependency commented out in requirements.txt for 1 week
  - If issues arise, can quickly revert changes
- **No database migration needed**: Draft data never goes to PostgreSQL

---

## Confidence Score: 8/10

**Reasoning:**

**Strengths (+8):**
- Clear API compatibility with existing RedisSessionService
- All context provided (183 Redis operations mapped)
- Exact same dataclass_json serialization pattern
- Comprehensive validation gates with manual testing guide
- Atomic file writes prevent data corruption
- Background cleanup task handles expiration
- asyncio.Lock ensures concurrency safety

**Risks (-2):**
- File I/O performance on every write (mitigated: low write frequency in bot)
- No unit tests specified (mitigated: comprehensive manual testing guide exists)
- First-time deployment will lose active sessions (mitigated: acceptable by user, 24h TTL)

**Overall:** High confidence for one-pass implementation success. The comprehensive context, exact API mirroring, and detailed validation steps make this achievable. The main risk is ensuring all 183 Redis operations are converted with 'await' keywords, but the validation loop catches this.
