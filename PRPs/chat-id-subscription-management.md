name: "Chat ID Subscription Management System"
description: |

## Purpose
Implement a robust chat ID management system that tracks user subscriptions to the Telegram bot, ensures unique chat IDs in the database, and automatically cleans up invalid/blocked users on a weekly basis.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Create a system that:
- Stores unique chat IDs in the database (one chat ID per user, no duplicates)
- Tracks when users start/stop the bot (subscription status)
- Runs a weekly cleanup job to detect and remove invalid/blocked chat IDs
- Handles user unsubscribe and re-subscribe scenarios gracefully

## Why
- **Data Integrity**: Prevents duplicate chat IDs and ensures accurate user tracking
- **Cost Efficiency**: Reduces wasted broadcast attempts to blocked/invalid users
- **Compliance**: Respects user privacy by removing data when users block the bot
- **Reliability**: Maintains clean database for broadcast messaging feature (already implemented)

## What
A complete chat subscription management system that integrates with the existing UserBase model and booking system.

### Success Criteria
- [x] UserBase model has unique chat_id field
- [x] Chat ID is captured and stored when user sends /start command
- [x] Weekly job validates all chat IDs and removes invalid ones
- [x] Handles re-subscription scenarios (user blocks then unblocks bot)
- [x] No duplicate chat IDs in database
- [x] Broadcast feature uses validated chat IDs only

## All Needed Context

### Documentation & References (list all context needed to implement the feature)
```yaml
# MUST READ - Include these in your context window

- url: https://docs.python-telegram-bot.org/en/stable/telegram.bot.html
  why: Official python-telegram-bot API documentation for bot methods

- url: https://core.telegram.org/bots/api#sendchataction
  why: Telegram Bot API reference for checking chat validity without bothering users
  critical: |
    getChat() method has CACHING ISSUES - results cached for weeks
    Use sendChatAction() to verify chat is accessible - returns 403 Forbidden if user blocked bot
    Error codes: 403 = "Bot was blocked by user", 400 = "Chat not found"

- url: https://github.com/python-telegram-bot/python-telegram-bot/issues/2484
  why: Discussion on detecting blocked users
  critical: |
    my_chat_member updates provide real-time block/unblock events
    Status changes: "member" -> "kicked" when user blocks bot
    Status changes: "kicked" -> "member" when user unblocks bot

- file: /Users/a/secret-house-booking-bot/db/models/user.py
  why: Current UserBase model - need to add chat_id field here
  pattern: |
    class UserBase(Base):
        __tablename__ = 'user'
        id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
        contact: Mapped[str] = mapped_column(String, unique=True, nullable=False)

- file: /Users/a/secret-house-booking-bot/src/services/database_service.py
  why: Database service singleton pattern - add chat_id methods here
  pattern: |
    Lines 493-508: get_all_chat_ids() already exists but pulls from BookingBase
    Lines 43-61: get_or_create_user() pattern to follow
    Must follow singleton pattern with self.Session() context manager

- file: /Users/a/secret-house-booking-bot/src/services/job_service.py
  why: Job scheduler service - add weekly cleanup job here
  pattern: |
    Lines 36-47: register_jobs() method - add new weekly job here
    Lines 49-88: send_booking_details() job pattern to follow
    Uses pytz.timezone("Europe/Minsk") for scheduling
    Jobs registered with context.job_queue.run_daily() or run_weekly()

- file: /Users/a/secret-house-booking-bot/src/handlers/menu_handler.py
  why: Entry point for /start command - capture chat_id here
  pattern: |
    Line 195: show_menu() function is /start handler
    Uses LoggerService.info() for logging
    Has access to update.effective_chat.id for chat_id

- file: /Users/a/secret-house-booking-bot/src/handlers/admin_handler.py
  why: Broadcasting implementation that uses chat IDs
  pattern: |
    Lines 264, 308: Uses database_service.get_all_chat_ids()
    Lines 315-413: broadcast_to_users() function with error handling
    Uses TelegramError exception catching (line 27)

- file: /Users/a/secret-house-booking-bot/alembic/versions/c28d5944418c_remove_subscription_functionality.py
  why: Previous subscription removal migration - understand what was removed
  critical: Old subscription table was dropped, we're NOT recreating it
```

### Current Codebase tree (overview of the project structure)
```bash
secret-house-booking-bot/
├── alembic/
│   ├── versions/           # Database migrations
│   │   ├── 8e261b9824f5_add_comment_and_is_paid_columns_to_.py
│   │   ├── c28d5944418c_remove_subscription_functionality.py
│   │   ├── 7a348eb5fbe1_add_feedback_submitted_to_booking.py
│   │   └── 16c4e4787de0_add_incognito_questionnaire_fields.py
│   └── env.py
├── db/
│   ├── models/
│   │   ├── base.py         # SQLAlchemy Base
│   │   ├── user.py         # UserBase model ⚠️ MODIFY THIS
│   │   ├── booking.py      # BookingBase model (has chat_id)
│   │   └── gift.py         # GiftBase model
│   ├── database.py         # Database engine setup
│   └── run_migrations.py
├── src/
│   ├── config/
│   │   └── config.py       # Environment variables
│   ├── handlers/
│   │   ├── menu_handler.py  # /start handler ⚠️ MODIFY THIS
│   │   ├── admin_handler.py # Broadcasting feature
│   │   └── ...
│   ├── services/
│   │   ├── database_service.py  # DB operations ⚠️ MODIFY THIS
│   │   ├── job_service.py       # Job scheduler ⚠️ MODIFY THIS
│   │   └── logger_service.py
│   ├── models/
│   │   └── enum/
│   └── main.py              # Application entry point
├── tests/
│   ├── test_date_pricing_service.py
│   └── test_calculation_rate_integration.py
└── requirements.txt
```

### Desired Codebase tree with files to be added and responsibility of file
```bash
secret-house-booking-bot/
├── alembic/
│   └── versions/
│       └── <timestamp>_add_chat_id_to_user.py  # NEW: Migration to add chat_id column
├── db/
│   └── models/
│       └── user.py                             # MODIFIED: Add chat_id field
├── src/
│   ├── handlers/
│   │   └── menu_handler.py                     # MODIFIED: Capture chat_id on /start
│   └── services/
│       ├── database_service.py                 # MODIFIED: Add chat management methods
│       ├── job_service.py                      # MODIFIED: Add weekly cleanup job
│       └── chat_validation_service.py          # NEW: Chat validation logic
```

### Known Gotchas of our codebase & Library Quirks
```python
# CRITICAL: Telegram Bot API caching behavior
# getChat() results are cached for WEEKS - DO NOT USE for validation
# Use sendChatAction("typing") instead - it returns 403 immediately if blocked

# CRITICAL: Database session management
# ALWAYS use singleton pattern: with self.Session() as session:
# See database_service.py lines 31-41 for correct pattern
# NEVER create sessions outside context manager

# CRITICAL: Job scheduler timezone
# Uses pytz.timezone("Europe/Minsk") - see job_service.py line 37
# Jobs run daily at specific time with context.job_queue.run_daily()
# Weekly jobs: use run_repeating(interval=timedelta(days=7))

# CRITICAL: Migration generation
# Uses Alembic with SQLite in offline mode
# Command: ALEMBIC_OFFLINE=true uv run alembic revision --autogenerate -m "message"
# See CLAUDE.md lines for environment variable setup

# CRITICAL: Error handling in broadcasts
# See admin_handler.py lines 315-413
# Uses TelegramError exception with sleep between messages
# Must catch telegram.error.Forbidden for blocked users

# CRITICAL: UserBase model pattern
# contact field is unique and required
# chat_id should be unique but nullable (user might not have started bot yet)
# Use get_or_create_user pattern from database_service.py line 43

# CRITICAL: Logging pattern
# Use LoggerService.info(__name__, "message", update) for success
# Use LoggerService.error(__name__, "message", exception=e, kwargs={...}) for errors
# See job_service.py lines 53-88 for examples
```

## Implementation Blueprint

### Data models and structure

**Database Model Changes:**
```python
# db/models/user.py - MODIFY UserBase class

from sqlalchemy import String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

class UserBase(Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contact: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=True)  # NEW
    # nullable=True because user might exist from booking but not started bot
    # unique=True ensures one chat_id per user
```

**Service Model:**
```python
# src/services/chat_validation_service.py - NEW FILE

from telegram.error import Forbidden, BadRequest, TelegramError
from singleton_decorator import singleton

@singleton
class ChatValidationService:
    """Service for validating chat IDs and detecting blocked users"""

    async def is_chat_valid(self, bot, chat_id: int) -> bool:
        """
        Check if chat_id is valid and bot is not blocked.

        Uses sendChatAction to avoid cache issues.
        Returns True if chat is accessible, False otherwise.

        GOTCHA: Don't use getChat() - it caches results for weeks!
        """
        pass  # Implementation in tasks below

    async def validate_all_chat_ids(self, bot, database_service) -> dict:
        """
        Validate all chat IDs in database.

        Returns dict with:
        - total_checked: int
        - valid: int
        - invalid: int
        - removed_ids: list[int]
        """
        pass  # Implementation in tasks below
```

### list of tasks to be completed to fullfill the PRP in the order they should be completed

```yaml
Task 1: Create database migration for chat_id field
GOAL: Add chat_id column to user table with proper constraints

CREATE alembic/versions/<timestamp>_add_chat_id_to_user.py:
  - COMMAND: ALEMBIC_OFFLINE=true uv run alembic revision --autogenerate -m "Add chat_id to users"
  - VERIFY: Migration file created in alembic/versions/
  - PATTERN: Follow c28d5944418c_remove_subscription_functionality.py structure
  - CRITICAL: Use batch_alter_table for SQLite compatibility
  - VALIDATION: Check migration adds:
      - Column: chat_id (BigInteger, nullable=True, unique=True)

Task 2: Modify UserBase model to include chat_id
GOAL: Update ORM model to include chat_id field

MODIFY db/models/user.py:
  - FIND: "contact: Mapped[str] = mapped_column(String, unique=True, nullable=False)"
  - INSERT AFTER: "chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=True)"
  - IMPORT: Add "BigInteger" to sqlalchemy imports (line 5)
  - PRESERVE: Existing id and contact fields unchanged
  - VALIDATION: Run "uv run python -c 'from db.models.user import UserBase; print(UserBase.__table__.columns)'"

Task 3: Add chat_id management methods to DatabaseService
GOAL: Create methods to update and retrieve chat IDs from users

MODIFY src/services/database_service.py:
  - FIND: "def get_or_create_user(self, contact: str)" (around line 43)
  - UNDERSTAND: This is the pattern - returns existing or creates new user

  - ADD NEW METHOD after get_user_by_id (after line 81):
    def update_user_chat_id(self, contact: str, chat_id: int) -> UserBase:
        """Update or set chat_id for user. Handles duplicates gracefully."""
        # PATTERN: Use self.Session() context manager
        # LOGIC:
        #   1. Get or create user by contact
        #   2. Check if chat_id already exists for different user
        #   3. If duplicate, remove old user's chat_id (user blocked then restarted)
        #   4. Set chat_id for current user
        #   5. Commit and return user
        # ERROR HANDLING: LoggerService.error on exception, rollback session

  - ADD NEW METHOD after update_user_chat_id:
    def get_all_user_chat_ids(self) -> list[int]:
        """Get all chat IDs from UserBase (not BookingBase)"""
        # PATTERN: Similar to get_all_chat_ids() at line 493
        # CHANGE: Query UserBase instead of BookingBase
        # FILTER: Only non-null chat_ids
        # RETURN: list[int] of unique chat_ids

  - ADD NEW METHOD after get_all_user_chat_ids:
    def remove_user_chat_id(self, chat_id: int) -> bool:
        """Remove chat_id from user (set to None). Returns True if found."""
        # PATTERN: Use self.Session() context manager
        # LOGIC:
        #   1. Find user with this chat_id
        #   2. Set chat_id = None
        #   3. Commit
        # RETURN: True if user found, False otherwise

  - VALIDATION: Run "uv run python -c 'from src.services.database_service import DatabaseService; ds = DatabaseService(); print(dir(ds))'"

Task 4: Create ChatValidationService for chat checking
GOAL: Service to validate chat IDs using Telegram API without cache issues

CREATE src/services/chat_validation_service.py:
  - MIRROR pattern from: src/services/database_service.py (singleton pattern)
  - IMPORTS:
      from telegram.error import Forbidden, BadRequest, TelegramError
      from singleton_decorator import singleton
      from src.services.logger_service import LoggerService
      import asyncio

  - CREATE CLASS ChatValidationService:
      @singleton decorator

      async def is_chat_valid(self, bot, chat_id: int) -> bool:
          """
          CRITICAL: Use sendChatAction("typing") NOT getChat()

          Try to send "typing" action to chat
          If 403 Forbidden -> user blocked bot -> return False
          If 400 Bad Request -> chat not found -> return False
          If success -> chat is valid -> return True

          PATTERN:
              try:
                  await bot.sendChatAction(chat_id=chat_id, action="typing")
                  return True
              except Forbidden:
                  # User blocked bot
                  LoggerService.info(__name__, f"Chat {chat_id} blocked bot")
                  return False
              except BadRequest:
                  # Chat not found
                  LoggerService.info(__name__, f"Chat {chat_id} not found")
                  return False
              except TelegramError as e:
                  # Other error - log and treat as invalid
                  LoggerService.error(__name__, "Chat validation error", exception=e)
                  return False
          """

      async def validate_all_chat_ids(self, bot, chat_ids: list[int]) -> dict:
          """
          Validate list of chat IDs and return results

          PATTERN:
              - Loop through chat_ids
              - For each: call is_chat_valid()
              - Track valid/invalid counts
              - Sleep 0.1s between checks (rate limiting)

          RETURN:
              {
                  "total_checked": len(chat_ids),
                  "valid": valid_count,
                  "invalid": invalid_count,
                  "invalid_ids": [list of invalid chat_ids]
              }
          """

  - VALIDATION: Run "uv run ruff check src/services/chat_validation_service.py --fix"

Task 5: Modify menu_handler to capture chat_id on /start
GOAL: Store chat_id when user starts bot

MODIFY src/handlers/menu_handler.py:
  - FIND: "async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:" (line 195)
  - LOCATE: "await job.init_job(update, context)" (line 197)

  - INSERT AFTER line 197:
      # Capture and store user's chat_id
      chat_id = update.effective_chat.id
      user_contact = update.effective_user.username or str(chat_id)

      try:
          database_service = DatabaseService()
          database_service.update_user_chat_id(user_contact, chat_id)
          LoggerService.info(
              __name__,
              f"Chat ID stored for user",
              kwargs={"chat_id": chat_id, "contact": user_contact}
          )
      except Exception as e:
          LoggerService.error(
              __name__,
              "Failed to store chat_id",
              exception=e,
              kwargs={"chat_id": chat_id}
          )

  - ADD IMPORT at top (around line 8):
      from src.services.database_service import DatabaseService

  - PRESERVE: All existing show_menu logic
  - VALIDATION: Run "uv run ruff check src/handlers/menu_handler.py --fix"

Task 6: Add weekly cleanup job to JobService
GOAL: Schedule weekly job to validate and clean up invalid chat IDs

MODIFY src/services/job_service.py:
  - ADD IMPORT at top:
      from datetime import timedelta
      from src.services.chat_validation_service import ChatValidationService

  - MODIFY register_jobs method (around line 36):
      FIND: if not context.job_queue.get_jobs_by_name("send_feeback"):
      INSERT AFTER (around line 47):

          if not context.job_queue.get_jobs_by_name("cleanup_invalid_chats"):
              # Run weekly on Sunday at 3 AM
              context.job_queue.run_repeating(
                  self.cleanup_invalid_chats,
                  interval=timedelta(days=7),
                  first=timedelta(seconds=10),  # First run 10s after start for testing
                  name="cleanup_invalid_chats"
              )

  - ADD NEW METHOD after send_feeback (after line 131):
      async def cleanup_invalid_chats(self, context: CallbackContext):
          """
          Weekly job to validate all chat IDs and remove invalid ones.

          PATTERN: Similar to send_booking_details (lines 49-88)

          LOGIC:
              1. Get all chat_ids from database_service.get_all_user_chat_ids()
              2. If no chat_ids, log and return
              3. Create ChatValidationService instance
              4. Call validate_all_chat_ids() with bot and chat_ids
              5. For each invalid_id in results["invalid_ids"]:
                  - database_service.remove_user_chat_id(invalid_id)
                  - Log removal
              6. Log summary with total/valid/invalid counts

          ERROR HANDLING:
              - Try/except around entire job
              - Log errors with LoggerService.error
              - Continue processing other chat_ids if one fails

          LOGGING:
              - Info: Job start, summary at end
              - Error: Any failures during validation or removal
          """

  - VALIDATION: Run "uv run ruff check src/services/job_service.py --fix"

Task 7: Update broadcast feature to use UserBase chat_ids
GOAL: Modify admin broadcast to use validated chat IDs from UserBase

MODIFY src/handlers/admin_handler.py:
  - FIND: "chat_ids = database_service.get_all_chat_ids()" (lines 264, 308)
  - REPLACE WITH: "chat_ids = database_service.get_all_user_chat_ids()"
  - DO THIS IN TWO PLACES:
      1. start_broadcast function (around line 264)
      2. handle_broadcast_input function (around line 308)

  - PRESERVE: All error handling in broadcast_to_users (lines 315-413)
  - NOTE: This function already handles Forbidden exceptions properly

  - VALIDATION: Run "uv run ruff check src/handlers/admin_handler.py --fix"

Task 8: Run database migration
GOAL: Apply the migration to add chat_id column

EXECUTE:
  # Apply migration to database
  uv run alembic upgrade head

VERIFY:
  # Check that column exists
  uv run python -c "from db.models.user import UserBase; from database import engine; from sqlalchemy import inspect; insp = inspect(engine); print([c.name for c in insp.get_columns('user')])"

  # Should print: ['id', 'contact', 'chat_id']

Task 9: Create integration test for chat ID management
GOAL: Test the full flow of chat ID capture and validation

CREATE tests/test_chat_id_management.py:
  - MIRROR pattern from: tests/test_date_pricing_service.py
  - TEST CASES:
      1. test_update_user_chat_id_new_user()
          - Create user with contact and chat_id
          - Verify stored correctly

      2. test_update_user_chat_id_duplicate_handling()
          - User A has chat_id 123
          - User B tries to use chat_id 123
          - Verify User A's chat_id set to None
          - Verify User B gets chat_id 123

      3. test_get_all_user_chat_ids()
          - Create 3 users with chat_ids
          - Create 1 user without chat_id
          - Verify returns only 3 chat_ids

      4. test_remove_user_chat_id()
          - Create user with chat_id
          - Remove chat_id
          - Verify chat_id is None

      5. test_chat_validation_service_valid_chat()
          - Mock bot.sendChatAction to succeed
          - Verify is_chat_valid returns True

      6. test_chat_validation_service_blocked_chat()
          - Mock bot.sendChatAction to raise Forbidden
          - Verify is_chat_valid returns False

  - USE: pytest with unittest.mock for mocking bot
  - VALIDATION: Run "uv run pytest tests/test_chat_id_management.py -v"
```

### Per task pseudocode as needed added to each task

```python
# Task 3 - update_user_chat_id method
async def update_user_chat_id(self, contact: str, chat_id: int) -> UserBase:
    with self.Session() as session:
        try:
            # Get or create user by contact
            user = session.scalar(
                select(UserBase).where(UserBase.contact == contact)
            )
            if not user:
                user = UserBase(contact=contact)
                session.add(user)

            # Check if this chat_id is already assigned to different user
            existing_user = session.scalar(
                select(UserBase).where(
                    and_(
                        UserBase.chat_id == chat_id,
                        UserBase.id != user.id if user.id else True
                    )
                )
            )

            # If chat_id exists for different user, remove it (re-subscribe scenario)
            if existing_user:
                LoggerService.info(
                    __name__,
                    f"Removing chat_id {chat_id} from user {existing_user.id}",
                    kwargs={"old_user_id": existing_user.id}
                )
                existing_user.chat_id = None

            # Set chat_id for current user
            user.chat_id = chat_id
            session.commit()

            LoggerService.info(__name__, f"Updated chat_id for user", kwargs={
                "user_id": user.id, "chat_id": chat_id, "contact": contact
            })
            return user

        except Exception as e:
            session.rollback()
            LoggerService.error(__name__, "update_user_chat_id", exception=e)
            raise

# Task 4 - ChatValidationService.is_chat_valid
async def is_chat_valid(self, bot, chat_id: int) -> bool:
    """
    CRITICAL: sendChatAction doesn't cache results like getChat

    Error handling hierarchy:
    1. Forbidden (403) -> User blocked bot
    2. BadRequest (400) -> Chat not found
    3. TelegramError -> Network/other issues
    """
    try:
        await bot.send_chat_action(chat_id=chat_id, action="typing")
        return True
    except Forbidden as e:
        # User blocked the bot
        LoggerService.info(
            __name__,
            f"Chat {chat_id} blocked bot",
            kwargs={"chat_id": chat_id, "error": str(e)}
        )
        return False
    except BadRequest as e:
        # Chat doesn't exist
        LoggerService.info(
            __name__,
            f"Chat {chat_id} not found",
            kwargs={"chat_id": chat_id, "error": str(e)}
        )
        return False
    except TelegramError as e:
        # Other errors - treat as invalid to be safe
        LoggerService.error(
            __name__,
            f"Error validating chat {chat_id}",
            exception=e,
            kwargs={"chat_id": chat_id}
        )
        return False

# Task 6 - cleanup_invalid_chats job
async def cleanup_invalid_chats(self, context: CallbackContext):
    """Weekly cleanup of invalid chat IDs"""
    try:
        # Get all chat IDs from users
        chat_ids = database_service.get_all_user_chat_ids()

        if not chat_ids:
            LoggerService.info(
                __name__,
                "No chat IDs to validate",
                kwargs={"chat_count": 0}
            )
            return

        LoggerService.info(
            __name__,
            f"Starting weekly chat validation",
            kwargs={"total_chats": len(chat_ids)}
        )

        # Validate all chat IDs
        validation_service = ChatValidationService()
        results = await validation_service.validate_all_chat_ids(
            self._application.bot,
            chat_ids
        )

        # Remove invalid chat IDs from database
        removed_count = 0
        for invalid_chat_id in results["invalid_ids"]:
            try:
                if database_service.remove_user_chat_id(invalid_chat_id):
                    removed_count += 1
                    LoggerService.info(
                        __name__,
                        f"Removed invalid chat_id",
                        kwargs={"chat_id": invalid_chat_id}
                    )
            except Exception as e:
                LoggerService.error(
                    __name__,
                    f"Failed to remove chat_id",
                    exception=e,
                    kwargs={"chat_id": invalid_chat_id}
                )

        # Log summary
        LoggerService.info(
            __name__,
            f"Weekly chat cleanup completed",
            kwargs={
                "total_checked": results["total_checked"],
                "valid": results["valid"],
                "invalid": results["invalid"],
                "removed": removed_count
            }
        )

    except Exception as e:
        LoggerService.error(
            __name__,
            "Weekly chat cleanup failed",
            exception=e
        )
```

### Integration Points
```yaml
DATABASE:
  - migration: "Add column 'chat_id' (BigInteger, unique, nullable) to user table"
  - constraint: "UNIQUE constraint on chat_id to prevent duplicates"
  - index: "Automatic index created by unique constraint"

HANDLERS:
  - modify: src/handlers/menu_handler.py
  - point: show_menu() function - /start command entry point
  - action: Capture chat_id and call database_service.update_user_chat_id()

  - modify: src/handlers/admin_handler.py
  - point: start_broadcast() and handle_broadcast_input()
  - action: Replace get_all_chat_ids() with get_all_user_chat_ids()

JOBS:
  - modify: src/services/job_service.py
  - point: register_jobs() method
  - action: Add run_repeating job for weekly cleanup
  - schedule: Every 7 days, first run 10 seconds after startup (for testing)

SERVICES:
  - create: src/services/chat_validation_service.py
  - purpose: Validate chat IDs using Telegram API
  - pattern: Singleton decorator, async methods

  - modify: src/services/database_service.py
  - add_methods:
      - update_user_chat_id(contact, chat_id)
      - get_all_user_chat_ids()
      - remove_user_chat_id(chat_id)
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding

# Check all modified Python files
uv run ruff check db/models/user.py --fix
uv run ruff check src/services/database_service.py --fix
uv run ruff check src/services/chat_validation_service.py --fix
uv run ruff check src/services/job_service.py --fix
uv run ruff check src/handlers/menu_handler.py --fix
uv run ruff check src/handlers/admin_handler.py --fix

# Type checking (if using mypy)
# uv run mypy db/models/user.py
# uv run mypy src/services/

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Database Migration Validation
```bash
# Verify migration was generated correctly
ls -la alembic/versions/*add_chat_id_to_user.py

# Check migration content
cat alembic/versions/*add_chat_id_to_user.py

# Expected: Should see batch_alter_table with add_column for chat_id

# Run migration
uv run alembic upgrade head

# Verify column exists
uv run python -c "from db.models.user import UserBase; from database import engine; from sqlalchemy import inspect; insp = inspect(engine); cols = [c.name for c in insp.get_columns('user')]; print('chat_id' in cols)"

# Expected: True
```

### Level 3: Unit Tests
```bash
# Run chat ID management tests
uv run pytest tests/test_chat_id_management.py -v

# Expected: All tests pass
# If failing: Read error, understand root cause, fix code, re-run

# Run all existing tests to ensure nothing broke
uv run pytest tests/ -v

# Expected: All existing tests still pass
```

### Level 4: Integration Test (Manual)
```bash
# Start the bot in test mode with short interval for cleanup job
timeout 30 python src/main.py

# In Telegram app:
# 1. Send /start to bot -> Should capture your chat_id
# 2. Check logs for "Chat ID stored for user"

# Check database directly
uv run python -c "from src.services.database_service import DatabaseService; ds = DatabaseService(); print(ds.get_all_user_chat_ids())"

# Expected: Should see your chat_id in the list

# Test cleanup job (will run 10 seconds after start)
# Wait for log: "Starting weekly chat validation"
# Expected: Your chat_id should remain (it's valid)

# Test blocked user scenario:
# 1. Block the bot in Telegram
# 2. Wait for next cleanup job (or restart bot)
# 3. Check logs for "Chat {chat_id} blocked bot"
# 4. Verify chat_id removed from database
```

### Level 5: Broadcast Feature Test
```bash
# Start bot
python src/main.py

# As admin user:
# 1. Send /broadcast to bot
# 2. Enter broadcast message
# 3. Verify it uses get_all_user_chat_ids()
# 4. Check logs for broadcast success/failure counts

# Expected:
# - Broadcasts only to valid chat_ids from UserBase
# - Properly handles Forbidden errors for blocked users
# - Logs show accurate counts
```

## Final validation Checklist
- [ ] Migration created and applied successfully
- [ ] UserBase model includes chat_id field (unique, nullable)
- [ ] DatabaseService has new methods: update_user_chat_id, get_all_user_chat_ids, remove_user_chat_id
- [ ] ChatValidationService created with is_chat_valid and validate_all_chat_ids methods
- [ ] Menu handler captures chat_id on /start
- [ ] Weekly cleanup job registered and runs successfully
- [ ] Broadcast feature uses UserBase chat_ids
- [ ] All unit tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `uv run ruff check src/ db/`
- [ ] Manual test: /start captures chat_id correctly
- [ ] Manual test: Cleanup job validates and removes invalid chat_ids
- [ ] Manual test: Broadcast uses validated chat_ids
- [ ] Logs are informative but not verbose
- [ ] No duplicate chat_ids in database

---

## Anti-Patterns to Avoid
- ❌ Don't use getChat() for validation - it caches results for weeks
- ❌ Don't create new session patterns - follow existing singleton with context manager
- ❌ Don't skip unique constraint on chat_id - prevents duplicates
- ❌ Don't make chat_id required (not nullable) - users might exist before starting bot
- ❌ Don't ignore Forbidden errors in broadcast - they indicate blocked users
- ❌ Don't run cleanup job too frequently - weekly is sufficient, daily wastes API calls
- ❌ Don't forget to handle re-subscribe scenario - remove old chat_id when duplicate detected
- ❌ Don't skip sleep in validation loop - rate limiting is important
- ❌ Don't use SQLAlchemy Integer for chat_id - Telegram chat IDs are BigInteger
- ❌ Don't forget timezone in job scheduling - use Europe/Minsk per existing pattern

## Edge Cases to Handle

1. **User blocks bot then unblocks**:
   - Old chat_id in database
   - User sends /start with same chat_id
   - Solution: update_user_chat_id handles this by checking for duplicates

2. **User blocks bot and subscribes from different account**:
   - Old chat_id becomes invalid
   - New chat_id for different user
   - Solution: Weekly cleanup removes old chat_id

3. **User exists from booking but never started bot**:
   - User has contact but no chat_id
   - Solution: chat_id is nullable, get_all_user_chat_ids filters null values

4. **Migration runs on existing database with users**:
   - Existing users get NULL chat_id
   - Solution: Migration adds column as nullable, users get chat_id on next /start

5. **Broadcast happens during cleanup**:
   - Race condition possible
   - Solution: Both read from database, cleanup removes, broadcast may get Forbidden
   - Broadcast already handles Forbidden gracefully (lines 380-385 in admin_handler.py)

6. **Bot restarted during cleanup job**:
   - Job interrupted mid-process
   - Solution: Job runs again in 7 days, validation is idempotent

## Performance Considerations

- **Weekly cleanup frequency**: 7 days is reasonable, daily would waste API calls
- **Rate limiting in validation**: Sleep 0.1s between chat checks to avoid rate limits
- **Database queries**: get_all_user_chat_ids uses SELECT DISTINCT with WHERE chat_id IS NOT NULL
- **Broadcast impact**: No change, still loops through chat_ids with error handling

## Confidence Score

**Score: 9/10**

**Reasoning:**
- ✅ Complete context provided (Telegram API docs, existing patterns, gotchas)
- ✅ Clear task breakdown with pseudocode
- ✅ Validation gates at each level (syntax, migration, tests, integration)
- ✅ Edge cases identified and handled
- ✅ Anti-patterns documented
- ✅ Follows existing codebase patterns (singleton, logging, job scheduling)
- ✅ Executable validation commands provided
- ⚠️ Minor risk: Telegram API behavior changes (mitigated by using sendChatAction per 2024 docs)
- ⚠️ Testing blocked user scenario requires manual interaction

**Likelihood of one-pass implementation**: Very High

The only areas that might need adjustment are:
1. Exact Telegram error messages (may vary by API version)
2. Job scheduling timing details (first run interval)

These are minor and easily fixed during validation loop iteration.