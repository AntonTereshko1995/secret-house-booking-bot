# PRP: Admin Booking Management Interface

## Goal
Implement a comprehensive admin interface for viewing and managing all bookings. The system provides a list view with up to 100 booking buttons (Telegram API limit), each opening a detailed view with actions: cancel, reschedule, change price, change prepayment, and change tariff. After each action, the system sends a notification message to the customer.

**Architecture Note:** This feature is split into two handlers:
- **`admin_handler.py`**: Contains the `/manage_bookings` command that shows the booking list
- **`booking_details_handler.py`**: New file containing detail view and all booking actions (cancel, change price, change tariff, etc.)

## Why
- **Business Value**: Centralized booking management reduces manual work and improves admin efficiency
- **Customer Communication**: Automatic notifications keep customers informed of changes
- **Flexibility**: Admins can modify bookings as circumstances change (pricing errors, customer requests, rescheduling)
- **Integration**: Builds on existing admin patterns and booking modification flows
- **User Experience**: Customers receive timely updates about their booking changes

## What
Create a two-level admin interface:

**Level 1 - Booking List:**
1. Triggered by new command `/manage_bookings` (admin-only)
2. Shows all future bookings (not canceled) as inline keyboard buttons
3. Each button displays: start date and time (e.g., "15.01.2025 14:00")
4. Maximum 100 buttons (Telegram limit: 8 per row, 100 total)
5. Buttons sorted chronologically (earliest first)

**Level 2 - Booking Detail:**
1. Clicking a booking button opens detailed view in new handler
2. Shows full booking information (using existing `generate_booking_info_message`)
3. Action buttons:
   - 🔙 **Назад** (Back to list)
   - ❌ **Отменить бронь** (Cancel booking)
   - 📅 **Перенести бронь** (Reschedule booking)
   - 💰 **Изменить стоимость** (Change price)
   - 💳 **Изменить предоплату** (Change prepayment)
   - 🎯 **Изменить тариф** (Change tariff)

**Level 3 - Actions:**
Each action:
- Uses conversation handler for input (where needed)
- Updates database
- Sends notification to customer via their chat_id
- Returns to detail view with updated info

### Success Criteria
- [ ] Command `/manage_bookings` registered and admin-only
- [ ] Booking list shows max 100 future bookings as buttons
- [ ] Buttons display date/time: "DD.MM.YYYY HH:MM"
- [ ] Clicking button opens detail view with full booking info
- [ ] Detail view has 6 action buttons + back button
- [ ] Cancel action: marks booking as canceled, notifies customer
- [ ] Reschedule action: opens date picker, updates dates, notifies customer
- [ ] Change price: text input → validates → updates → notifies customer
- [ ] Change prepayment: text input → validates → updates → notifies customer
- [ ] Change tariff: tariff selection → updates → recalculates price → notifies customer
- [ ] Back button returns to booking list
- [ ] Customer notifications include relevant booking details
- [ ] All actions log to LoggerService
- [ ] Non-admin users receive permission denied

## All Needed Context

### Documentation & References

```yaml
# MUST READ - Include these in your context window

- url: https://core.telegram.org/bots/api#inlinekeyboardmarkup
  section: "InlineKeyboardMarkup"
  why: Button layout and limitations
  critical: |
    - Maximum 100 buttons total per message
    - Maximum 8 buttons per row
    - callback_data limited to 64 bytes
    - Use compact encoding for callback data

- url: https://docs.python-telegram-bot.org/en/stable/telegram.inlinekeyboardbutton.html
  section: "InlineKeyboardButton"
  why: Button creation and callback patterns
  critical: |
    - callback_data must be string, max 64 bytes
    - Use pattern matching in CallbackQueryHandler
    - Format: "ACTION_bookingid_{id}_userid_{uid}"

- url: https://docs.python-telegram-bot.org/en/stable/telegram.ext.conversationhandler.html
  section: "ConversationHandler"
  why: Multi-step action flows (reschedule, change price, etc.)
  critical: |
    - Entry points, states, and fallbacks
    - Store context in context.user_data
    - Return state constants from handlers
    - Use END to terminate conversation

- file: src/handlers/admin_handler.py
  why: Primary reference for admin patterns (booking list will be added here)
  patterns:
    - get_booking_list() (lines 281-304): Existing booking list command (simple text output)
    - get_future_bookings() (lines 1142-1146): Query for future bookings - REUSE THIS
    - booking_callback() (lines 779-801): Callback pattern for booking actions
    - _create_booking_keyboard() (lines 588-618): Inline keyboard creation
    - request_price_input() (lines 818-845): Text input conversation flow
    - handle_price_input() (lines 886-926): Input validation and update
    - approve_booking() (lines 1044-1080): Customer notification pattern
    - cancel_booking() (lines 1083-1102): Cancellation with notification
  critical: |
    - Admin check: `if chat_id != ADMIN_CHAT_ID: return END`
    - Use context.user_data to store booking_id, user_chat_id between steps
    - Callback data parsing with string_helper.parse_booking_callback_data()
    - Customer notifications via context.bot.send_message(chat_id=user.chat_id)
    - Message editing with _edit_message() helper (lines 633-647)

- file: src/handlers/feedback_handler.py
  why: Reference for separate handler file structure
  patterns:
    - File structure: imports, service instances, handler functions, get_handler() export
    - ConversationHandler pattern with entry_points, states, fallbacks
  critical: |
    - Export main handler via get_handler() function
    - Import and register in main.py: application.add_handler(feedback_handler.get_handler())

- file: src/helpers/string_helper.py
  why: Message generation and callback parsing
  methods:
    - generate_booking_info_message() (lines 140-221): Full booking details
    - parse_booking_callback_data() (lines 223-245): Parse callback_data
  critical: |
    - Reuse generate_booking_info_message() for detail view
    - Use consistent callback_data format
    - Include user info in messages

- file: db/models/booking.py
  why: BookingBase model structure
  fields:
    - id, user_id, start_date, end_date, tariff, price, prepayment_price
    - is_canceled, is_prepaymented, calendar_event_id
    - user relationship for user.chat_id access
  critical: |
    - All bookings have user relationship for chat_id
    - Check is_canceled=False for active bookings
    - Update calendar_event_id when rescheduling

- file: src/services/database_service.py
  why: Database query and update methods
  methods:
    - get_booking_by_start_date_period() (lines ~285): Query bookings by date range
    - get_booking_by_id() (line ~250): Fetch single booking
    - update_booking() (lines ~260): Update booking fields
    - get_user_by_id(): Fetch user for chat_id
  critical: |
    - Use get_future_bookings() pattern from admin_handler.py (lines 1142-1146)
    - Update method returns updated booking instance
    - Always check user.chat_id exists before sending messages

- file: src/services/calendar_service.py
  why: Google Calendar integration for rescheduling
  methods:
    - add_event(): Creates calendar event
    - update_event(): Updates existing event
    - delete_event(): Removes event
  critical: |
    - Update calendar when rescheduling
    - Use calendar_event_id from booking
    - Handle API errors gracefully

- file: src/constants.py
  why: Define new conversation state constants
  pattern: Lines 56-66 (Admin constants)
  critical: |
    - Add: MANAGE_BOOKING_DETAIL = "MANAGE_BOOKING_DETAIL"
    - Add: MANAGE_RESCHEDULE = "MANAGE_RESCHEDULE"
    - Add: MANAGE_CHANGE_TARIFF = "MANAGE_CHANGE_TARIFF"

- file: src/main.py
  why: Command and handler registration
  pattern: Lines 27-38 (admin_commands), lines 101-128 (handler registration)
  critical: |
    - Add "manage_bookings" to admin_commands list
    - Register ConversationHandler for multi-step actions
    - Register CallbackQueryHandler for button clicks

- file: PRPs/admin-broadcast-messaging.md
  why: Similar admin command pattern with customer messaging
  patterns:
    - Admin permission checks
    - Customer notification patterns
    - Rate limiting (if sending many messages)
  critical: Use context.bot.send_message() for customer notifications

- url: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
  section: "strftime() format codes"
  why: Date formatting for button labels
  critical: Use "%d.%m.%Y %H:%M" for consistency with existing code
```

### Current Codebase Structure
```
src/
├── handlers/
│   ├── admin_handler.py          # Add booking list command here
│   ├── booking_details_handler.py # CREATE NEW: Detail view and actions
│   ├── booking_handler.py        # Reference for booking flow
│   └── change_booking_date_handler.py  # Reference for date changes
├── services/
│   ├── database_service.py       # Booking queries and updates
│   ├── calendar_service.py       # Google Calendar integration
│   └── logger_service.py         # Error logging
├── helpers/
│   ├── string_helper.py          # Message generation
│   └── tariff_helper.py          # Tariff name formatting
├── models/
│   └── enum/
│       └── tariff.py             # Tariff enum for selection
├── constants.py                  # Add new state constants
└── main.py                       # Register commands and handlers

db/
└── models/
    └── booking.py                # BookingBase with all fields
```

### Desired Codebase Changes
```yaml
src/constants.py:
  - ADD: MANAGE_BOOKING_DETAIL = "MANAGE_BOOKING_DETAIL"
  - ADD: MANAGE_RESCHEDULE_DATE = "MANAGE_RESCHEDULE_DATE"
  - ADD: MANAGE_RESCHEDULE_TIME = "MANAGE_RESCHEDULE_TIME"
  - ADD: MANAGE_CHANGE_PRICE = "MANAGE_CHANGE_PRICE"
  - ADD: MANAGE_CHANGE_PREPAYMENT = "MANAGE_CHANGE_PREPAYMENT"
  - ADD: MANAGE_CHANGE_TARIFF = "MANAGE_CHANGE_TARIFF"

src/handlers/admin_handler.py:
  - ADD: async def manage_bookings_list(update, context) -> None  # Main command handler

src/handlers/booking_details_handler.py:  # NEW FILE
  - CREATE: New handler file for booking detail view and actions
  - ADD: async def show_booking_detail(update, context) -> int
  - ADD: async def back_to_booking_list(update, context) -> int
  - ADD: async def start_cancel_booking(update, context) -> int
  - ADD: async def start_reschedule_booking(update, context) -> int
  - ADD: async def start_change_price(update, context) -> int
  - ADD: async def handle_price_change_input(update, context) -> int
  - ADD: async def start_change_prepayment(update, context) -> int
  - ADD: async def handle_prepayment_change_input(update, context) -> int
  - ADD: async def start_change_tariff(update, context) -> int
  - ADD: async def handle_tariff_selection(update, context) -> int
  - ADD: async def notify_customer_cancellation(context, booking, user) -> None
  - ADD: async def notify_customer_reschedule(context, booking, user, old_dates) -> None
  - ADD: async def notify_customer_price_change(context, booking, user, old_price) -> None
  - ADD: async def notify_customer_prepayment_change(context, booking, user, old_prepay) -> None
  - ADD: async def notify_customer_tariff_change(context, booking, user, old_tariff) -> None
  - ADD: def get_handler() -> ConversationHandler  # Main handler export

src/helpers/string_helper.py:
  - ADD: def parse_manage_booking_callback(data: str) -> dict
  - ADD: def format_booking_button_label(booking: BookingBase) -> str

src/main.py:
  - UPDATE: admin_commands list (add BotCommand("manage_bookings", "Управление бронированиями"))
  - ADD: from src.handlers import booking_details_handler
  - ADD: application.add_handler(booking_details_handler.get_handler())
  - ADD: application.add_handler(CommandHandler("manage_bookings", admin_handler.manage_bookings_list))
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Telegram Bot API Limits
# - Maximum 100 buttons total in InlineKeyboardMarkup
# - Maximum 8 buttons per row
# - callback_data max 64 bytes
# - Solution: Use compact callback format "MB_{booking_id}"

# CRITICAL: python-telegram-bot conversation handlers
# - Must return state constant or END from each handler
# - Use context.user_data to pass data between steps
# - CallbackQueryHandler must answer() the query
# - MessageHandler in states must filter by ADMIN_CHAT_ID

# CRITICAL: Database updates
# - Always fetch fresh booking before operations
# - Check user.chat_id exists before sending messages
# - Update calendar_event_id when rescheduling
# - Use database_service.update_booking() which returns updated instance

# CRITICAL: Customer notifications
# - Check if user.chat_id is not None before sending
# - Handle TelegramError (user blocked bot, chat not found)
# - Use HTML parse_mode for formatted messages
# - Include booking ID for customer reference

# CRITICAL: Date/time handling
# - Project uses Europe/Minsk timezone (main.py line 133)
# - Use datetime.strptime() with "%d.%m.%Y %H:%M" format
# - When rescheduling, validate new date doesn't conflict with existing bookings
# - Update both start_date and end_date (maintain duration)

# GOTCHA: Callback data size limit
# Format must be compact: "MB_123" not "MANAGE_BOOKING_bookingid_123_userid_456"
# Parse format:
#   - List view: "MBL" (manage booking list - back button)
#   - Detail view: "MBD_{booking_id}"
#   - Actions: "MBA_{action}_{booking_id}" where action is: cancel, reschedule, price, prepay, tariff

# GOTCHA: Message editing vs. sending
# - Use update.callback_query.edit_message_text() for button clicks
# - Use update.message.reply_text() for text input responses
# - Check message type (text vs caption) with _edit_message() helper

# GOTCHA: Existing code patterns
# - Reuse get_future_bookings() from admin_handler.py line 1142
# - Reuse _create_booking_keyboard() pattern but adapt for management
# - Reuse request_price_input() / handle_price_input() patterns for text input
# - Follow booking_callback() pattern for callback parsing

# GOTCHA: Price recalculation when changing tariff
# - Use calculation_rate_service.calculate_rate() to recalculate price
# - Pass booking details: dates, tariff, guests, extras (sauna, photoshoot, etc.)
# - Update both price and prepayment_price if needed
```

## Implementation Blueprint

### Data Models and Structure
```python
# No new database models needed - uses existing BookingBase

# Callback data format (keep under 64 bytes)
CALLBACK_FORMATS = {
    "booking_list": "MBL",                           # Back to list
    "booking_detail": "MBD_{booking_id}",            # View detail
    "cancel": "MBA_cancel_{booking_id}",             # Cancel action
    "reschedule": "MBA_reschedule_{booking_id}",     # Reschedule action
    "price": "MBA_price_{booking_id}",               # Change price
    "prepay": "MBA_prepay_{booking_id}",             # Change prepayment
    "tariff": "MBA_tariff_{booking_id}",             # Change tariff
    "tariff_select": "MBT_{tariff_value}_{booking_id}",  # Tariff selection
    "back_detail": "MBB_{booking_id}",               # Back to detail
}

# Context.user_data keys for conversation state
CONTEXT_KEYS = {
    "manage_booking_id": int,        # Current booking being managed
    "manage_user_chat_id": int,      # Customer chat_id for notifications
    "manage_old_value": Any,         # Old value (for change notifications)
    "manage_action": str,            # Current action type
}
```

### Task List (in order of completion)

```yaml
Task 1: Add conversation state constants
  FILE: src/constants.py
  ACTION: ADD new constants
  CODE: |
    # Admin - Booking Management
    MANAGE_BOOKING_DETAIL = "MANAGE_BOOKING_DETAIL"
    MANAGE_RESCHEDULE_DATE = "MANAGE_RESCHEDULE_DATE"
    MANAGE_RESCHEDULE_TIME = "MANAGE_RESCHEDULE_TIME"
    MANAGE_CHANGE_PRICE = "MANAGE_CHANGE_PRICE"
    MANAGE_CHANGE_PREPAYMENT = "MANAGE_CHANGE_PREPAYMENT"
    MANAGE_CHANGE_TARIFF = "MANAGE_CHANGE_TARIFF"

Task 2: Add helper functions for callback parsing
  FILE: src/helpers/string_helper.py
  ACTION: ADD two new functions at end of file
  PATTERN: Similar to parse_booking_callback_data() (existing)
  CODE: |
    def parse_manage_booking_callback(data: str) -> dict:
        """Parse callback data from booking management buttons

        Formats:
          - MBL: Back to list
          - MBD_{booking_id}: View detail
          - MBA_{action}_{booking_id}: Action
          - MBT_{tariff}_{booking_id}: Tariff selection
          - MBB_{booking_id}: Back to detail
        """
        parts = data.split("_")

        if data == "MBL":
            return {"type": "list"}
        elif parts[0] == "MBD":
            return {"type": "detail", "booking_id": int(parts[1])}
        elif parts[0] == "MBA":
            return {"type": "action", "action": parts[1], "booking_id": int(parts[2])}
        elif parts[0] == "MBT":
            return {"type": "tariff_select", "tariff": int(parts[1]), "booking_id": int(parts[2])}
        elif parts[0] == "MBB":
            return {"type": "back_detail", "booking_id": int(parts[1])}
        else:
            raise ValueError(f"Unknown callback format: {data}")

    def format_booking_button_label(booking: BookingBase) -> str:
        """Format booking for button label: 'DD.MM.YYYY HH:MM'"""
        return booking.start_date.strftime("%d.%m.%Y %H:%M")

Task 3: Create booking list command
  FILE: src/handlers/admin_handler.py
  ACTION: ADD function after get_booking_list() (around line 305)
  PATTERN: Similar to get_unpaid_bookings() but with inline keyboard
  DEPENDENCIES: get_future_bookings(), format_booking_button_label()
  CODE: |
    async def manage_bookings_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to show all future bookings as inline buttons"""
        chat_id = update.effective_chat.id
        if chat_id != ADMIN_CHAT_ID:
            await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
            return END

        bookings = get_future_bookings()

        if not bookings:
            await update.message.reply_text("🔍 Не найдено активных бронирований.")
            return END

        # Telegram limit: max 100 buttons
        bookings = bookings[:100]

        # Create inline keyboard (max 8 buttons per row, 1 per row for readability)
        keyboard = []
        for booking in bookings:
            label = string_helper.format_booking_button_label(booking)
            user = database_service.get_user_by_id(booking.user_id)
            # Add user contact to button for context
            button_text = f"{label} - {user.contact}"
            keyboard.append([
                InlineKeyboardButton(button_text, callback_data=f"MBD_{booking.id}")
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
            f"📋 <b>Управление бронированиями</b>\n\n"
            f"Всего активных броней: {len(bookings)}\n"
            f"Выберите бронирование для просмотра и управления:"
        )

        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

        LoggerService.info(__name__, "Admin opened booking management list", update)
        return END

Task 4: Create new booking_details_handler.py file
  FILE: src/handlers/booking_details_handler.py
  ACTION: CREATE new file with imports and initial structure
  PATTERN: Similar to feedback_handler.py structure
  CODE: |
    import sys
    import os
    from datetime import datetime
    from typing import Optional

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import (
        ContextTypes,
        ConversationHandler,
        CallbackQueryHandler,
        MessageHandler,
        filters,
    )
    from telegram.error import TelegramError

    from src.services.logger_service import LoggerService
    from src.services.database_service import DatabaseService
    from src.services.calculation_rate_service import CalculationRateService
    from src.decorators.callback_error_handler import safe_callback_query
    from src.helpers import string_helper, tariff_helper
    from src.config.config import ADMIN_CHAT_ID
    from src.constants import (
        END,
        MANAGE_BOOKING_DETAIL,
        MANAGE_CHANGE_PRICE,
        MANAGE_CHANGE_PREPAYMENT,
        MANAGE_CHANGE_TARIFF,
    )
    from src.models.enum.tariff import Tariff
    from db.models.booking import BookingBase
    from db.models.user import UserBase
    from src.handlers.admin_handler import get_future_bookings

    database_service = DatabaseService()
    calculation_rate_service = CalculationRateService()

    # All handler functions will be added here in subsequent tasks

Task 5: Create booking detail view handler
  FILE: src/handlers/booking_details_handler.py
  ACTION: ADD function after imports
  PATTERN: Similar to accept_booking_payment() for message formatting
  DEPENDENCIES: parse_manage_booking_callback(), generate_booking_info_message()
  CODE: |
    @safe_callback_query()
    async def show_booking_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show detailed booking information with action buttons"""
        await update.callback_query.answer()

        data = string_helper.parse_manage_booking_callback(update.callback_query.data)
        booking_id = data["booking_id"]

        booking = database_service.get_booking_by_id(booking_id)
        if not booking:
            await update.callback_query.edit_message_text("❌ Бронирование не найдено.")
            return END

        user = database_service.get_user_by_id(booking.user_id)

        # Generate detailed message
        message = (
            f"📋 <b>Детали бронирования #{booking.id}</b>\n\n"
            f"{string_helper.generate_booking_info_message(booking, user)}\n"
        )

        if booking.is_canceled:
            message = "⛔ <b>ОТМЕНЕНО</b>\n\n" + message

        # Create action buttons
        keyboard = [
            [InlineKeyboardButton("🔙 Назад к списку", callback_data="MBL")],
            [InlineKeyboardButton("❌ Отменить бронь", callback_data=f"MBA_cancel_{booking.id}")],
            [InlineKeyboardButton("📅 Перенести бронь", callback_data=f"MBA_reschedule_{booking.id}")],
            [InlineKeyboardButton("💰 Изменить стоимость", callback_data=f"MBA_price_{booking.id}")],
            [InlineKeyboardButton("💳 Изменить предоплату", callback_data=f"MBA_prepay_{booking.id}")],
            [InlineKeyboardButton("🎯 Изменить тариф", callback_data=f"MBA_tariff_{booking.id}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

        LoggerService.info(
            __name__,
            "Admin viewing booking detail",
            update,
            kwargs={"booking_id": booking_id}
        )

        return MANAGE_BOOKING_DETAIL

Task 6: Create back to list handler
  FILE: src/handlers/booking_details_handler.py
  ACTION: ADD function after show_booking_detail()
  PATTERN: Reuse manage_bookings_list() logic from admin_handler.py
  NOTE: get_future_bookings already imported in Task 4
  CODE: |
    @safe_callback_query()
    async def back_to_booking_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Return to booking list from detail view"""
        await update.callback_query.answer()

        bookings = get_future_bookings()

        if not bookings:
            await update.callback_query.edit_message_text("🔍 Не найдено активных бронирований.")
            return END

        bookings = bookings[:100]

        keyboard = []
        for booking in bookings:
            label = string_helper.format_booking_button_label(booking)
            user = database_service.get_user_by_id(booking.user_id)
            button_text = f"{label} - {user.contact}"
            keyboard.append([
                InlineKeyboardButton(button_text, callback_data=f"MBD_{booking.id}")
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
            f"📋 <b>Управление бронированиями</b>\n\n"
            f"Всего активных броней: {len(bookings)}\n"
            f"Выберите бронирование для просмотра и управления:"
        )

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

        return END

Task 7: Create cancel booking action
  FILE: src/handlers/booking_details_handler.py
  ACTION: ADD function after back_to_booking_list()
  PATTERN: Similar to existing cancel_booking() in admin_handler.py (lines 1083-1102)
  DEPENDENCIES: notify_customer_cancellation()
  CODE: |
    @safe_callback_query()
    async def start_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel booking and notify customer"""
        await update.callback_query.answer()

        data = string_helper.parse_manage_booking_callback(update.callback_query.data)
        booking_id = data["booking_id"]

        booking = database_service.get_booking_by_id(booking_id)
        user = database_service.get_user_by_id(booking.user_id)

        # Mark as canceled
        booking = database_service.update_booking(booking_id, is_canceled=True)

        # Notify customer
        await notify_customer_cancellation(context, booking, user)

        # Update admin message
        message = (
            f"✅ <b>Бронирование #{booking.id} отменено</b>\n\n"
            f"Клиент уведомлен: {user.contact}\n\n"
            f"<i>Используйте /manage_bookings для возврата к списку</i>"
        )

        await update.callback_query.edit_message_text(
            text=message,
            parse_mode="HTML"
        )

        LoggerService.info(
            __name__,
            "Admin canceled booking",
            update,
            kwargs={"booking_id": booking_id, "user_contact": user.contact}
        )

        return END

    async def notify_customer_cancellation(
        context: ContextTypes.DEFAULT_TYPE,
        booking: BookingBase,
        user: UserBase
    ):
        """Send cancellation notification to customer"""
        if not user.chat_id:
            LoggerService.warning(
                __name__,
                "Cannot notify customer - no chat_id",
                kwargs={"booking_id": booking.id, "user_id": user.id}
            )
            return

        try:
            message = (
                f"⚠️ <b>Внимание!</b> ⚠️\n\n"
                f"❌ <b>Ваше бронирование отменено администратором.</b>\n\n"
                f"📋 Детали:\n"
                f"Дата: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
                f"Тариф: {tariff_helper.get_name(booking.tariff)}\n\n"
                f"📞 Администратор свяжется с вами для уточнения деталей."
            )

            await context.bot.send_message(
                chat_id=user.chat_id,
                text=message,
                parse_mode="HTML"
            )

            LoggerService.info(
                __name__,
                "Customer notified of cancellation",
                kwargs={"booking_id": booking.id, "chat_id": user.chat_id}
            )
        except TelegramError as e:
            LoggerService.error(
                __name__,
                "Failed to notify customer of cancellation",
                exception=e,
                kwargs={"booking_id": booking.id, "chat_id": user.chat_id}
            )

Task 8: Create change price action
  FILE: src/handlers/booking_details_handler.py
  ACTION: ADD functions after notify_customer_cancellation()
  PATTERN: Reuse existing request_price_input() / handle_price_input() pattern from admin_handler.py (lines 818-926)
  CODE: |
    @safe_callback_query()
    async def start_change_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Ask admin to enter new price"""
        await update.callback_query.answer()

        data = string_helper.parse_manage_booking_callback(update.callback_query.data)
        booking_id = data["booking_id"]
        booking = database_service.get_booking_by_id(booking_id)
        user = database_service.get_user_by_id(booking.user_id)

        # Store context
        context.user_data["manage_booking_id"] = booking_id
        context.user_data["manage_user_chat_id"] = user.chat_id
        context.user_data["manage_old_value"] = booking.price

        keyboard = [[InlineKeyboardButton("Отмена", callback_data=f"MBB_{booking_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
            f"📝 <b>Изменение стоимости бронирования #{booking_id}</b>\n\n"
            f"Текущая стоимость: <b>{booking.price} руб.</b>\n\n"
            f"Введите новую стоимость цифрами (например: 450):"
        )

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

        return MANAGE_CHANGE_PRICE

    async def handle_price_change_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle price input from admin"""
        if update.effective_chat.id != ADMIN_CHAT_ID:
            return END

        booking_id = context.user_data.get("manage_booking_id")
        if not booking_id:
            return END

        price_text = update.message.text.strip()

        # Validate input
        try:
            new_price = float(price_text)
            if new_price <= 0:
                await update.message.reply_text("❌ Стоимость должна быть положительным числом. Попробуйте еще раз:")
                return MANAGE_CHANGE_PRICE
        except ValueError:
            await update.message.reply_text("❌ Неверный формат. Введите число (например: 450). Попробуйте еще раз:")
            return MANAGE_CHANGE_PRICE

        old_price = context.user_data.get("manage_old_value")

        # Update booking
        booking = database_service.update_booking(booking_id, price=new_price)
        user = database_service.get_user_by_id(booking.user_id)

        # Notify customer
        await notify_customer_price_change(context, booking, user, old_price)

        # Confirm to admin
        await update.message.reply_text(
            f"✅ Стоимость изменена: {old_price} → {new_price} руб.\n"
            f"Клиент уведомлен: {user.contact}\n\n"
            f"<i>Используйте /manage_bookings для возврата к списку</i>",
            parse_mode="HTML"
        )

        # Clear context
        context.user_data.pop("manage_booking_id", None)
        context.user_data.pop("manage_user_chat_id", None)
        context.user_data.pop("manage_old_value", None)

        LoggerService.info(
            __name__,
            "Admin changed booking price",
            update,
            kwargs={"booking_id": booking_id, "old_price": old_price, "new_price": new_price}
        )

        return END

    async def notify_customer_price_change(
        context: ContextTypes.DEFAULT_TYPE,
        booking: BookingBase,
        user: UserBase,
        old_price: float
    ):
        """Notify customer of price change"""
        if not user.chat_id:
            LoggerService.warning(
                __name__,
                "Cannot notify customer - no chat_id",
                kwargs={"booking_id": booking.id, "user_id": user.id}
            )
            return

        try:
            message = (
                f"📢 <b>Изменение стоимости бронирования</b>\n\n"
                f"Администратор изменил стоимость вашего бронирования:\n\n"
                f"📋 Детали:\n"
                f"Дата: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n"
                f"Тариф: {tariff_helper.get_name(booking.tariff)}\n\n"
                f"💰 Старая стоимость: {old_price} руб.\n"
                f"💰 Новая стоимость: {booking.price} руб.\n\n"
                f"По всем вопросам свяжитесь с администратором."
            )

            await context.bot.send_message(
                chat_id=user.chat_id,
                text=message,
                parse_mode="HTML"
            )

            LoggerService.info(
                __name__,
                "Customer notified of price change",
                kwargs={"booking_id": booking.id, "chat_id": user.chat_id}
            )
        except TelegramError as e:
            LoggerService.error(
                __name__,
                "Failed to notify customer of price change",
                exception=e,
                kwargs={"booking_id": booking.id, "chat_id": user.chat_id}
            )

Task 9: Create change prepayment action
  FILE: src/handlers/booking_details_handler.py
  ACTION: ADD functions after notify_customer_price_change()
  PATTERN: Nearly identical to Task 8, change "price" to "prepayment"
  CODE: |
    # Similar structure to Task 8 but for prepayment_price field
    # Functions: start_change_prepayment(), handle_prepayment_change_input(), notify_customer_prepayment_change()
    # Use MANAGE_CHANGE_PREPAYMENT state
    # Update prepayment_price field instead of price

Task 10: Create change tariff action
  FILE: src/handlers/booking_details_handler.py
  ACTION: ADD functions after notify_customer_prepayment_change()
  PATTERN: Similar to create_promocode tariff selection in admin_handler.py (lines 1583-1644)
  DEPENDENCIES: Tariff enum, calculation_rate_service
  CODE: |
    @safe_callback_query()
    async def start_change_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show tariff selection buttons"""
        await update.callback_query.answer()

        data = string_helper.parse_manage_booking_callback(update.callback_query.data)
        booking_id = data["booking_id"]
        booking = database_service.get_booking_by_id(booking_id)
        user = database_service.get_user_by_id(booking.user_id)

        # Store context
        context.user_data["manage_booking_id"] = booking_id
        context.user_data["manage_user_chat_id"] = user.chat_id
        context.user_data["manage_old_value"] = booking.tariff

        # Create tariff selection keyboard
        keyboard = []
        for tariff in Tariff:
            tariff_name = tariff_helper.get_name(tariff)
            keyboard.append([
                InlineKeyboardButton(
                    f"🎯 {tariff_name}",
                    callback_data=f"MBT_{tariff.value}_{booking_id}"
                )
            ])

        keyboard.append([InlineKeyboardButton("Отмена", callback_data=f"MBB_{booking_id}")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        current_tariff = tariff_helper.get_name(booking.tariff)
        message = (
            f"📝 <b>Изменение тарифа бронирования #{booking_id}</b>\n\n"
            f"Текущий тариф: <b>{current_tariff}</b>\n\n"
            f"Выберите новый тариф:"
        )

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

        return MANAGE_CHANGE_TARIFF

    @safe_callback_query()
    async def handle_tariff_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle tariff selection and recalculate price"""
        await update.callback_query.answer()

        data = string_helper.parse_manage_booking_callback(update.callback_query.data)
        new_tariff_value = data["tariff"]
        booking_id = data["booking_id"]

        new_tariff = Tariff(new_tariff_value)
        old_tariff = context.user_data.get("manage_old_value")

        booking = database_service.get_booking_by_id(booking_id)
        user = database_service.get_user_by_id(booking.user_id)

        # Recalculate price with new tariff
        old_price = booking.price
        new_price = calculation_rate_service.calculate_rate(
            start_date=booking.start_date,
            end_date=booking.end_date,
            tariff=new_tariff,
            number_of_guests=booking.number_of_guests,
            has_sauna=booking.has_sauna,
            has_photoshoot=booking.has_photoshoot,
            gift_id=booking.gift_id,
            promocode_id=booking.promocode_id
        )

        # Update booking
        booking = database_service.update_booking(
            booking_id,
            tariff=new_tariff,
            price=new_price
        )

        # Notify customer
        await notify_customer_tariff_change(context, booking, user, old_tariff, old_price)

        # Confirm to admin
        old_tariff_name = tariff_helper.get_name(old_tariff)
        new_tariff_name = tariff_helper.get_name(new_tariff)

        message = (
            f"✅ <b>Тариф изменен</b>\n\n"
            f"📋 Бронирование #{booking_id}\n"
            f"👤 Клиент: {user.contact}\n\n"
            f"🎯 Тариф: {old_tariff_name} → {new_tariff_name}\n"
            f"💰 Стоимость: {old_price} → {new_price} руб.\n\n"
            f"Клиент уведомлен.\n\n"
            f"<i>Используйте /manage_bookings для возврата к списку</i>"
        )

        await update.callback_query.edit_message_text(
            text=message,
            parse_mode="HTML"
        )

        # Clear context
        context.user_data.pop("manage_booking_id", None)
        context.user_data.pop("manage_user_chat_id", None)
        context.user_data.pop("manage_old_value", None)

        LoggerService.info(
            __name__,
            "Admin changed booking tariff",
            update,
            kwargs={
                "booking_id": booking_id,
                "old_tariff": old_tariff.name,
                "new_tariff": new_tariff.name,
                "old_price": old_price,
                "new_price": new_price
            }
        )

        return END

    async def notify_customer_tariff_change(
        context: ContextTypes.DEFAULT_TYPE,
        booking: BookingBase,
        user: UserBase,
        old_tariff: Tariff,
        old_price: float
    ):
        """Notify customer of tariff change"""
        if not user.chat_id:
            LoggerService.warning(
                __name__,
                "Cannot notify customer - no chat_id",
                kwargs={"booking_id": booking.id, "user_id": user.id}
            )
            return

        try:
            old_tariff_name = tariff_helper.get_name(old_tariff)
            new_tariff_name = tariff_helper.get_name(booking.tariff)

            message = (
                f"📢 <b>Изменение тарифа бронирования</b>\n\n"
                f"Администратор изменил тариф вашего бронирования:\n\n"
                f"📋 Детали:\n"
                f"Дата: {booking.start_date.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"🎯 Старый тариф: {old_tariff_name}\n"
                f"🎯 Новый тариф: {new_tariff_name}\n\n"
                f"💰 Старая стоимость: {old_price} руб.\n"
                f"💰 Новая стоимость: {booking.price} руб.\n\n"
                f"По всем вопросам свяжитесь с администратором."
            )

            await context.bot.send_message(
                chat_id=user.chat_id,
                text=message,
                parse_mode="HTML"
            )

            LoggerService.info(
                __name__,
                "Customer notified of tariff change",
                kwargs={"booking_id": booking.id, "chat_id": user.chat_id}
            )
        except TelegramError as e:
            LoggerService.error(
                __name__,
                "Failed to notify customer of tariff change",
                exception=e,
                kwargs={"booking_id": booking.id, "chat_id": user.chat_id}
            )

Task 11: Create reschedule action (simplified - just notification, detailed implementation later)
  FILE: src/handlers/booking_details_handler.py
  ACTION: ADD placeholder function after notify_customer_tariff_change()
  NOTE: Full reschedule requires date/time picker integration - out of scope for initial PR
  CODE: |
    @safe_callback_query()
    async def start_reschedule_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Reschedule booking - future implementation"""
        await update.callback_query.answer()

        data = string_helper.parse_manage_booking_callback(update.callback_query.data)
        booking_id = data["booking_id"]

        message = (
            f"🚧 <b>Функция в разработке</b>\n\n"
            f"Перенос бронирования будет добавлен в следующем обновлении.\n"
            f"Используйте существующий функционал изменения даты через меню пользователя.\n\n"
            f"<i>Используйте /manage_bookings для возврата к списку</i>"
        )

        await update.callback_query.edit_message_text(
            text=message,
            parse_mode="HTML"
        )

        return END

Task 12: Create conversation handler and get_handler() export
  FILE: src/handlers/booking_details_handler.py
  ACTION: ADD function at end of file
  PATTERN: Similar to get_create_promocode_handler() in admin_handler.py (lines 1666-1727)
  NOTE: Export via get_handler() to match other handlers pattern (feedback_handler, etc.)
  CODE: |
    def get_handler() -> ConversationHandler:
        """Returns ConversationHandler for booking details management"""
        handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(show_booking_detail, pattern="^MBD_\\d+$"),
            ],
            states={
                MANAGE_BOOKING_DETAIL: [
                    # Action handlers
                    CallbackQueryHandler(start_cancel_booking, pattern="^MBA_cancel_\\d+$"),
                    CallbackQueryHandler(start_reschedule_booking, pattern="^MBA_reschedule_\\d+$"),
                    CallbackQueryHandler(start_change_price, pattern="^MBA_price_\\d+$"),
                    CallbackQueryHandler(start_change_prepayment, pattern="^MBA_prepay_\\d+$"),
                    CallbackQueryHandler(start_change_tariff, pattern="^MBA_tariff_\\d+$"),
                    # Back to list
                    CallbackQueryHandler(back_to_booking_list, pattern="^MBL$"),
                ],
                MANAGE_CHANGE_PRICE: [
                    MessageHandler(
                        filters.Chat(chat_id=ADMIN_CHAT_ID) & filters.TEXT & ~filters.COMMAND,
                        handle_price_change_input,
                    ),
                    CallbackQueryHandler(show_booking_detail, pattern="^MBB_\\d+$"),
                ],
                MANAGE_CHANGE_PREPAYMENT: [
                    MessageHandler(
                        filters.Chat(chat_id=ADMIN_CHAT_ID) & filters.TEXT & ~filters.COMMAND,
                        handle_prepayment_change_input,
                    ),
                    CallbackQueryHandler(show_booking_detail, pattern="^MBB_\\d+$"),
                ],
                MANAGE_CHANGE_TARIFF: [
                    CallbackQueryHandler(handle_tariff_selection, pattern="^MBT_\\d+_\\d+$"),
                    CallbackQueryHandler(show_booking_detail, pattern="^MBB_\\d+$"),
                ],
            },
            fallbacks=[
                CallbackQueryHandler(back_to_booking_list, pattern="^MBL$"),
            ],
        )
        return handler

Task 13: Register command and handlers in main.py
  FILE: src/main.py
  ACTION: MODIFY imports, admin_commands list, and add handler registration
  LOCATION: Lines 12 (imports), 27-38 (admin_commands), lines 101-128 (handler registration)
  CODE: |
    # Add to imports (line 12):
    from src.handlers import menu_handler, admin_handler, feedback_handler, booking_details_handler

    # In set_commands() function, add to admin_commands list (around line 28):
    BotCommand("manage_bookings", "Управление бронированиями"),

    # In __main__ block, after other admin handlers (around line 107):
    application.add_handler(booking_details_handler.get_handler())
    application.add_handler(
        CommandHandler("manage_bookings", admin_handler.manage_bookings_list)
    )
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
python -m py_compile src/handlers/admin_handler.py
python -m py_compile src/handlers/booking_details_handler.py
python -m py_compile src/helpers/string_helper.py
python -m py_compile src/constants.py
python -m py_compile src/main.py

# Expected: No syntax errors. If errors, READ the error and fix.
```

### Level 2: Manual Testing (No automated tests for Telegram bots in this project)
```bash
# Start the bot in debug mode
export ENV=debug
python src/main.py

# Test sequence:
# 1. Send /manage_bookings as admin
#    - Expected: List of bookings as buttons (or "no bookings" message)
#
# 2. Click a booking button
#    - Expected: Detail view with 6 action buttons + back button
#
# 3. Click "🔙 Назад к списку"
#    - Expected: Return to booking list
#
# 4. Click a booking, then "❌ Отменить бронь"
#    - Expected: Booking marked as canceled
#    - Expected: Customer receives notification (check customer chat)
#    - Expected: Admin sees confirmation
#
# 5. Click a booking, then "💰 Изменить стоимость"
#    - Expected: Admin prompted for new price
#    - Send: "500"
#    - Expected: Price updated, customer notified, admin sees confirmation
#
# 6. Click a booking, then "💳 Изменить предоплату"
#    - Expected: Similar flow to price change
#
# 7. Click a booking, then "🎯 Изменить тариф"
#    - Expected: Tariff selection buttons
#    - Click a tariff
#    - Expected: Tariff + price updated, customer notified
#
# 8. Test error cases:
#    - Send non-numeric price (e.g., "abc")
#      - Expected: Error message, prompt to retry
#    - Send negative price (e.g., "-100")
#      - Expected: Error message, prompt to retry
#    - Test with booking where user has no chat_id
#      - Expected: Action succeeds, warning logged (no notification sent)

# Check logs for errors
tail -f logs/app.log
```

### Level 3: Database Verification
```bash
# Connect to database and verify changes
sqlite3 test_the_secret_house.db

# Check booking was canceled
SELECT id, is_canceled, price, tariff FROM booking WHERE id = <booking_id>;

# Check price was updated
SELECT id, price, prepayment_price FROM booking WHERE id = <booking_id>;

# Exit sqlite
.exit
```

## Final Validation Checklist
- [ ] All Python files compile without syntax errors
- [ ] Admin can open booking list with /manage_bookings
- [ ] Booking list shows correct date/time format
- [ ] Clicking booking opens detail view
- [ ] All 6 action buttons work correctly
- [ ] Back button returns to list
- [ ] Cancel action updates database and notifies customer
- [ ] Price change validates input and notifies customer
- [ ] Prepayment change validates input and notifies customer
- [ ] Tariff change recalculates price and notifies customer
- [ ] Customer notifications include booking details
- [ ] Error handling works for invalid inputs
- [ ] Logs show all actions with booking_id and user info
- [ ] Non-admin users get permission denied for /manage_bookings
- [ ] Maximum 100 bookings shown (Telegram limit)
- [ ] No crashes or unhandled exceptions

---

## Anti-Patterns to Avoid
- ❌ Don't exceed 100 buttons - Telegram API hard limit
- ❌ Don't forget to answer() callback queries - causes "query too old" errors
- ❌ Don't send messages without checking user.chat_id exists
- ❌ Don't hardcode user-facing strings - keep Russian messages consistent
- ❌ Don't skip input validation - always check numeric inputs
- ❌ Don't forget to clear context.user_data after actions
- ❌ Don't use time.sleep() - always use await asyncio.sleep()
- ❌ Don't forget to update calendar when rescheduling (future task)
- ❌ Don't ignore TelegramError - log and handle gracefully
- ❌ Don't create new patterns - reuse existing admin_handler patterns

---

## PRP Confidence Score

**Score: 9/10**

**Rationale:**
- ✅ All necessary context provided (existing patterns, models, helpers)
- ✅ Clear implementation steps with code pseudocode
- ✅ References to specific lines in existing code
- ✅ Known gotchas and limitations documented
- ✅ Telegram API limits researched and addressed
- ✅ Validation strategy defined (manual testing)
- ⚠️ Reschedule action simplified (date picker integration complex)
- ✅ Customer notification patterns clear
- ✅ Error handling patterns documented
- ✅ Database update patterns clear

**One-pass implementation likelihood: HIGH** - All patterns exist in codebase, clear references provided, no complex external dependencies (except future reschedule feature).

---

## Files Modified/Created Summary

### New Files (1)
- **`src/handlers/booking_details_handler.py`** - Complete new handler for booking detail view and all actions

### Modified Files (4)
- **`src/constants.py`** - Add 6 new conversation state constants
- **`src/helpers/string_helper.py`** - Add 2 helper functions for callback parsing and button labels
- **`src/handlers/admin_handler.py`** - Add 1 command function (manage_bookings_list)
- **`src/main.py`** - Update imports, admin commands, and register new handlers

### Total Lines of Code: ~600-700 lines (mostly in booking_details_handler.py)
