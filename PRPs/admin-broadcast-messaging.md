# PRP: Admin Broadcast Messaging to All Users

## Goal
Implement an admin-only command `/broadcast` that allows the administrator to send messages to all users in the database. The system must retrieve all unique chat IDs from the database and send messages with proper rate limiting to comply with Telegram API restrictions (1 message per second per chat, ~30 messages per second globally).

## Why
- **Business Value**: Enables admin to communicate important announcements, promotions, or updates to all customers
- **Integration**: Uses existing admin handler patterns and database service
- **Communication Efficiency**: Centralized bulk messaging capability without manual individual messages
- **User Reach**: Directly contacts all users who have ever interacted with the bot

## What
Create a new admin command that:
1. Is triggered by `/broadcast` command (admin-only)
2. Starts a conversation flow where admin inputs the message text
3. Retrieves all unique chat IDs from bookings in the database
4. Sends the message to each user with rate limiting (1 msg/sec per chat, ~30/sec globally)
5. Provides progress updates and completion status
6. Handles errors gracefully (user blocked bot, chat not found, etc.)
7. Allows admin to cancel the broadcast before execution

### Success Criteria
- [ ] Command `/broadcast` is registered and only accessible to admin
- [ ] Conversation handler accepts message input from admin
- [ ] All unique chat IDs are retrieved from BookingBase table
- [ ] Messages are sent with proper rate limiting (asyncio.sleep)
- [ ] Progress updates shown during broadcast (every 10 users or similar)
- [ ] Error handling for blocked bots, deleted chats, API errors
- [ ] Completion summary shows: total sent, failed, duration
- [ ] Admin can cancel broadcast before it starts
- [ ] Non-admin users receive permission denied message

## All Needed Context

### Documentation & References

```yaml
# MUST READ - Include these in your context window

- url: https://core.telegram.org/bots/faq
  section: "Rate limits"
  why: Official Telegram rate limits documentation
  critical: |
    - 1 message per second per individual chat (strict limit)
    - ~30 messages per second globally for broadcasts (free tier)
    - 429 errors occur when limits exceeded
    - Use asyncio.sleep() for delays

- url: https://docs.python-telegram-bot.org/
  section: "ConversationHandler, Update, ContextTypes"
  why: Conversation flow for message input
  critical: |
    - ConversationHandler for multi-step commands
    - MessageHandler for text input capture
    - States defined in constants.py

- file: src/handlers/admin_handler.py
  why: Primary reference for admin command patterns
  patterns:
    - change_password() (lines 107-131): Admin check + conversation flow pattern
    - handle_password_input() (lines 134-170): Text input handler in conversation
    - get_unpaid_bookings() (lines 210-234): Admin command with database queries
    - get_booking_list() (lines 184-207): Iterating through bookings
    - get_password_handler() (lines 93-104): ConversationHandler setup pattern
  critical: |
    - Admin check: `if chat_id != ADMIN_CHAT_ID: return END`
    - Use context.user_data to store state between conversation steps
    - Return conversation state constants (ENTER_PRICE, SET_PASSWORD, etc.)
    - Use MessageHandler with filters.Chat(chat_id=ADMIN_CHAT_ID) in states

- file: db/models/booking.py
  why: BookingBase model with chat_id field
  fields:
    - chat_id: Mapped[int] (line 20) - User's Telegram chat ID
  critical: All bookings have chat_id, use DISTINCT to get unique chat IDs

- file: src/services/database_service.py
  why: Database query patterns
  methods:
    - get_booking_by_period() (lines 285-319): SQLAlchemy query pattern
    - Session context manager pattern
  critical: |
    - Use `with self.Session() as session:` pattern
    - Use select() with distinct() for unique chat IDs
    - Error handling with LoggerService.error

- file: src/main.py
  why: Command registration pattern
  pattern: |
    Lines 24-27: admin_commands list in set_commands()
    Lines 48-50: Handler registration
  critical: Register both CommandHandler and ConversationHandler

- file: src/constants.py
  why: Define new conversation state constants
  pattern: |
    Lines 55-59: Admin state constants (SET_PASSWORD, ENTER_PRICE, etc.)
  critical: Add BROADCAST_INPUT constant for message input state

- url: https://docs.python.org/3/library/asyncio-task.html#asyncio.sleep
  section: asyncio.sleep()
  why: Non-blocking delays for rate limiting
  critical: |
    - Use `await asyncio.sleep(seconds)` NOT time.sleep()
    - Allows other handlers to run during delays
    - Essential for Telegram rate limit compliance
```

### Current Codebase Structure
```
src/
├── handlers/
│   ├── admin_handler.py          # Add broadcast functions here
│   ├── feedback_handler.py       # Reference for conversation handlers
│   └── menu_handler.py
├── services/
│   ├── database_service.py       # Add get_all_chat_ids() method
│   └── logger_service.py         # For error logging
├── models/
│   └── booking.py                # BookingBase with chat_id
├── constants.py                  # Add BROADCAST_INPUT constant
└── main.py                       # Register command and handler

db/
└── models/
    └── booking.py                # chat_id field (line 20)
```

### Desired Codebase Changes
```
src/constants.py:
  - ADD: BROADCAST_INPUT = "BROADCAST_INPUT"

src/services/database_service.py:
  - ADD: def get_all_chat_ids() -> list[int]

src/handlers/admin_handler.py:
  - ADD: def get_broadcast_handler() -> ConversationHandler
  - ADD: async def start_broadcast(update, context) -> int
  - ADD: async def handle_broadcast_input(update, context) -> int
  - ADD: async def cancel_broadcast(update, context) -> int
  - ADD: async def execute_broadcast(context, chat_ids, message) -> dict

src/main.py:
  - UPDATE: admin_commands list (add "broadcast" command)
  - ADD: application.add_handler(admin_handler.get_broadcast_handler())
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Telegram rate limits (from official docs)
# - 1 message per second PER CHAT (strict limit)
# - ~30 messages per second globally (free tier)
# - Use asyncio.sleep() to enforce delays

import asyncio
await asyncio.sleep(1.0)  # 1 second delay per chat
# DO NOT use time.sleep() - it's blocking!

# CRITICAL: Admin check pattern (from admin_handler.py:110)
chat_id = update.effective_chat.id
if chat_id != ADMIN_CHAT_ID:
    await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
    return END

# CRITICAL: ConversationHandler state pattern (admin_handler.py:93-104)
# - States dictionary maps state constants to list of handlers
# - MessageHandler with filters.Chat restricts to admin chat
# - Return state constant to continue conversation, END to finish

handler = ConversationHandler(
    entry_points=[CommandHandler("broadcast", start_broadcast)],
    states={
        BROADCAST_INPUT: [
            MessageHandler(
                filters.Chat(chat_id=ADMIN_CHAT_ID) & filters.TEXT & ~filters.COMMAND,
                handle_broadcast_input
            ),
            CallbackQueryHandler(cancel_broadcast, pattern="^cancel_broadcast$"),
        ],
    },
    fallbacks=[],
)

# CRITICAL: Error handling for send_message
# Users may block bot or delete chat - handle gracefully
try:
    await context.bot.send_message(chat_id=chat_id, text=message)
    success_count += 1
except Exception as e:
    # Don't log every failure - just count them
    failed_count += 1
    # Only log unexpected errors
    if "Forbidden" not in str(e) and "Chat not found" not in str(e):
        LoggerService.error(__name__, f"Broadcast error for chat {chat_id}", e)

# CRITICAL: Progress updates during long operations
# Send update every N users to show progress
if (index + 1) % 10 == 0:
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"📤 Отправлено: {index + 1}/{total} сообщений..."
    )

# CRITICAL: Get unique chat IDs using DISTINCT
# Multiple bookings per user means duplicate chat_ids
from sqlalchemy import select, distinct
chat_ids = session.scalars(
    select(distinct(BookingBase.chat_id))
).all()

# GOTCHA: context.user_data persists between handler calls
# Use it to store broadcast message between conversation steps
context.user_data["broadcast_message"] = message_text

# GOTCHA: Rate limiting calculation
# For 100 users at 1 msg/sec per chat = ~100 seconds
# For safety: 1.1 second delay (allows ~27 msg/sec globally)
await asyncio.sleep(1.1)  # Safe rate: ~0.9 messages per second per chat
```

## Implementation Blueprint

### Data Models and Structure
```python
# No new database models needed - using existing BookingBase
# Using chat_id: Mapped[int] from BookingBase (line 20 in booking.py)

# Broadcast result structure (not persisted, just for reporting)
BroadcastResult = {
    "total_users": int,      # Total unique chat IDs found
    "sent": int,             # Successfully sent messages
    "failed": int,           # Failed sends (blocked, deleted, errors)
    "duration_seconds": float,  # Total time taken
}
```

### List of Tasks

```yaml
Task 1: Add conversation state constant
FILE: src/constants.py
ACTION: ADD new constant after ENTER_PREPAYMENT (after line 59)
DETAILS:
  - Add: BROADCAST_INPUT = "BROADCAST_INPUT"
  - This state represents waiting for admin to input broadcast message

Task 2: Add database method to get all unique chat IDs
FILE: src/services/database_service.py
ACTION: ADD new method after get_unpaid_bookings
PATTERN: Mirror get_booking_by_period() structure
DETAILS:
  - Method name: get_all_chat_ids(self) -> list[int]
  - Use select(distinct(BookingBase.chat_id))
  - Return list of unique chat IDs
  - Handle exceptions with LoggerService.error
  - Return empty list on error

Task 3: Add broadcast conversation handler functions
FILE: src/handlers/admin_handler.py
ACTION: ADD three new functions after get_unpaid_bookings
PATTERN: Mirror change_password conversation flow (lines 107-181)
DETAILS:
  - start_broadcast(): Entry point, admin check, prompt for message
  - handle_broadcast_input(): Capture message, confirm, execute broadcast
  - cancel_broadcast(): Cancel broadcast operation
  - execute_broadcast(): Helper function to send messages with rate limiting

Task 4: Create ConversationHandler for broadcast
FILE: src/handlers/admin_handler.py
ACTION: ADD new function after get_password_handler (after line 104)
PATTERN: Mirror get_password_handler() structure (lines 93-104)
DETAILS:
  - Function name: get_broadcast_handler() -> ConversationHandler
  - Entry point: CommandHandler("broadcast", start_broadcast)
  - State: BROADCAST_INPUT with MessageHandler for text input
  - Include cancel callback handler

Task 5: Register broadcast handler and command
FILE: src/main.py
ACTION: UPDATE admin commands and add handler
DETAILS:
  - ADD to admin_commands list (line 24-27):
    BotCommand("broadcast", "Рассылка всем пользователям")
  - ADD handler registration after other admin handlers (after line 50):
    application.add_handler(admin_handler.get_broadcast_handler())

Task 6: Test implementation
ACTION: Manual testing with rate limiting verification
DETAILS:
  - Run bot: PYTHONPATH=/Users/a/secret-house-booking-bot python src/main.py
  - Test as admin: send /broadcast
  - Enter test message
  - Verify rate limiting (should take ~1 second per user)
  - Verify progress updates
  - Verify completion summary
  - Test cancellation flow
  - Test as non-admin: verify permission denied
```

### Task 1 Pseudocode: Add Constant
```python
# src/constants.py (add after line 59)

# Admin
SET_PASSWORD = "SET_PASSWORD"
EDIT_BOOKING_PURCHASE = "EDIT_BOOKING_PURCHASE"
ENTER_PRICE = "ENTER_PRICE"
ENTER_PREPAYMENT = "ENTER_PREPAYMENT"
BROADCAST_INPUT = "BROADCAST_INPUT"  # ADD THIS LINE
```

### Task 2 Pseudocode: Database Query Method
```python
# src/services/database_service.py (add after get_unpaid_bookings)

def get_all_chat_ids(self) -> list[int]:
    """Get all unique chat IDs from bookings"""
    try:
        with self.Session() as session:
            # PATTERN: Use distinct() to get unique chat_ids
            # CRITICAL: Some users may have multiple bookings
            chat_ids = session.scalars(
                select(distinct(BookingBase.chat_id))
            ).all()

            # Convert to list and return
            return list(chat_ids)
    except Exception as e:
        # PATTERN: Log errors using LoggerService
        print(f"Error in get_all_chat_ids: {e}")
        LoggerService.error(__name__, "get_all_chat_ids", e)
        return []  # Return empty list on error
```

### Task 3 Pseudocode: Broadcast Handler Functions
```python
# src/handlers/admin_handler.py (add after get_unpaid_bookings, around line 235)

import asyncio
import time
from src.constants import BROADCAST_INPUT, END

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to start broadcast - asks for message text"""
    # PATTERN: Admin check (from change_password:110)
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
        return END

    # Get total users count for preview
    chat_ids = database_service.get_all_chat_ids()
    total_users = len(chat_ids)

    if total_users == 0:
        await update.message.reply_text("❌ В базе нет пользователей для рассылки.")
        return END

    # Prompt for message input
    keyboard = [[InlineKeyboardButton("Отмена", callback_data="cancel_broadcast")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"📢 <b>Рассылка сообщений</b>\n\n"
        f"Количество получателей: <b>{total_users}</b>\n"
        f"Примерное время: <b>~{total_users} секунд</b>\n\n"
        f"Введите текст сообщения для рассылки:"
    )

    await update.message.reply_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    return BROADCAST_INPUT


async def handle_broadcast_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast message input from admin and execute broadcast"""
    # PATTERN: Admin check (from handle_password_input:139)
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_CHAT_ID:
        return END

    # Get message text
    message_text = update.message.text.strip()

    if not message_text:
        await update.message.reply_text("❌ Сообщение не может быть пустым. Попробуйте еще раз:")
        return BROADCAST_INPUT

    # Store in context for potential future use
    context.user_data["broadcast_message"] = message_text

    # Get all chat IDs
    chat_ids = database_service.get_all_chat_ids()

    # Send confirmation and start broadcast
    await update.message.reply_text(
        f"✅ Начинаю рассылку для {len(chat_ids)} пользователей...\n"
        f"📤 Это займет примерно {len(chat_ids)} секунд."
    )

    # Execute broadcast with rate limiting
    result = await execute_broadcast(context, chat_ids, message_text)

    # Send completion summary
    summary = (
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📊 Статистика:\n"
        f"• Всего пользователей: {result['total_users']}\n"
        f"• Успешно отправлено: {result['sent']}\n"
        f"• Не доставлено: {result['failed']}\n"
        f"• Время выполнения: {result['duration_seconds']:.1f} сек"
    )

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=summary,
        parse_mode="HTML"
    )

    # Clear context
    context.user_data.pop("broadcast_message", None)

    return END


async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel broadcast operation"""
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("❌ Рассылка отменена.")

    # Clear context
    context.user_data.pop("broadcast_message", None)

    return END


async def execute_broadcast(
    context: ContextTypes.DEFAULT_TYPE,
    chat_ids: list[int],
    message: str
) -> dict:
    """
    Execute broadcast with rate limiting and error handling

    Rate limiting strategy:
    - 1 message per second per chat (Telegram limit)
    - ~30 messages per second globally (free tier)
    - Use 1.1 second delay to stay safe (~27 msg/sec)
    """
    start_time = time.time()
    total_users = len(chat_ids)
    sent_count = 0
    failed_count = 0

    for index, chat_id in enumerate(chat_ids):
        try:
            # CRITICAL: Rate limiting - 1 msg/sec per chat
            # Use asyncio.sleep() for non-blocking delay
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML"
            )
            sent_count += 1

            # Progress update every 10 users
            if (index + 1) % 10 == 0:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"�� Прогресс: {index + 1}/{total_users} ({sent_count} отправлено, {failed_count} ошибок)"
                )

            # CRITICAL: Rate limit delay
            # 1.1 seconds = safe rate (~0.9 msg/sec per chat, ~27 msg/sec globally)
            await asyncio.sleep(1.1)

        except Exception as e:
            # Handle common errors: bot blocked, chat deleted
            failed_count += 1
            error_str = str(e)

            # Only log unexpected errors (not blocks/deletions)
            if "Forbidden" not in error_str and "Chat not found" not in error_str:
                LoggerService.error(
                    __name__,
                    f"Broadcast error for chat {chat_id}",
                    exception=e
                )

    duration = time.time() - start_time

    return {
        "total_users": total_users,
        "sent": sent_count,
        "failed": failed_count,
        "duration_seconds": duration,
    }
```

### Task 4 Pseudocode: ConversationHandler Setup
```python
# src/handlers/admin_handler.py (add after get_password_handler, around line 105)

def get_broadcast_handler() -> ConversationHandler:
    """Returns ConversationHandler for broadcast command"""
    handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", start_broadcast)],
        states={
            BROADCAST_INPUT: [
                MessageHandler(
                    filters.Chat(chat_id=ADMIN_CHAT_ID) & filters.TEXT & ~filters.COMMAND,
                    handle_broadcast_input
                ),
                CallbackQueryHandler(cancel_broadcast, pattern="^cancel_broadcast$"),
            ],
        },
        fallbacks=[],
    )
    return handler
```

### Task 5 Pseudocode: Register in Main
```python
# src/main.py

# Step 1: Update set_commands() function (around line 24-28)
async def set_commands(application: Application):
    user_commands = [BotCommand("start", "Открыть 'Главное меню'")]
    admin_commands = user_commands + [
        BotCommand("booking_list", "Бронирования"),
        BotCommand("change_password", "Изменить пароль"),
        BotCommand("unpaid_bookings", "Неоплаченные бронирования"),
        BotCommand("broadcast", "Рассылка всем пользователям"),  # ADD THIS
    ]
    # ... rest of function

# Step 2: Add handler registration (after line 50)
application.add_handler(admin_handler.get_broadcast_handler())
```

### Integration Points
```yaml
DATABASE:
  - No migrations needed - using existing BookingBase.chat_id field
  - New query method: get_all_chat_ids() with DISTINCT

HANDLERS:
  - admin_handler.py:
    * New ConversationHandler: get_broadcast_handler()
    * New functions: start_broadcast, handle_broadcast_input, cancel_broadcast, execute_broadcast

CONSTANTS:
  - Add BROADCAST_INPUT state constant

MAIN:
  - Register ConversationHandler for broadcast
  - Add to admin commands list

EXTERNAL API:
  - Telegram Bot API: send_message with rate limiting
  - asyncio.sleep() for non-blocking delays
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run linter on modified files
uv run ruff check src/handlers/admin_handler.py --fix
uv run ruff check src/services/database_service.py --fix
uv run ruff check src/constants.py --fix
uv run ruff check src/main.py --fix

# Type checking
uv run mypy src/handlers/admin_handler.py
uv run mypy src/services/database_service.py

# Expected: No errors. If errors, READ and fix.
```

### Level 2: Unit Tests
```bash
# No formal unit tests required for this PRP
# Manual testing is appropriate for admin-only feature
# Key test: verify rate limiting timing manually
```

### Level 3: Integration Test
```bash
# Start the bot
PYTHONPATH=/Users/a/secret-house-booking-bot python src/main.py

# Manual test checklist:
# 1. As admin: Send /broadcast
#    Expected: Prompt for message with user count and time estimate
#
# 2. Enter test message: "Тестовое сообщение"
#    Expected: Broadcast starts, progress updates every 10 users
#
# 3. Verify rate limiting:
#    - Time the broadcast: should be ~1.1 seconds per user
#    - For 10 users: ~11 seconds total
#
# 4. Check completion summary:
#    Expected: Total, sent, failed counts with duration
#
# 5. Test cancellation: /broadcast -> type message -> click "Отмена"
#    Expected: "Рассылка отменена" message
#
# 6. As non-admin: Send /broadcast
#    Expected: "⛔ Эта команда не доступна в этом чате."
#
# 7. Verify users receive message:
#    Expected: Check a few user chats to confirm delivery
#
# 8. Test with blocked user scenario:
#    Expected: Failed count increases, no crash
#
# 9. Check command appears in admin menu:
#    Expected: /broadcast visible in admin command list
```

## Final Validation Checklist
- [ ] Linting passes: `uv run ruff check src/`
- [ ] Type checking passes: `uv run mypy src/`
- [ ] BROADCAST_INPUT constant added to constants.py
- [ ] get_all_chat_ids() returns unique chat IDs
- [ ] Command appears in admin menu
- [ ] Admin can execute /broadcast
- [ ] Non-admin receives permission denied
- [ ] Message input captured correctly
- [ ] Rate limiting verified (~1.1 sec per message)
- [ ] Progress updates appear every 10 users
- [ ] Completion summary shows accurate statistics
- [ ] Cancellation works before broadcast starts
- [ ] Handles blocked users gracefully (no crash)
- [ ] No console errors during execution
- [ ] asyncio.sleep() used (not time.sleep())
- [ ] HTML parse mode works in broadcast messages

---

## Anti-Patterns to Avoid
- ❌ Don't use time.sleep() - use asyncio.sleep() (non-blocking)
- ❌ Don't skip rate limiting - will cause 429 errors and bot bans
- ❌ Don't send faster than 1 msg/sec per chat - Telegram will block
- ❌ Don't ignore errors - users may block bot or delete chat
- ❌ Don't log every failed send - clutters logs (only unexpected errors)
- ❌ Don't forget admin check - security critical
- ❌ Don't forget to register ConversationHandler in main.py
- ❌ Don't use broadcast for spam - respect users
- ❌ Don't fetch chat_ids without DISTINCT - will send duplicates
- ❌ Don't block event loop during broadcast - use async patterns
- ❌ Don't forget progress updates - admin needs feedback during long operations
- ❌ Don't compare chat_id without proper type - ADMIN_CHAT_ID is int in this codebase

## Confidence Score: 8.5/10

**Reasoning:**
- ✅ Clear requirements with existing conversation handler patterns
- ✅ Database query is straightforward (DISTINCT chat_ids)
- ✅ Rate limiting strategy is well-documented and proven
- ✅ Admin handler patterns well-established in codebase
- ✅ Error handling strategy is clear
- ⚠️ Minor risk: Long-running operation may encounter edge cases
- ⚠️ Testing difficulty: Requires real users in database for full test
- ⚠️ Rate limiting timing: Need to verify 1.1 sec is optimal
- ✅ No complex business logic or data transformations
- ✅ Straightforward integration into main.py

**Why not 10/10:**
1. Long-running async operations can have edge cases (network issues, bot restarts during broadcast)
2. Rate limiting optimal value (1.0 vs 1.1 seconds) needs real-world testing
3. No existing broadcast pattern in codebase to reference
4. Potential for hitting global rate limit (~30 msg/sec) with large user bases

**Mitigation strategies:**
- Start conservative with 1.1 second delays (can optimize later)
- Add comprehensive error handling for all send_message failures
- Progress updates keep admin informed of any issues
- Clear documentation of rate limits in code comments