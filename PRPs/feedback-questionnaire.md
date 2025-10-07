# PRP: Customer Feedback Questionnaire After Booking Completion

## Goal
Implement an automated customer feedback questionnaire system that is sent to guests after their booking is completed. The questionnaire collects 9 questions (6 with rating buttons 1-10, 3 with text input) and automatically forwards the complete feedback to the admin chat. **Feedback is NOT stored in database - only sent to admin chat.**

## Why
- **Business Value**: Collect structured customer feedback to improve service quality and understand guest satisfaction
- **Integration**: Seamlessly integrates with existing job scheduler system that already sends booking details
- **User Experience**: Provides an easy-to-use inline button interface for ratings and text input for detailed feedback
- **Automation**: Automatically sends feedback summary to admin chat for review without manual intervention
- **Lightweight**: No database overhead - feedback is temporary data stored in Redis during conversation, then sent to admin and cleared

## What
Create a multi-step conversation handler that:
1. Is triggered by `job_service.py` → `send_feedback()` method (line 59-74)
2. Presents 9 sequential questions to the customer
3. Questions 1-6: Rating questions with inline buttons (1-10)
4. Questions 7-9: Text input questions
5. Automatically sends the complete feedback to `ADMIN_CHAT_ID` after the last question
6. **NO database storage** - only Redis for temporary storage during conversation

### Success Criteria
- [x] Handler integrates with existing `send_feedback()` call in `job_service.py`
- [x] All 9 questions are presented sequentially with appropriate input methods
- [x] Rating questions show buttons 1-10 in a clean layout
- [x] Text questions accept user input with proper validation
- [x] Complete feedback is automatically sent to admin chat after question 9
- [x] Conversation handler follows existing codebase patterns (see `available_dates_handler.py`, `question_handler.py`)
- [x] Proper error handling and logging using `LoggerService`
- [x] Clean conversation end without exposing internal states to user
- [x] **NO database persistence** - feedback cleared from Redis after sending to admin

## All Needed Context

### Documentation & References

```yaml
# MUST READ - Include these in your context window

- url: https://docs.python-telegram-bot.org/en/stable/telegram.ext.conversationhandler.html
  why: ConversationHandler states, entry_points, fallbacks for multi-step conversations
  critical: Return state constants to transition, return END to finish conversation

- url: https://core.telegram.org/bots/api
  why: Telegram Bot API for InlineKeyboardButton and InlineKeyboardMarkup

- file: src/handlers/available_dates_handler.py
  why: Reference pattern for handler structure with CallbackQueryHandler
  pattern: |
    def get_handler():
        return [
            CallbackQueryHandler(callback_function, pattern=f"^pattern_(.+)$"),
            CallbackQueryHandler(back_navigation, pattern=f"^{END}$")
        ]

- file: src/handlers/question_handler.py
  why: Pattern for MessageHandler with text input
  pattern: MessageHandler(filters.TEXT & ~filters.COMMAND, message)

- file: src/handlers/admin_handler.py (lines 446-460)
  why: Current send_feedback implementation that needs to be modified
  note: Currently sends Google Forms link, needs to be replaced with conversation handler trigger

- file: src/services/job_service.py (lines 59-74)
  why: Job scheduler that calls send_feedback after booking completion
  note: Runs daily at 8:00 AM, calls admin_handler.send_feedback() for completed bookings

- file: src/constants.py
  why: Constants for conversation states (END, BACK, CONFIRM, etc.)
  pattern: Use ConversationHandler.END for conversation termination
```

### Current Codebase Tree (Relevant Parts)

```bash
src/
├── main.py                              # Application entry point (register handlers here)
├── config/
│   └── config.py                        # Contains ADMIN_CHAT_ID
├── constants.py                         # Conversation state constants
├── handlers/
│   ├── __init__.py
│   ├── available_dates_handler.py       # Reference pattern
│   ├── question_handler.py              # Reference for text input
│   ├── admin_handler.py                 # Contains send_feedback (modify)
│   └── feedback_handler.py              # NEW FILE TO CREATE
├── services/
│   ├── job_service.py                   # Calls send_feedback
│   ├── database_service.py              # Database operations
│   ├── logger_service.py                # Logging
│   └── navigation_service.py            # safe_edit_message_text
├── helpers/
│   └── string_helper.py                 # String utilities
└── models/
    └── feedback.py                      # NEW FILE - Feedback data model

db/
└── models/
    ├── booking.py                       # BookingBase model
    └── feedback.py                      # NEW FILE - Feedback database model
```

### Desired Codebase Tree with Files to Be Added

```bash
src/
├── handlers/
│   └── feedback_handler.py              # NEW: Multi-step feedback conversation handler
├── models/
│   └── feedback.py                      # NEW: Pydantic model for feedback data (Redis only)
└── constants.py                         # MODIFY: Add FEEDBACK state constant

# NO database models needed - feedback is NOT persisted
```

### Known Gotchas & Library Quirks

```python
# CRITICAL: python-telegram-bot v20+ uses async/await
# All handler functions MUST be async

# GOTCHA: ConversationHandler entry_points trigger conversation
# The existing send_feedback() should send a message with inline button to start the conversation
# NOT directly trigger the conversation handler

# PATTERN: Use callback_data with prefixes to route to correct handler
# Example: "FEEDBACK-Q1_5" means Feedback Question 1, answer 5

# CRITICAL: InlineKeyboardButton callback_data has 64-byte limit
# Use short prefixes: "FBQ1_5" instead of "FEEDBACK-QUESTION1_ANSWER_5"

# PATTERN: Use navigation_service.safe_edit_message_text() for editing messages
# Located at: src/services/navigation_service.py

# GOTCHA: MessageHandler in conversation states requires return of next state
# Return state constant or END to transition

# PATTERN: Logging with LoggerService.info/__name__, "message", update, kwargs={'key': 'value'}

# CRITICAL: Database operations use DatabaseService singleton
# Pattern: database_service = DatabaseService()

# PATTERN: Admin messages to ADMIN_CHAT_ID use context.bot.send_message()
# Example: await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)
```

## Implementation Blueprint

### Data Models and Structure

```python
# src/models/feedback.py
from pydantic import BaseModel, Field
from typing import Optional

class Feedback(BaseModel):
    """
    Pydantic model for feedback data during conversation.

    IMPORTANT: This is ONLY used for temporary storage in Redis during
    the conversation. Feedback is NOT saved to database - only sent to
    admin chat and then cleared from Redis.
    """
    booking_id: int
    chat_id: int

    # Rating questions (1-10)
    expectations_rating: Optional[int] = None
    comfort_rating: Optional[int] = None
    cleanliness_rating: Optional[int] = None
    host_support_rating: Optional[int] = None
    location_rating: Optional[int] = None
    recommendation_rating: Optional[int] = None

    # Text questions
    liked_most: Optional[str] = None
    improvements: Optional[str] = None
    public_review: Optional[str] = None

# NO database model needed - feedback is NOT persisted to database
```

### List of Tasks to Complete the PRP (In Order)

```yaml
Task 1: Update constants.py
  - ADD new state constants for feedback conversation
  - Pattern: FEEDBACK = "FEEDBACK" (following existing pattern)
  - States needed: FEEDBACK_Q1 through FEEDBACK_Q9

Task 2: Create Pydantic model (src/models/feedback.py)
  - CREATE Pydantic model Feedback for data validation
  - FOLLOW pattern from src/models/booking_draft.py
  - All fields Optional during conversation collection
  - booking_id and chat_id required
  - NOTE: Only used for Redis storage, NOT for database

Task 3: Create feedback_handler.py
  - CREATE src/handlers/feedback_handler.py
  - IMPLEMENT get_handler() returning list of CallbackQueryHandler and MessageHandler
  - IMPLEMENT entry point: start_feedback_conversation()
  - IMPLEMENT 6 rating question handlers (Q1-Q6) with 1-10 buttons
  - IMPLEMENT 3 text question handlers (Q7-Q9) with text input
  - IMPLEMENT send_feedback_to_admin() - final step
  - USE RedisService to store feedback data during conversation (pattern from booking_handler.py)
  - Each handler returns next state constant

Task 6: Modify admin_handler.py send_feedback()
  - MODIFY src/handlers/admin_handler.py (line 446-460)
  - REPLACE Google Forms link with conversation starter
  - SEND message with inline button "Оставить отзыв" (callback_data="START_FEEDBACK")
  - Button should trigger feedback conversation handler

Task 5: Register handler in main.py
  - ADD import for feedback_handler
  - REGISTER ConversationHandler for feedback in application.add_handler()
  - FOLLOW pattern from other conversation handlers registration

Task 6: Add RedisService support for feedback
  - ADD methods to src/services/redis_service.py for storing feedback data
  - Pattern: init_feedback(), update_feedback_field(), get_feedback(), clear_feedback()
  - MIRROR pattern from existing booking methods in RedisService

Task 7: Testing and validation
  - RUN: uv run ruff check --fix
  - RUN: uv run ruff format .
  - MANUAL TEST: Trigger feedback flow from completed booking
  - VERIFY: All questions appear in sequence
  - VERIFY: Feedback sent to ADMIN_CHAT_ID
  - VERIFY: Feedback stored in database
```

### Per Task Pseudocode

#### Task 5: feedback_handler.py Pseudocode (Critical Implementation)

```python
# src/handlers/feedback_handler.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters
from src.constants import END, FEEDBACK_Q1, FEEDBACK_Q2, ... FEEDBACK_Q9
from src.services.redis_service import RedisService
from src.services.database_service import DatabaseService
from src.services.logger_service import LoggerService
from src.config.config import ADMIN_CHAT_ID

redis_service = RedisService()
database_service = DatabaseService()

def get_handler():
    """Return list of handlers for feedback conversation"""
    return [
        # Entry point - start feedback
        CallbackQueryHandler(start_feedback, pattern="^START_FEEDBACK$"),

        # Q1-Q6: Rating questions (1-10 buttons)
        CallbackQueryHandler(handle_q1_rating, pattern="^FBQ1_(\d+)$"),
        CallbackQueryHandler(handle_q2_rating, pattern="^FBQ2_(\d+)$"),
        CallbackQueryHandler(handle_q3_rating, pattern="^FBQ3_(\d+)$"),
        CallbackQueryHandler(handle_q4_rating, pattern="^FBQ4_(\d+)$"),
        CallbackQueryHandler(handle_q5_rating, pattern="^FBQ5_(\d+)$"),
        CallbackQueryHandler(handle_q6_rating, pattern="^FBQ6_(\d+)$"),

        # Q7-Q9: Text input questions
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_response),

        # Back navigation
        CallbackQueryHandler(cancel_feedback, pattern=f"^{END}$")
    ]

async def start_feedback(update: Update, context):
    """Entry point: Initialize feedback and show Q1"""
    # PATTERN: Extract booking_id from callback_data or context
    # Initialize Redis with booking_id, chat_id
    redis_service.init_feedback(update, booking_id)

    # Show Q1 with rating buttons 1-10
    await show_question_1(update, context)
    return FEEDBACK_Q1

async def show_question_1(update, context):
    """Q1: Оправдались ли ваши ожидания от отдыха в нашем доме?"""
    # PATTERN: Create 10 inline buttons (2 rows of 5)
    keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"FBQ1_{i}")
         for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=f"FBQ1_{i}")
         for i in range(6, 11)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Use navigation_service.safe_edit_message_text for editing
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="Оправдались ли ваши ожидания от отдыха в нашем доме?\n\nОцените от 1 до 10:",
        reply_markup=reply_markup
    )

async def handle_q1_rating(update, context):
    """Handle Q1 rating button click"""
    await update.callback_query.answer()

    # Extract rating from callback_data
    rating = int(update.callback_query.data.split("_")[-1])

    # Store in Redis
    redis_service.update_feedback_field(update, "expectations_rating", rating)

    # Log action
    LoggerService.info(__name__, "Q1 rating received", update,
                      kwargs={'rating': rating})

    # Show Q2
    await show_question_2(update, context)
    return FEEDBACK_Q2

# ... Similar handlers for Q2-Q6 ...

async def handle_q6_rating(update, context):
    """Handle Q6 rating (last rating question)"""
    await update.callback_query.answer()
    rating = int(update.callback_query.data.split("_")[-1])
    redis_service.update_feedback_field(update, "recommendation_rating", rating)

    # Transition to text questions
    await show_question_7(update, context)
    return FEEDBACK_Q7

async def show_question_7(update, context):
    """Q7: Что вам больше всего понравилось в доме и на его территории?"""
    # PATTERN: No buttons for text input, just message
    redis_service.update_feedback_field(update, "current_question", 7)

    await update.callback_query.edit_message_text(
        text="Что вам больше всего понравилось в доме и на его территории?\n\n"
             "Напишите ваш ответ:"
    )
    return FEEDBACK_Q7

async def handle_text_response(update, context):
    """Handle text responses for Q7, Q8, Q9"""
    # PATTERN: Check current_question from Redis to route correctly
    feedback_data = redis_service.get_feedback(update)
    current_q = feedback_data.get("current_question")

    text = update.message.text

    if current_q == 7:
        # Store Q7 answer
        redis_service.update_feedback_field(update, "liked_most", text)
        await show_question_8(update, context)
        return FEEDBACK_Q8

    elif current_q == 8:
        # Store Q8 answer
        redis_service.update_feedback_field(update, "improvements", text)
        await show_question_9(update, context)
        return FEEDBACK_Q9

    elif current_q == 9:
        # Store Q9 answer (final question)
        redis_service.update_feedback_field(update, "public_review", text)

        # Send to admin and save to database
        await send_feedback_to_admin(update, context)

        # Thank user and end conversation
        await update.message.reply_text(
            "Спасибо за ваш отзыв! 🌟\n"
            "Ваше мнение очень важно для нас."
        )

        # Clean up Redis
        redis_service.clear_feedback(update)

        return END

async def send_feedback_to_admin(update, context):
    """Send complete feedback to ADMIN_CHAT_ID (NO database storage)"""
    # PATTERN: Get all feedback from Redis
    feedback_data = redis_service.get_feedback(update)

    # Convert to Pydantic model for validation
    from src.models.feedback import Feedback
    feedback = Feedback(**feedback_data)

    # Format message for admin
    message = (
        "📊 <b>Новый отзыв клиента</b>\n\n"
        f"<b>Бронирование ID:</b> {feedback.booking_id}\n\n"

        f"<b>1. Ожидания от отдыха:</b> {feedback.expectations_rating}/10\n"
        f"<b>2. Уровень комфорта:</b> {feedback.comfort_rating}/10\n"
        f"<b>3. Чистота и уборка:</b> {feedback.cleanliness_rating}/10\n"
        f"<b>4. Общение и поддержка:</b> {feedback.host_support_rating}/10\n"
        f"<b>5. Расположение дома:</b> {feedback.location_rating}/10\n"
        f"<b>6. Рекомендация друзьям:</b> {feedback.recommendation_rating}/10\n\n"

        f"<b>7. Что понравилось:</b>\n{feedback.liked_most}\n\n"
        f"<b>8. Что улучшить:</b>\n{feedback.improvements}\n\n"
        f"<b>9. Публичный отзыв:</b>\n{feedback.public_review}"
    )

    # PATTERN: Send to ADMIN_CHAT_ID
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=message,
        parse_mode='HTML'
    )

    LoggerService.info(__name__, "Feedback sent to admin", update,
                      kwargs={'booking_id': feedback.booking_id})

async def cancel_feedback(update, context):
    """Cancel feedback conversation"""
    redis_service.clear_feedback(update)
    await update.callback_query.answer("Отзыв отменен")
    return END
```

#### Task 6: Modify admin_handler.py send_feedback()

```python
# MODIFY: src/handlers/admin_handler.py (lines 446-460)

async def send_feedback(context: ContextTypes.DEFAULT_TYPE, booking: BookingBase):
    """Modified to trigger feedback conversation instead of sending Google Forms link"""
    try:
        # Create inline button to start feedback conversation
        keyboard = [[InlineKeyboardButton(
            "📝 Оставить отзыв",
            callback_data=f"START_FEEDBACK_{booking.id}"
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = await context.bot.send_message(
            chat_id=booking.chat_id,
            text="🏡 <b>The Secret House благодарит вас за выбор нашего дома для аренды!</b> 💫\n\n"
                 "Мы хотели бы узнать, как Вам понравилось наше обслуживание. "
                 "Будем благодарны, если вы оставите отзыв.\n\n"
                 "После получения фидбека мы дарим Вам <b>10% скидки</b> для следующей поездки.",
            parse_mode='HTML',
            reply_markup=reply_markup
        )

        LoggerService.info(__name__, "Feedback request sent successfully",
                          kwargs={'chat_id': booking.chat_id, 'booking_id': booking.id})

    except Exception as e:
        LoggerService.error(__name__, "Failed to send feedback request",
                           exception=e, kwargs={'booking_id': booking.id})
        raise
```

### Integration Points

```yaml
REDIS:
  - keys: "feedback:{chat_id}" for temporary storage during conversation
  - methods: init_feedback(), update_feedback_field(), get_feedback(), clear_feedback()

HANDLERS:
  - register: ConversationHandler in src/main.py
  - pattern: entry_points=[CallbackQueryHandler(start_feedback, pattern="^START_FEEDBACK_(\d+)$")]
  - states: {FEEDBACK_Q1: [...handlers...], FEEDBACK_Q2: [...], ...}

SERVICES:
  - redis_service: Add feedback storage methods (temporary only)
  - NO database_service changes needed
```

## Validation Loop

### Level 1: Syntax & Style

```bash
# Run these FIRST - fix any errors before proceeding
uv run ruff check src/ --fix
uv run ruff format src/
uv run mypy src/

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Manual Integration Test

```bash
# Start the bot
PYTHONPATH=/Users/a/secret-house-booking-bot python apps/telegram_bot/main.py

# Or using configured command:
timeout 30 python apps/telegram_bot/main.py

# Test Steps:
# 1. Trigger job_service.send_feedback() manually or wait for scheduled job
# 2. User receives message with "Оставить отзыв" button
# 3. Click button → Q1 appears with 1-10 rating buttons
# 4. Answer all 9 questions in sequence
# 5. After Q9, verify:
#    - User receives thank you message
#    - Admin chat receives formatted feedback message
#    - Feedback saved to database

# Check logs for errors
# Expected: All messages sent successfully, no exceptions
```

## Final Validation Checklist

- [ ] All tests pass (if tests exist)
- [ ] No linting errors: `uv run ruff check src/`
- [ ] No type errors: `uv run mypy src/`
- [ ] Manual test: Feedback conversation flows correctly through all 9 questions
- [ ] Manual test: Rating buttons (1-10) work for Q1-Q6
- [ ] Manual test: Text input works for Q7-Q9
- [ ] Manual test: Feedback sent to ADMIN_CHAT_ID with correct formatting
- [ ] Manual test: **Feedback NOT stored in database** (verify no database writes)
- [ ] Error handling: Conversation cancels gracefully
- [ ] Logs are informative: LoggerService used for all major actions
- [ ] Redis cleanup: feedback data cleared after completion

---

## Anti-Patterns to Avoid

- ❌ Don't use synchronous functions - all handlers must be async
- ❌ Don't exceed 64-byte limit for callback_data
- ❌ Don't forget to return state constants from handlers
- ❌ Don't skip RedisService for temporary storage during conversation
- ❌ Don't forget to clean up Redis data after conversation ends
- ❌ Don't hardcode booking_id - extract from callback_data or context
- ❌ Don't forget HTML parsing mode when using bold tags in messages
- ❌ Don't skip logging with LoggerService for debugging
- ❌ Don't forget to call update.callback_query.answer() for button clicks
- ❌ Don't mix MessageHandler and CallbackQueryHandler states (keep them separate)

## Questions to Consider

**Q: Should feedback be required or optional?**
A: Optional - user can cancel anytime. Add "Отменить" button to rating questions.

**Q: What happens if user doesn't complete feedback?**
A: Conversation times out (default 1 hour), Redis data cleaned up automatically.

**Q: Should we validate text length for Q7-Q9?**
A: Yes, limit to 1000 characters each. Return error message if exceeded.

**Q: Store partial feedback if user cancels?**
A: No, clear from Redis. Feedback is never saved to database - only sent to admin chat.

---

## PRP Confidence Score

**Score: 9/10**

**Rationale:**
- ✅ Comprehensive context from codebase analysis
- ✅ Clear task breakdown with pseudocode
- ✅ References to existing patterns (available_dates_handler, question_handler)
- ✅ Integration points well-defined
- ✅ Database models specified
- ✅ Validation steps executable
- ⚠️ Minor: Actual RedisService implementation details not fully verified (need to check existing methods)

**Risk Areas:**
- RedisService might need custom serialization for feedback data
- ConversationHandler registration order in main.py might need adjustment
- Callback_data length might exceed 64 bytes with booking_id included

**Mitigation:**
- Reference `booking_handler.py` for RedisService usage patterns
- Test callback_data lengths: "START_FEEDBACK_12345" = 21 bytes ✓
- Add logging at every state transition for debugging

**Updated: NO DATABASE STORAGE**
- Removed all database-related tasks (Task 2 was database model, Task 8 was migration)
- Feedback is temporary data in Redis → sent to admin chat → cleared
- Simplified from 10 tasks to 7 tasks
