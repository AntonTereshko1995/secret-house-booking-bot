# PRP: Admin Command to Display Unpaid Bookings

## Goal
Implement an admin-only command `/unpaid_bookings` that displays all active bookings that have not been prepaid yet, showing them with action buttons to allow quick admin processing.

## Why
- **Business Value**: Allows admin to quickly identify bookings awaiting payment confirmation
- **Integration**: Uses existing admin handler patterns and booking management system
- **Efficiency**: Reduces manual search time for unpaid bookings
- **User Experience**: Admin gets immediate overview of pending payments with actionable buttons

## What
Create a new admin command that:
1. Is triggered by `/unpaid_bookings` command (admin-only)
2. Queries database for bookings where `is_prepaymented = False`, `is_canceled = False`, and `is_done = False`
3. For each found booking, displays it using the existing `accept_booking_payment()` function
4. Shows action buttons (confirm payment, cancel, change price, etc.)
5. Returns END if no bookings found or command executed by non-admin

### Success Criteria
- [ ] Command `/unpaid_bookings` is registered and only accessible to admin
- [ ] Correctly filters bookings by payment status
- [ ] Each booking is displayed with full details and action buttons
- [ ] Non-admin users receive permission denied message
- [ ] Follows existing admin handler patterns (see `change_password` and `get_booking_list`)
- [ ] Proper error handling and logging

## All Needed Context

### Documentation & References

```yaml
# MUST READ - Include these in your context window

- url: https://docs.python-telegram-bot.org/en/stable/
  why: CommandHandler, Update, ContextTypes for command handling
  critical: Commands registered in main.py with CommandHandler

- file: src/handlers/admin_handler.py
  why: Primary reference for admin command patterns
  patterns:
    - get_password_handler() (lines 85-95): ConversationHandler pattern
    - change_password() (lines 98-142): Admin check pattern with ADMIN_CHAT_ID
    - get_booking_list() (lines 170-194): Command that displays multiple bookings
    - accept_booking_payment() (lines 197-274): Function to display booking with action buttons
  critical: |
    - Admin check: `if str(chat_id) != ADMIN_CHAT_ID: return END`
    - Display pattern: iterate bookings and send with action buttons
    - Use accept_booking_payment() to show each booking with buttons

- file: db/models/booking.py
  why: BookingBase model structure
  fields:
    - is_prepaymented: Mapped[bool] (line 32)
    - is_canceled: Mapped[bool] (line 29)
    - is_done: Mapped[bool] (line 33)
    - user_id, start_date, end_date, price, prepayment_price, etc.

- file: src/services/database_service.py
  why: Database query patterns for bookings
  methods:
    - get_booking_by_period() (lines 285-319): Shows filter pattern with is_prepaymented, is_canceled, is_done
    - get_booking_by_id() (lines 441-450): Get single booking
  critical: Use SQLAlchemy `select()` with `and_()` for multiple conditions

- file: src/main.py
  why: How to register new commands
  pattern: |
    Line 56-58:
    application.add_handler(
        CommandHandler("booking_list", admin_handler.get_booking_list)
    )
  critical: Add similar line for /unpaid_bookings command
```

### Current Codebase Structure
```
src/
├── handlers/
│   └── admin_handler.py          # Add new function here
├── services/
│   └── database_service.py       # Add query method if needed
├── models/
│   └── booking.py                # BookingBase model
└── main.py                       # Register command here
```

### Desired Codebase Changes
```
src/handlers/admin_handler.py:
  - ADD: async def get_unpaid_bookings(update, context)

src/services/database_service.py:
  - ADD: def get_unpaid_bookings() -> Sequence[BookingBase]

src/main.py:
  - ADD: CommandHandler registration for /unpaid_bookings
  - UPDATE: admin_commands list in set_commands()
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Admin check pattern
# Pattern from admin_handler.py:98-102
chat_id = update.effective_chat.id
if str(chat_id) != ADMIN_CHAT_ID:
    await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
    return END

# CRITICAL: accept_booking_payment signature (line 197-205)
# Requires: update, context, booking, user_chat_id, photo, document, is_payment_by_cash
# For admin command: photo=None, document=None, is_payment_by_cash=False
await accept_booking_payment(
    update, context, booking, booking.chat_id, None, None, False
)

# CRITICAL: Database query pattern for multiple filters
# Use and_() to combine conditions (see database_service.py:294-300)
from sqlalchemy import and_, select
bookings = session.scalars(
    select(BookingBase).where(
        and_(
            BookingBase.is_prepaymented == False,
            BookingBase.is_canceled == False,
            BookingBase.is_done == False,
        )
    ).order_by(BookingBase.start_date)
).all()

# GOTCHA: ADMIN_CHAT_ID is a string from config
# Always compare: if str(chat_id) != ADMIN_CHAT_ID

# GOTCHA: Return END constant to exit handler
# Import from src/constants.py
from src.constants import END
```

## Implementation Blueprint

### Data Models and Structure
```python
# No new models needed - using existing BookingBase
# Fields used:
# - is_prepaymented: bool
# - is_canceled: bool
# - is_done: bool
# - All booking detail fields (start_date, end_date, price, etc.)
```

### List of Tasks

```yaml
Task 1: Add database query method for unpaid bookings
FILE: src/services/database_service.py
ACTION: ADD new method after get_booking_by_user_contact (after line 472)
PATTERN: Mirror get_booking_by_period() structure (lines 285-319)
DETAILS:
  - Method name: get_unpaid_bookings()
  - Return type: Sequence[BookingBase]
  - Filter conditions:
    * is_prepaymented == False
    * is_canceled == False
    * is_done == False
  - Order by: start_date
  - Use try/except with LoggerService.error

Task 2: Add admin command handler function
FILE: src/handlers/admin_handler.py
ACTION: ADD new function after get_booking_list (after line 194)
PATTERN: Mirror get_booking_list() and change_password() patterns
DETAILS:
  - Function name: async def get_unpaid_bookings(update, context)
  - Admin check using ADMIN_CHAT_ID (same as change_password:100-102)
  - Query: bookings = database_service.get_unpaid_bookings()
  - If no bookings: send "🔍 Не найдено неоплаченных бронирований." and return END
  - For each booking: call accept_booking_payment() with correct parameters
  - Return END at the end

Task 3: Register command in main.py
FILE: src/main.py
ACTION: ADD command handler and update admin commands list
DETAILS:
  - ADD to admin_commands list in set_commands() (line 24-27):
    BotCommand("unpaid_bookings", "Неоплаченные бронирования")
  - ADD CommandHandler after booking_list handler (after line 58):
    CommandHandler("unpaid_bookings", admin_handler.get_unpaid_bookings)

Task 4: Test the implementation
ACTION: Manual testing
DETAILS:
  - Run bot: PYTHONPATH=/Users/a/secret-house-booking-bot python src/main.py
  - Test as admin: send /unpaid_bookings
  - Test as non-admin: verify permission denied
  - Verify bookings display with action buttons
  - Verify "no bookings" message when list is empty
```

### Task 1 Pseudocode: Database Query Method
```python
# src/services/database_service.py (add after line 472)

def get_unpaid_bookings(self) -> Sequence[BookingBase]:
    """Get all unpaid, active bookings"""
    try:
        with self.Session() as session:
            # PATTERN: Use select() with and_() for multiple conditions
            bookings = session.scalars(
                select(BookingBase).where(
                    and_(
                        BookingBase.is_prepaymented == False,
                        BookingBase.is_canceled == False,
                        BookingBase.is_done == False,
                    )
                ).order_by(BookingBase.start_date)
            ).all()
            return bookings
    except Exception as e:
        # PATTERN: Log errors using LoggerService
        print(f"Error in get_unpaid_bookings: {e}")
        LoggerService.error(__name__, "get_unpaid_bookings", e)
        return []  # Return empty list on error
```

### Task 2 Pseudocode: Admin Command Handler
```python
# src/handlers/admin_handler.py (add after line 194)

async def get_unpaid_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to show all unpaid bookings"""
    # PATTERN: Admin check (from change_password:100-102)
    chat_id = update.effective_chat.id
    if str(chat_id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
        return END

    # Query unpaid bookings
    bookings = database_service.get_unpaid_bookings()

    # Handle empty case (pattern from get_booking_list:178-180)
    if not bookings:
        await update.message.reply_text("🔍 Не найдено неоплаченных бронирований.")
        return END

    # Display each booking with action buttons
    # CRITICAL: Use accept_booking_payment() to show buttons
    for booking in bookings:
        # PATTERN: accept_booking_payment signature (line 197-205)
        # Parameters: update, context, booking, user_chat_id, photo, document, is_payment_by_cash
        await accept_booking_payment(
            update,
            context,
            booking,
            booking.chat_id,  # User's chat_id from booking
            None,             # photo = None (no photo from command)
            None,             # document = None (no document from command)
            False             # is_payment_by_cash = False (default)
        )

    return END
```

### Task 3 Pseudocode: Register Command
```python
# src/main.py

# Step 1: Update set_commands() function (around line 24-27)
async def set_commands(application: Application):
    user_commands = [BotCommand("start", "Открыть 'Главное меню'")]
    admin_commands = user_commands + [
        BotCommand("booking_list", "Бронирования"),
        BotCommand("change_password", "Изменить пароль"),
        BotCommand("unpaid_bookings", "Неоплаченные бронирования"),  # ADD THIS
    ]
    # ... rest of function

# Step 2: Add CommandHandler (after line 58)
application.add_handler(
    CommandHandler("unpaid_bookings", admin_handler.get_unpaid_bookings)
)
```

### Integration Points
```yaml
DATABASE:
  - No migrations needed - using existing BookingBase fields

HANDLERS:
  - admin_handler.py: New function get_unpaid_bookings()
  - Reuses existing accept_booking_payment() function

SERVICES:
  - database_service.py: New query method get_unpaid_bookings()

MAIN:
  - Register new CommandHandler for /unpaid_bookings
  - Add to admin commands list
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run linter on modified files
uv run ruff check src/handlers/admin_handler.py --fix
uv run ruff check src/services/database_service.py --fix
uv run ruff check src/main.py --fix

# Type checking
uv run mypy src/handlers/admin_handler.py
uv run mypy src/services/database_service.py

# Expected: No errors. If errors, READ and fix.
```

### Level 2: Unit Tests
```bash
# No unit tests required for this PRP
# This is a simple command that uses existing tested functions
# Manual testing is sufficient
```

### Level 3: Integration Test
```bash
# Start the bot
PYTHONPATH=/Users/a/secret-house-booking-bot python src/main.py

# Manual test checklist:
# 1. As admin user: Send /unpaid_bookings
#    Expected: List of unpaid bookings with action buttons OR "no bookings" message
#
# 2. As non-admin user: Send /unpaid_bookings
#    Expected: "⛔ Эта команда не доступна в этом чате."
#
# 3. Click action buttons on displayed bookings
#    Expected: Existing accept_booking_payment handlers work correctly
#
# 4. Check admin commands list
#    Expected: /unpaid_bookings appears in command menu for admin
```

## Final Validation Checklist
- [ ] Linting passes: `uv run ruff check src/`
- [ ] Type checking passes: `uv run mypy src/`
- [ ] Command appears in admin menu
- [ ] Admin can execute /unpaid_bookings
- [ ] Non-admin receives permission denied
- [ ] Bookings display with correct details
- [ ] Action buttons work (confirm, cancel, change price)
- [ ] Empty list shows appropriate message
- [ ] No console errors during execution

---

## Anti-Patterns to Avoid
- ❌ Don't create new database models - use existing BookingBase
- ❌ Don't skip admin check - security requirement
- ❌ Don't hardcode filters - use database query method
- ❌ Don't duplicate accept_booking_payment code - reuse existing function
- ❌ Don't forget to register command in main.py
- ❌ Don't compare chat_id without str() conversion - ADMIN_CHAT_ID is string
- ❌ Don't forget to return END from handler
- ❌ Don't use sync database calls - all database methods are sync, handlers are async

## Confidence Score: 9/10

**Reasoning:**
- ✅ Clear requirements with existing patterns to follow
- ✅ Reuses 90% of existing code (accept_booking_payment, database patterns)
- ✅ Simple query with well-defined filters
- ✅ Admin handler pattern is well-established in codebase
- ⚠️ Minor risk: Calling accept_booking_payment from command context (but pattern exists in gift_callback)
- ✅ No complex business logic or edge cases
- ✅ Straightforward integration into main.py

**Why not 10/10:**
Slight uncertainty around accept_booking_payment being called directly from command context vs callback context, but the function signature supports both (it's just an async function that sends messages).
