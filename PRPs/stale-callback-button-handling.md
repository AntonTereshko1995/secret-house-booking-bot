# PRP: Handle Stale Callback Query Buttons After Bot Restart

## Goal
Implement robust callback query error handling to gracefully manage stale inline keyboard buttons that users click after the bot has been restarted or redeployed. Users should receive clear feedback instead of experiencing unresponsive buttons, and should be guided to refresh their menu state without manual intervention.

## Why
- **User Experience**: Currently, when the bot restarts (due to system updates, deployments, or crashes), users who click on inline keyboard buttons from before the restart experience unresponsive buttons. They must manually navigate to "Главное меню" to continue using the bot.
- **Business Value**: Reduces user frustration and support requests related to "broken buttons"
- **Technical Necessity**: Telegram callback queries expire after ~10-15 seconds, and any callback query from before a bot restart becomes invalid (error: "Query is too old and response timeout expired or query ID is invalid")
- **Automation**: Automatically detect stale buttons and either refresh the user's state or guide them back to a working state

## What
Implement a comprehensive callback query error handling system that:
1. Catches and gracefully handles `BadRequest` exceptions related to expired/invalid callback queries
2. Detects when buttons are from before a bot restart (stale state)
3. Automatically responds to users with helpful messages and options
4. Provides a fallback mechanism to restore user interaction without manual `/start` command
5. Optionally removes or disables stale inline keyboards to prevent confusion

### Success Criteria
- [ ] All callback query handlers gracefully handle `BadRequest` exceptions for expired queries
- [ ] Users receive clear, user-friendly messages when clicking stale buttons
- [ ] Automatic state recovery mechanism is implemented (either auto-refresh menu or provide quick action button)
- [ ] No unhandled exceptions in logs related to "query too old" or "invalid query ID"
- [ ] Solution works across all conversation handlers (booking, gift certificate, feedback, etc.)
- [ ] Logging properly distinguishes between expired queries (info level) and actual errors (error level)
- [ ] Users can continue their session without needing to manually type `/start`

## All Needed Context

### Documentation & References

```yaml
# MUST READ - Include these in your context window

- url: https://docs.python-telegram-bot.org/en/stable/telegram.error.html
  why: BadRequest exception handling and telegram error types
  critical: BadRequest is raised for "query too old" errors - must catch specifically

- url: https://docs.python-telegram-bot.org/en/stable/telegram.callbackquery.html
  why: CallbackQuery.answer() method and its timeout behavior
  critical: Must call answer() within ~10 seconds or query expires. After bot restart, all old queries are invalid.

- url: https://core.telegram.org/bots/api#callbackquery
  why: Telegram Bot API documentation on callback queries
  section: Understanding callback query lifecycle and expiration

- url: https://docs.python-telegram-bot.org/en/stable/telegram.ext.conversationhandler.html
  why: ConversationHandler state management and fallback handling
  critical: Fallbacks are triggered on errors - can use for recovery

- url: https://github.com/python-telegram-bot/python-telegram-bot/issues/2254
  why: Feature request and discussion about handling expired callback queries
  note: Community consensus is to catch BadRequest and check error message string

- url: https://stackoverflow.com/questions/58661909/bad-request-query-is-too-old-and-response-timeout-expired-or-query-id-is-invali
  why: Stack Overflow solutions for handling this specific error
  pattern: Try-except with string checking for "query too old"

- file: src/services/navigation_service.py
  why: Already has safe_edit_message_text method that catches BadRequest for "Message is not modified"
  pattern: |
    Lines 106-118 show how to catch BadRequest safely:
    async def safe_edit_message_text(self, callback_query: CallbackQuery, text, reply_markup=None):
        try:
            await callback_query.edit_message_text(...)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                pass
            else:
                raise
  note: Extend this pattern for callback_query.answer() and add "query too old" handling

- file: src/handlers/menu_handler.py
  why: Main menu handler - good place to implement auto-recovery
  pattern: Lines 228-288 show_menu function - this is where users should be redirected
  note: Entry point for recovery mechanism

- file: src/handlers/booking_handler.py
  why: Complex callback query handler with many callback patterns
  pattern: Lines 59-105 get_handler() returns list of CallbackQueryHandlers
  note: All these handlers need error handling wrapper

- file: src/main.py
  why: Application setup and error_handler registration
  pattern: Lines 42-45 show existing error_handler
  note: Can add global callback query error handling here

- file: src/services/logger_service.py
  why: Logging service for proper error categorization
  pattern: LoggerService.info() for expected errors, LoggerService.error() for unexpected

- file: src/services/redis_service.py
  why: Redis-based state management - shows how booking state is persisted
  pattern: Session data stored with TTL (24 hours by default)
  note: Stale buttons may reference expired Redis sessions
```

### Current Codebase Tree (Relevant Parts)

```bash
src/
├── main.py                              # App entry, error handler registration
├── config/
│   └── config.py                        # Configuration constants
├── constants.py                         # Conversation state constants (END, BACK, MENU, etc.)
├── handlers/
│   ├── __init__.py
│   ├── menu_handler.py                  # Main menu - recovery entry point
│   ├── booking_handler.py               # Complex handler with many callbacks
│   ├── cancel_booking_handler.py
│   ├── change_booking_date_handler.py
│   ├── gift_certificate_handler.py
│   ├── feedback_handler.py
│   ├── question_handler.py
│   ├── admin_handler.py
│   ├── available_dates_handler.py
│   └── price_handler.py
├── services/
│   ├── navigation_service.py            # safe_edit_message_text pattern exists here
│   ├── redis_service.py                 # Session state management
│   ├── logger_service.py                # Logging service
│   └── database_service.py
├── helpers/
│   └── string_helper.py
└── models/
    └── booking_draft.py                 # Draft booking model stored in Redis

db/
└── models/
    └── booking.py                       # Booking database model
```

### Desired Codebase Structure with New Files

```bash
src/
├── decorators/
│   └── callback_error_handler.py        # NEW: Decorator for callback query error handling
├── services/
│   └── callback_recovery_service.py     # NEW: Service for auto-recovery from stale callbacks
└── (existing files with modifications)
```

### Known Gotchas & Library Quirks

```python
# CRITICAL: python-telegram-bot callback query behavior
# 1. Callback queries expire after ~10-15 seconds if not answered
# 2. After bot restart, ALL old callback queries become invalid
# 3. Error message is: "Bad Request: query is too old and response timeout expired or query ID is invalid"
# 4. There is NO specific exception type - must catch BadRequest and check string

# GOTCHA: Multiple places call callback_query.answer()
# Pattern in codebase: Most handlers call `await update.callback_query.answer()` at start
# See: booking_handler.py lines 176, 188, 319, 337, etc.
# ALL these calls can fail if query is stale

# GOTCHA: safe_edit_message_text exists but doesn't handle all BadRequest cases
# See: navigation_service.py lines 106-118
# Only handles "Message is not modified" - needs extension for expired queries

# GOTCHA: ConversationHandler state may be lost on restart
# Redis sessions persist for 24 hours, but conversation state is in-memory
# When bot restarts, conversation state resets but Redis data may still exist
# This creates inconsistency: user has session data but no active conversation state

# GOTCHA: Error handler in main.py is basic
# See: main.py lines 42-45
# Only logs errors, doesn't attempt recovery

# Library Quirk: callback_query.answer() with show_alert=True
# Can show a popup alert to user - useful for "button expired" messages
# Example: await query.answer("Это действие больше недоступно", show_alert=True)

# Codebase pattern: Callback data format is "PREFIX_VALUE"
# Examples: "BOOKING-TARIFF_1", "BOOKING-PHOTO_True", "CALENDAR-CALLBACK-START_2024-01-15"
# String helper extracts value: string_helper.get_callback_data(data)
```

## Implementation Blueprint

### Approach Overview

We'll implement a **multi-layer solution**:

1. **Layer 1**: Decorator for callback query handlers to catch and handle expired queries
2. **Layer 2**: Enhanced `safe_answer_callback_query()` method in NavigationService
3. **Layer 3**: Auto-recovery service that detects stale state and offers menu refresh
4. **Layer 4**: Enhanced global error handler to catch any missed cases

This approach ensures graceful degradation and clear user feedback.

### Data Models and Structure

No new database models needed. We'll use existing structures:

```python
# Extend existing navigation_service.py with new methods
# No new Pydantic/ORM models required

# Optional: Add metadata to Redis sessions for state validation
# Example: Store bot_start_time in Redis to detect stale sessions
```

### List of Tasks (In Order)

```yaml
Task 1: Create callback error handler decorator
  FILE: src/decorators/callback_error_handler.py (NEW)
  PURPOSE: Reusable decorator to wrap callback handlers with error handling
  PATTERN: Similar to retry decorators, catches BadRequest exceptions
  DEPENDENCIES: None

Task 2: Enhance NavigationService with safe callback methods
  FILE: src/services/navigation_service.py (MODIFY)
  PURPOSE: Add safe_answer_callback_query() and safe_callback_handler() methods
  PATTERN: Mirror existing safe_edit_message_text() pattern
  DEPENDENCIES: Task 1 (for reference, not hard dependency)

Task 3: Create callback recovery service
  FILE: src/services/callback_recovery_service.py (NEW)
  PURPOSE: Detect stale buttons and provide auto-recovery mechanisms
  PATTERN: Singleton service, similar to RedisService
  DEPENDENCIES: Task 2 (uses NavigationService methods)

Task 4: Apply error handling to existing handlers
  FILES TO MODIFY:
    - src/handlers/booking_handler.py
    - src/handlers/gift_certificate_handler.py
    - src/handlers/feedback_handler.py
    - src/handlers/cancel_booking_handler.py
    - src/handlers/change_booking_date_handler.py
    - src/handlers/available_dates_handler.py
    - src/handlers/question_handler.py
    - src/handlers/admin_handler.py
  PURPOSE: Wrap callback query handlers with error handling
  PATTERN: Use decorator from Task 1 or NavigationService methods from Task 2
  DEPENDENCIES: Tasks 1, 2

Task 5: Enhance global error handler
  FILE: src/main.py (MODIFY)
  PURPOSE: Add callback query error detection to global error handler as last resort
  PATTERN: Check if error is BadRequest with "query too old", log and attempt recovery
  DEPENDENCIES: Task 3 (uses recovery service)

Task 6: Add logging and monitoring
  FILE: src/services/logger_service.py (potentially modify for better categorization)
  PURPOSE: Ensure expired queries are logged at INFO level, real errors at ERROR level
  PATTERN: Conditional logging based on error type
  DEPENDENCIES: Tasks 1-5

Task 7: Testing and validation
  PURPOSE: Manual testing with bot restart scenarios
  PATTERN:
    1. Start bot
    2. User clicks button to get inline keyboard
    3. Restart bot
    4. User clicks old button
    5. Verify: Clear message, auto-recovery offered
  DEPENDENCIES: All previous tasks
```

### Task-by-Task Pseudocode

```python
# ============================================================================
# Task 1: Create callback error handler decorator
# ============================================================================
# FILE: src/decorators/callback_error_handler.py (NEW)

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from src.services.logger_service import LoggerService

def safe_callback_query(recovery_function=None):
    """
    Decorator for callback query handlers to gracefully handle expired queries.

    Args:
        recovery_function: Optional async function to call for recovery
                          Signature: async def recovery(update, context)

    Usage:
        @safe_callback_query(recovery_function=show_menu)
        async def my_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.callback_query.answer()
            # ... rest of handler logic
    """
    def decorator(handler_func):
        @wraps(handler_func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                return await handler_func(update, context)
            except BadRequest as e:
                error_msg = str(e).lower()

                # PATTERN: Check for specific error messages
                if "query is too old" in error_msg or "query id is invalid" in error_msg:
                    LoggerService.info(
                        __name__,
                        "Callback query expired (likely bot restart)",
                        update,
                        kwargs={"error": str(e)}
                    )

                    # Try to answer with alert popup
                    try:
                        if update.callback_query:
                            await update.callback_query.answer(
                                "⚠️ Это действие больше недоступно. Обновляем меню...",
                                show_alert=True
                            )
                    except:
                        pass  # If answer also fails, ignore

                    # Call recovery function if provided
                    if recovery_function:
                        return await recovery_function(update, context)

                    # Default recovery: import and call show_menu
                    from src.handlers import menu_handler
                    return await menu_handler.show_menu(update, context)
                else:
                    # Re-raise if it's a different BadRequest error
                    raise
            except Exception as e:
                # Log unexpected errors and re-raise
                LoggerService.error(
                    __name__,
                    "Unexpected error in callback handler",
                    exception=e,
                    update=update
                )
                raise

        return wrapper
    return decorator


# ============================================================================
# Task 2: Enhance NavigationService
# ============================================================================
# FILE: src/services/navigation_service.py (MODIFY)

# ADD these methods to the NavigationService class:

async def safe_answer_callback_query(
    self,
    callback_query: CallbackQuery,
    text: str = None,
    show_alert: bool = False
) -> bool:
    """
    Safely answer a callback query, handling expired queries gracefully.

    Returns:
        True if answered successfully, False if query expired
    """
    try:
        await callback_query.answer(text=text, show_alert=show_alert)
        return True
    except BadRequest as e:
        error_msg = str(e).lower()
        if "query is too old" in error_msg or "query id is invalid" in error_msg:
            LoggerService.info(
                __name__,
                "Callback query already expired - cannot answer",
                kwargs={"error": str(e)}
            )
            return False
        else:
            # Re-raise other BadRequest errors
            raise

# MODIFY existing safe_edit_message_text to also handle expired queries:

async def safe_edit_message_text(
    self, callback_query: CallbackQuery, text, reply_markup=None
):
    try:
        await callback_query.edit_message_text(
            text=text, parse_mode="HTML", reply_markup=reply_markup
        )
    except BadRequest as e:
        error_msg = str(e).lower()
        if "message is not modified" in error_msg:
            # Ignore no-op edits (existing behavior)
            pass
        elif "query is too old" in error_msg or "message to edit not found" in error_msg:
            # PATTERN: Query expired or message deleted - log and continue
            LoggerService.info(
                __name__,
                "Cannot edit message - query expired or message deleted",
                kwargs={"error": str(e)}
            )
            # Don't raise - this is expected after bot restart
        else:
            raise


# ============================================================================
# Task 3: Create callback recovery service
# ============================================================================
# FILE: src/services/callback_recovery_service.py (NEW)

from singleton_decorator import singleton
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.services.logger_service import LoggerService
from src.services.navigation_service import NavigationService
from src.services.redis_service import RedisService
from src.constants import MENU

@singleton
class CallbackRecoveryService:
    """
    Service to handle recovery from stale callback queries.
    Detects expired sessions and provides auto-recovery.
    """

    def __init__(self):
        self.navigation_service = NavigationService()
        self.redis_service = RedisService()

    async def handle_stale_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message: str = None
    ):
        """
        Handle a stale callback query by showing recovery options.

        Args:
            update: Telegram Update object
            context: Callback context
            message: Optional custom message to show user
        """
        LoggerService.info(
            __name__,
            "Handling stale callback query",
            update
        )

        # Default message
        if not message:
            message = (
                "⚠️ <b>Бот был обновлен</b>\n\n"
                "Кнопки из предыдущей сессии больше не работают.\n"
                "Обновляем главное меню..."
            )

        # Try to send new message with menu (if callback_query exists)
        if update.callback_query and update.callback_query.message:
            try:
                # Try to edit the existing message
                keyboard = [
                    [InlineKeyboardButton(
                        "🏠 Главное меню",
                        callback_data=f"{MENU}"
                    )]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await self.navigation_service.safe_edit_message_text(
                    callback_query=update.callback_query,
                    text=message,
                    reply_markup=reply_markup
                )
            except:
                # If edit fails, send new message
                try:
                    await update.callback_query.message.reply_text(
                        text=message,
                        parse_mode="HTML"
                    )
                except:
                    pass

        # Clear any stale Redis state
        try:
            self.redis_service.clear_booking(update)
            self.redis_service.clear_feedback(update)
        except:
            pass

        # Auto-redirect to main menu
        from src.handlers import menu_handler
        return await menu_handler.show_menu(update, context)

    def is_callback_stale(self, update: Update) -> bool:
        """
        Detect if a callback query is likely stale.

        Heuristics:
        - Callback data exists but Redis session is empty/expired
        - (Future) Check bot start time vs callback timestamp
        """
        if not update.callback_query:
            return False

        # Check if user has active booking session
        # If callback is for booking but no session exists, it's stale
        callback_data = update.callback_query.data or ""

        if callback_data.startswith("BOOKING-"):
            booking = self.redis_service.get_booking(update)
            if not booking:
                LoggerService.info(
                    __name__,
                    "Callback query appears stale - no active booking session",
                    update
                )
                return True

        return False


# ============================================================================
# Task 4: Apply error handling to existing handlers
# ============================================================================
# MODIFY: src/handlers/booking_handler.py (and other similar handlers)

# BEFORE (example from booking_handler.py line 186):
async def select_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()  # <-- Can fail if query expired
        data = string_helper.get_callback_data(update.callback_query.data)
        # ...

# AFTER - Option A: Use decorator
from src.decorators.callback_error_handler import safe_callback_query

@safe_callback_query()  # <-- Add decorator
async def select_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        data = string_helper.get_callback_data(update.callback_query.data)
        # ... rest remains same

# AFTER - Option B: Use NavigationService method
navigation_service = NavigationService()

async def select_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        # Use safe method instead of direct answer
        answered = await navigation_service.safe_answer_callback_query(
            update.callback_query
        )
        if not answered:
            # Query expired - handle recovery
            from src.services.callback_recovery_service import CallbackRecoveryService
            recovery = CallbackRecoveryService()
            return await recovery.handle_stale_callback(update, context)

        data = string_helper.get_callback_data(update.callback_query.data)
        # ... rest remains same

# RECOMMENDED: Option A (decorator) for cleaner code
# Apply @safe_callback_query() decorator to ALL async def functions in:
# - booking_handler.py: select_tariff, include_photoshoot, include_sauna, etc.
# - gift_certificate_handler.py: all callback handlers
# - feedback_handler.py: all callback handlers
# - cancel_booking_handler.py: all callback handlers
# - change_booking_date_handler.py: all callback handlers
# - available_dates_handler.py: all callback handlers
# - admin_handler.py: callback handlers


# ============================================================================
# Task 5: Enhance global error handler
# ============================================================================
# MODIFY: src/main.py

# BEFORE (lines 42-45):
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    LoggerService.error(
        __name__, f"Update {update} caused error {context.error}", update
    )

# AFTER:
from telegram.error import BadRequest
from src.services.callback_recovery_service import CallbackRecoveryService

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enhanced error handler with callback query recovery"""

    # Check if it's a callback query expiration error
    if isinstance(context.error, BadRequest):
        error_msg = str(context.error).lower()
        if "query is too old" in error_msg or "query id is invalid" in error_msg:
            LoggerService.info(
                __name__,
                "Callback query expired - attempting recovery",
                update,
                kwargs={"error": str(context.error)}
            )

            # Attempt recovery if update is valid
            if isinstance(update, Update) and update.callback_query:
                recovery_service = CallbackRecoveryService()
                try:
                    await recovery_service.handle_stale_callback(update, context)
                    return  # Recovery successful, don't log as error
                except Exception as recovery_error:
                    LoggerService.error(
                        __name__,
                        "Recovery from stale callback failed",
                        exception=recovery_error,
                        update=update
                    )

    # Log all other errors normally
    LoggerService.error(
        __name__, f"Update {update} caused error {context.error}", update
    )


# ============================================================================
# Task 6: Enhanced logging
# ============================================================================
# OPTIONAL: If needed, modify logger_service.py to add specific categories
# For now, existing LoggerService.info() and LoggerService.error() are sufficient

# Ensure proper categorization in all the above code:
# - Expired queries: LoggerService.info() with clear message
# - Unexpected errors: LoggerService.error() with exception
```

### Integration Points

```yaml
HANDLERS:
  - modify: All callback query handlers in src/handlers/*.py
  - pattern: Add @safe_callback_query() decorator to async callback functions
  - alternative: Replace direct callback_query.answer() with navigation_service.safe_answer_callback_query()

SERVICES:
  - create: src/decorators/callback_error_handler.py
  - create: src/services/callback_recovery_service.py
  - modify: src/services/navigation_service.py (add safe_answer_callback_query)

MAIN APPLICATION:
  - modify: src/main.py error_handler function
  - pattern: Add BadRequest detection and recovery logic

REDIS STATE:
  - consideration: May need to clear stale sessions on recovery
  - pattern: Use redis_service.clear_booking() and clear_feedback()

CONVERSATION HANDLERS:
  - consideration: Stale callbacks may break conversation state
  - pattern: Recovery service returns to MENU state
  - alternative: Can return ConversationHandler.END to reset conversation
```

## Validation Loop

### Level 1: Code Quality
```bash
# NO syntax/style validation needed for this codebase
# Project doesn't use ruff/mypy based on CLAUDE.md
# Manual code review for:
# 1. Proper exception handling (try-except blocks)
# 2. Correct import statements
# 3. Consistent patterns with existing code
```

### Level 2: Manual Testing
```bash
# Test Scenario 1: Stale button after bot restart
# 1. Start bot: python src/main.py
# 2. User clicks "Забронировать дом 🏠" button
# 3. User gets tariff selection menu with inline buttons
# 4. RESTART BOT (Ctrl+C and restart)
# 5. User clicks any tariff button from old message
# Expected:
#   - No error in logs (or only INFO level log)
#   - User sees alert: "Это действие больше недоступно"
#   - User automatically gets fresh main menu
#   - User can continue without typing /start

# Test Scenario 2: Callback during active session
# 1. Start bot
# 2. User clicks "Забронировать дом 🏠"
# 3. User selects tariff immediately (no restart)
# Expected:
#   - Normal flow continues
#   - No error messages
#   - Booking flow proceeds as usual

# Test Scenario 3: Old message with multiple buttons
# 1. Start bot
# 2. User gets calendar picker (many inline buttons)
# 3. Restart bot
# 4. User clicks any date button
# Expected:
#   - Clear message about update
#   - Fresh calendar or main menu
#   - No confusion or silent failure

# Test Scenario 4: Simultaneous users
# 1. User A starts booking flow
# 2. User B starts booking flow
# 3. Restart bot
# 4. Both users click buttons
# Expected:
#   - Both users get recovery message
#   - No cross-contamination of sessions
#   - Both can restart independently
```

### Level 3: Production Monitoring
```bash
# After deployment, monitor logs for:
# 1. Frequency of "Callback query expired" INFO logs
#    - If very high, investigate bot stability
# 2. Any ERROR logs related to callback queries
#    - Should be rare after this implementation
# 3. User reports of "broken buttons"
#    - Should decrease significantly

# Log search patterns:
grep "Callback query expired" logs/app.log | wc -l
grep "BadRequest.*query" logs/app.log
```

## Final Validation Checklist
- [ ] Decorator created: `src/decorators/callback_error_handler.py`
- [ ] Recovery service created: `src/services/callback_recovery_service.py`
- [ ] NavigationService enhanced with `safe_answer_callback_query()`
- [ ] At least 5 key handlers decorated with `@safe_callback_query()`
- [ ] Global error handler in `main.py` enhanced
- [ ] Manual test scenario 1 passes (stale button after restart)
- [ ] Manual test scenario 2 passes (normal flow unaffected)
- [ ] No unhandled exceptions in logs for expired queries
- [ ] User receives clear feedback on stale button clicks
- [ ] Auto-recovery to main menu works
- [ ] LoggerService properly categorizes expired queries as INFO
- [ ] Code follows existing patterns from codebase

---

## Anti-Patterns to Avoid
- ❌ Don't catch all exceptions with bare `except:` - be specific with `BadRequest`
- ❌ Don't log expired queries as ERROR level - use INFO (they're expected)
- ❌ Don't show technical error messages to users - use friendly Russian text
- ❌ Don't ignore the error silently - always provide feedback
- ❌ Don't force users to manually type `/start` - auto-recover
- ❌ Don't apply decorator to non-callback handlers (e.g., MessageHandler functions)
- ❌ Don't forget to handle both `callback_query.answer()` AND `edit_message_text()` failures
- ❌ Don't create new callback patterns - follow existing "PREFIX_VALUE" format

## Implementation Notes

### Recommended Approach
1. Start with **Task 1** (decorator) - it's self-contained and reusable
2. Then **Task 2** (NavigationService) - enhances existing service
3. Test with one handler (e.g., booking_handler.py `select_tariff`) before applying broadly
4. Once working, apply to all handlers (**Task 4**)
5. Add global safety net (**Task 5**)

### Priority Order
- **High Priority**: Tasks 1, 2, 4 (core error handling)
- **Medium Priority**: Task 3 (recovery service for better UX)
- **Low Priority**: Task 5 (global handler as backup), Task 6 (enhanced logging)

### Estimated Complexity
- Task 1: **Simple** (30-50 lines, single file)
- Task 2: **Simple** (20-30 lines, modify existing file)
- Task 3: **Medium** (80-120 lines, new service)
- Task 4: **Tedious** (modify 8+ files, but repetitive pattern)
- Task 5: **Simple** (10-20 lines, modify existing function)
- Task 6: **Optional** (only if current logging insufficient)

**Total Estimated Lines of New Code**: ~200-300 lines
**Total Files Modified**: ~10-12 files

---

## Success Metrics

After implementation, measure:
1. **User Experience**: Users no longer report "broken buttons" after updates
2. **Error Logs**: 90%+ reduction in ERROR logs related to callback queries
3. **Session Recovery**: Users can continue without manual `/start` intervention
4. **Stability**: No regression in normal callback flow performance

## Confidence Score

**8.5/10** - High confidence for one-pass implementation because:
- ✅ Clear, well-researched solution with community consensus
- ✅ Existing patterns in codebase to follow (safe_edit_message_text)
- ✅ Comprehensive context provided (docs, examples, Stack Overflow solutions)
- ✅ Incremental approach allows testing at each step
- ✅ Python-telegram-bot library behavior well-documented

**Potential risks**:
- ⚠️ Tedious to apply to all handlers (Task 4) - might miss some
- ⚠️ Edge cases with concurrent users and Redis state - needs testing
- ⚠️ Telegram API behavior edge cases (message deleted, chat archived, etc.)
