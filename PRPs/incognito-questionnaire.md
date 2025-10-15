# PRP: Incognito Tariffs Pre-Payment Questionnaire

## Goal
Implement a multi-step questionnaire for all "Incognito" tariffs (INCOGNITA_DAY, INCOGNITA_HOURS, INCOGNITA_WORKER) that collects customer preferences for complimentary wine and premium transfer service **before** the payment step in the booking flow.

## Why
- **Premium Service Experience**: Incognito tariffs are premium offerings that include complimentary wine/snacks and optional business-class transfer service
- **Personalization**: Collect guest preferences to provide tailored service (wine type, transfer address)
- **Business Logic**: Only Incognito tariff customers receive these premium services
- **Integration**: Seamlessly integrates into existing booking flow between comment and payment steps
- **Data Collection**: Store preferences in booking record for service preparation

## What
Add two sequential questions after the booking comment step (line 665-690 in booking_handler.py) but before payment (line 789-843) for Incognito tariff bookings:

**Question 1: Wine Preference**
- Message: "Мы бесплатно подготавливаем вино и легкие закуски. Какое вино вы предпочитаете?"
- Options: 5 inline buttons
  - "Не нужно вино"
  - "Сладкое"
  - "Полусладкое"
  - "Сухое"
  - "Полусухое"

**Question 2: Transfer Service**
- Message: "Мы бесплатно предлагаем трансфер из дома и в дом на авто бизнес класса. Введите Ваш адрес."
- Options:
  - Inline button: "Не нужно" (skip to next step)
  - Text input: User types address (free-form text)

### Success Criteria
- [x] Questions appear ONLY for Incognito tariffs (INCOGNITA_DAY, INCOGNITA_HOURS, INCOGNITA_WORKER)
- [x] Questions appear after comment step and before payment step
- [x] Wine preference stored in database (new field: `wine_preference`)
- [x] Transfer address stored in database (new field: `transfer_address`)
- [x] Both fields nullable (optional)
- [x] Questions use existing patterns from booking_handler.py
- [x] Proper state management via BookingStep enum
- [x] Redis storage during booking flow
- [x] Logging for all actions
- [x] Error handling for invalid inputs

## All Needed Context

### Documentation & References

```yaml
# MUST READ - Include these in your context window

- url: https://docs.python-telegram-bot.org/en/stable/telegram.ext.conversationhandler.html
  why: ConversationHandler pattern for state transitions
  critical: Return next state constant from handlers

- url: https://core.telegram.org/bots/api#inlinekeyboardbutton
  why: InlineKeyboardButton and InlineKeyboardMarkup for button layouts
  critical: callback_data has 64-byte limit

- file: src/handlers/booking_handler.py
  why: Main reference for all patterns - handler structure, state transitions, Redis usage
  lines: 105-1661 (entire file structure)
  pattern: |
    - Handler registration in get_handler() (lines 56-95)
    - State-based message functions (e.g., sauna_message, photoshoot_message)
    - CallbackQueryHandler pattern with regex patterns
    - MessageHandler for text input
    - Redis field updates via redis_service.update_booking_field()
    - Navigation service for safe message editing

- file: src/models/enum/booking_step.py
  why: Add new states for wine and transfer questionnaire
  pattern: WINE_PREFERENCE = "WINE_PREFERENCE", TRANSFER_ADDRESS = "TRANSFER_ADDRESS"

- file: src/models/booking_draft.py
  why: Add wine_preference and transfer_address fields
  pattern: Optional[str] = None

- file: src/constants.py
  why: State constants for conversation handler
  note: Uses ConversationHandler.END, custom state strings

- file: db/models/booking.py
  why: Add database columns for wine_preference and transfer_address

- file: src/services/redis_service.py
  why: Pattern for storing booking fields during conversation
  pattern: update_booking_field(update, field_name, value)
```

### Current Codebase Tree (Relevant Parts)

```bash
src/
├── main.py                              # Register handlers
├── constants.py                         # State constants (MODIFY)
├── handlers/
│   └── booking_handler.py               # Main booking flow (MODIFY)
├── models/
│   ├── enum/
│   │   ├── booking_step.py              # Booking states enum (MODIFY)
│   │   └── tariff.py                    # Tariff enum (REFERENCE)
│   └── booking_draft.py                 # Booking data model (MODIFY)
├── services/
│   ├── redis_service.py                 # Redis operations (REFERENCE)
│   ├── navigation_service.py            # Safe message editing (REFERENCE)
│   └── logger_service.py                # Logging (REFERENCE)
└── helpers/
    └── string_helper.py                 # String utilities (REFERENCE)

db/
└── models/
    └── booking.py                       # Database model (MODIFY)

alembic/
└── versions/                            # Database migrations (ADD NEW)
```

### Desired Codebase Tree with Files to Be Added

```bash
src/
├── handlers/
│   └── booking_handler.py               # MODIFY: Add wine_preference_message(),
│                                        #         handle_wine_preference(),
│                                        #         transfer_message(),
│                                        #         handle_transfer_input()
├── models/
│   ├── enum/
│   │   └── booking_step.py              # MODIFY: Add WINE_PREFERENCE, TRANSFER_ADDRESS
│   └── booking_draft.py                 # MODIFY: Add wine_preference, transfer_address fields
└── constants.py                         # MODIFY: Add INCOGNITO_WINE, INCOGNITO_TRANSFER states

db/
└── models/
    └── booking.py                       # MODIFY: Add wine_preference, transfer_address columns

alembic/
└── versions/
    └── XXXXXX_add_incognito_preferences.py  # NEW: Migration file
```

### Known Gotchas & Library Quirks

```python
# CRITICAL: python-telegram-bot v20+ requires async/await
# All handler functions MUST be async

# PATTERN: Callback data format in booking_handler.py
# Format: "PREFIX_VALUE" where PREFIX identifies handler, VALUE is the data
# Example: "BOOKING-WINE_sweet" for wine preference

# GOTCHA: callback_data limit is 64 bytes
# Keep prefixes short: "BOOKING-WINE_" leaves 50+ bytes for value

# PATTERN: State transitions in booking_handler.py
# Each handler function returns next state constant
# Use BookingStep enum values for navigation_step tracking

# CRITICAL: RedisService pattern (lines 24-48 in booking_handler.py)
# redis_service.update_booking_field(update, "field_name", value)
# Automatically handles serialization/deserialization

# PATTERN: Checking tariff type (lines 191-209)
if (
    tariff == Tariff.INCOGNITA_DAY
    or tariff == Tariff.INCOGNITA_HOURS
    or tariff == Tariff.INCOGNITA_WORKER
):
    # Incognito-specific logic here

# PATTERN: Navigation service for safe message editing (line 167-171)
await navigation_service.safe_edit_message_text(
    callback_query=update.callback_query,
    text="<b>Message text</b>",
    reply_markup=reply_markup,
)

# PATTERN: Logging pattern (line 185, 229, etc.)
LoggerService.info(__name__, "Action description", update, kwargs={"key": "value"})

# PATTERN: Message handler for text input (see question_handler.py reference in feedback PRP)
# Use MessageHandler(filters.TEXT & ~filters.COMMAND, handler_function)

# GOTCHA: Text input handlers need state tracking
# Store current question in Redis to route correctly

# CRITICAL: Database operations use DatabaseService singleton
# Pattern at line 1574: database_service.add_booking(...)

# PATTERN: Back navigation (lines 98-102)
# Return to menu and clear Redis booking data
```

## Implementation Blueprint

### Data Models and Structure

```python
# 1. src/models/enum/booking_step.py (ADD new enum values)
class BookingStep(Enum):
    # ... existing values ...
    WINE_PREFERENCE = "WINE_PREFERENCE"
    TRANSFER_ADDRESS = "TRANSFER_ADDRESS"

# 2. src/models/booking_draft.py (ADD new fields)
@dataclass_json
@dataclass
class BookingDraft:
    # ... existing fields ...
    wine_preference: Optional[str] = None
    transfer_address: Optional[str] = None

# 3. db/models/booking.py (ADD new columns)
class BookingBase(Base):
    # ... existing columns ...
    wine_preference = Column(String, nullable=True)
    transfer_address = Column(String, nullable=True)

# 4. src/constants.py (ADD new state constants)
# States for incognito questionnaire
INCOGNITO_WINE = "INCOGNITO_WINE"
INCOGNITO_TRANSFER = "INCOGNITO_TRANSFER"
```

### List of Tasks to Complete the PRP (In Order)

```yaml
Task 1: Update BookingStep enum
  FILE: src/models/enum/booking_step.py
  ACTION: ADD two new enum values
  CODE: |
    WINE_PREFERENCE = "WINE_PREFERENCE"
    TRANSFER_ADDRESS = "TRANSFER_ADDRESS"
  WHY: Track questionnaire progress in booking flow

Task 2: Update BookingDraft model
  FILE: src/models/booking_draft.py
  ACTION: ADD two new optional fields after existing fields
  CODE: |
    wine_preference: Optional[str] = None
    transfer_address: Optional[str] = None
  WHY: Store questionnaire responses in Redis during booking

Task 3: Update constants.py
  FILE: src/constants.py
  ACTION: ADD two new state constants after BOOKING_COMMENT line
  CODE: |
    INCOGNITO_WINE = "INCOGNITO_WINE"
    INCOGNITO_TRANSFER = "INCOGNITO_TRANSFER"
  WHY: ConversationHandler state management

Task 4: Add CallbackQueryHandlers to get_handler()
  FILE: src/handlers/booking_handler.py
  LOCATION: Inside get_handler() function (around line 75)
  ACTION: ADD two new handlers after comment handler
  CODE: |
    CallbackQueryHandler(handle_wine_preference, pattern=f"^BOOKING-WINE_(.+|{END})$"),
    CallbackQueryHandler(handle_transfer_skip, pattern=f"^BOOKING-TRANSFER_({SKIP}|{END})$"),
  WHY: Route wine button clicks and transfer skip button

Task 5: Add MessageHandler for transfer address input
  FILE: src/handlers/booking_handler.py
  LOCATION: In get_handler() function, after CallbackQueryHandlers
  NOTE: MessageHandler for text input needs special handling
  ACTION: Modify existing text input handlers OR create state-specific routing
  PATTERN: Check navigation_step to route to correct handler
  WHY: Handle transfer address text input

Task 6: Create wine_preference_message() function
  FILE: src/handlers/booking_handler.py
  LOCATION: After comment_message() function (around line 1378)
  ACTION: CREATE new async function
  WHY: Display wine preference question with 5 buttons

Task 7: Create handle_wine_preference() function
  FILE: src/handlers/booking_handler.py
  LOCATION: After wine_preference_message()
  ACTION: CREATE new async function
  WHY: Process wine selection and transition to transfer question

Task 8: Create transfer_message() function
  FILE: src/handlers/booking_handler.py
  LOCATION: After handle_wine_preference()
  ACTION: CREATE new async function
  WHY: Display transfer service question with skip button

Task 9: Create handle_transfer_skip() function
  FILE: src/handlers/booking_handler.py
  LOCATION: After transfer_message()
  ACTION: CREATE new async function
  WHY: Handle "Не нужно" button click for transfer

Task 10: Create handle_transfer_input() function
  FILE: src/handlers/booking_handler.py
  LOCATION: After handle_transfer_skip()
  ACTION: CREATE new async function
  WHY: Process address text input

Task 11: Modify write_comment() function
  FILE: src/handlers/booking_handler.py
  LOCATION: Line 674-691 (write_comment function)
  ACTION: MODIFY flow to check tariff and route accordingly
  CHANGE: Replace "return await confirm_pay(update, context)" with conditional routing
  CODE: |
    booking = redis_service.get_booking(update)
    if (
        booking.tariff == Tariff.INCOGNITA_DAY
        or booking.tariff == Tariff.INCOGNITA_HOURS
        or booking.tariff == Tariff.INCOGNITA_WORKER
    ):
        return await wine_preference_message(update, context)
    else:
        return await confirm_pay(update, context)
  WHY: Inject questionnaire into Incognito booking flow only

Task 12: Update database model
  FILE: db/models/booking.py
  LOCATION: Inside BookingBase class
  ACTION: ADD two new columns
  CODE: |
    wine_preference = Column(String, nullable=True)
    transfer_address = Column(String, nullable=True)
  WHY: Persist questionnaire responses in database

Task 13: Create database migration
  COMMAND: ALEMBIC_OFFLINE=true uv run alembic revision --autogenerate -m "Add incognito questionnaire fields"
  FILE: alembic/versions/XXXXXX_add_incognito_questionnaire_fields.py
  ACTION: Review auto-generated migration, ensure nullable=True
  WHY: Update database schema

Task 14: Update save_booking_information() function
  FILE: src/handlers/booking_handler.py
  LOCATION: Line 1548-1614 (save_booking_information function)
  ACTION: MODIFY database_service.add_booking() call to include new fields
  NOTE: add_booking signature needs to be updated in DatabaseService
  WHY: Save questionnaire responses to database

Task 15: Update DatabaseService.add_booking() method
  FILE: src/services/database_service.py
  LOCATION: add_booking() method signature
  ACTION: ADD wine_preference and transfer_address parameters
  WHY: Accept new fields for database insertion
```

### Per Task Pseudocode

#### Task 6: wine_preference_message() Pseudocode

```python
# src/handlers/booking_handler.py (after comment_message function)

async def wine_preference_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display wine preference question for Incognito tariffs.

    Shows 5 wine options + back button.
    Stores navigation step in Redis.
    """
    # PATTERN: Update navigation step (see line 675, 889, etc.)
    redis_service.update_booking_field(update, "navigation_step", BookingStep.WINE_PREFERENCE)

    # PATTERN: Create inline keyboard with wine options
    # Format: 1 option per row for clarity
    keyboard = [
        [InlineKeyboardButton("Не нужно вино", callback_data="BOOKING-WINE_none")],
        [InlineKeyboardButton("Сладкое", callback_data="BOOKING-WINE_sweet")],
        [InlineKeyboardButton("Полусладкое", callback_data="BOOKING-WINE_semi_sweet")],
        [InlineKeyboardButton("Сухое", callback_data="BOOKING-WINE_dry")],
        [InlineKeyboardButton("Полусухое", callback_data="BOOKING-WINE_semi_dry")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-WINE_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "🍷 <b>Мы бесплатно подготавливаем вино и легкие закуски.</b>\n\n"
        "Какое вино вы предпочитаете?"
    )

    # PATTERN: Check if callback or message context (see line 241, 908, etc.)
    if update.message == None:
        await update.callback_query.answer()
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
            reply_markup=reply_markup,
        )
    else:
        await update.message.reply_text(
            text=message, parse_mode="HTML", reply_markup=reply_markup
        )

    # PATTERN: Return state constant for conversation handler
    return INCOGNITO_WINE


async def handle_wine_preference(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle wine preference button click.

    Extracts wine choice from callback_data.
    Stores in Redis.
    Transitions to transfer question.
    """
    await update.callback_query.answer()

    # PATTERN: Extract data from callback (see line 179, 290, etc.)
    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    # Store wine preference
    wine_preference = data  # "none", "sweet", "semi_sweet", "dry", "semi_dry"
    redis_service.update_booking_field(update, "wine_preference", wine_preference)

    # PATTERN: Logging (see line 298, 314, etc.)
    LoggerService.info(
        __name__,
        "Wine preference selected",
        update,
        kwargs={"wine_preference": wine_preference},
    )

    # Transition to transfer question
    return await transfer_message(update, context)
```

#### Task 8-10: Transfer Service Pseudocode

```python
async def transfer_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display transfer service question for Incognito tariffs.

    Shows message asking for address with "Не нужно" button.
    User can either click button or type address.
    """
    redis_service.update_booking_field(
        update, "navigation_step", BookingStep.TRANSFER_ADDRESS
    )

    # PATTERN: Simple keyboard with skip option (see line 1366-1369)
    keyboard = [
        [InlineKeyboardButton("Не нужно", callback_data=f"BOOKING-TRANSFER_{SKIP}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"BOOKING-TRANSFER_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "🚗 <b>Мы бесплатно предлагаем трансфер из дома и в дом на авто бизнес класса.</b>\n\n"
        "Введите Ваш адрес или нажмите 'Не нужно':"
    )

    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text=message,
        reply_markup=reply_markup,
    )

    return INCOGNITO_TRANSFER


async def handle_transfer_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle "Не нужно" button click for transfer.

    Stores None/empty for transfer_address.
    Proceeds to payment step.
    """
    await update.callback_query.answer()

    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    # Store empty/none for transfer
    redis_service.update_booking_field(update, "transfer_address", None)

    LoggerService.info(__name__, "Transfer service declined", update)

    # PATTERN: Proceed to payment step (see line 273, 690)
    return await confirm_pay(update, context)


async def handle_transfer_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle text input for transfer address.

    Called when user types address instead of clicking button.
    Validates input is not empty.
    Stores address and proceeds to payment.
    """
    # PATTERN: Text input handling (see line 257-285 check_user_contact)
    if update.message and update.message.text:
        address = update.message.text.strip()

        # Validate address is not empty
        if not address or len(address) < 5:
            LoggerService.warning(__name__, "Transfer address too short", update)
            await update.message.reply_text(
                "❌ <b>Ошибка!</b>\n"
                "Адрес слишком короткий. Пожалуйста, введите полный адрес.\n\n"
                "Или нажмите 'Не нужно', если трансфер не требуется.",
                parse_mode="HTML",
            )
            return INCOGNITO_TRANSFER

        # Store address
        redis_service.update_booking_field(update, "transfer_address", address)

        LoggerService.info(
            __name__,
            "Transfer address saved",
            update,
            kwargs={"address": address[:50]},  # Log first 50 chars only
        )

        # Proceed to payment
        return await confirm_pay(update, context)

    return INCOGNITO_TRANSFER


# CRITICAL: Routing text input to correct handler
# Need to modify existing message handler OR check navigation_step
#
# Option A: Check navigation_step in a routing function
# Option B: Add MessageHandler specifically for INCOGNITO_TRANSFER state in get_handler()
#
# Recommendation: Option B - cleaner state management
# Add to get_handler():
#   MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transfer_input)
# This will be routed by ConversationHandler based on current state
```

#### Task 11: Modify write_comment() Function

```python
# MODIFY: src/handlers/booking_handler.py lines 674-691

async def write_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_service.update_booking_field(update, "navigation_step", BookingStep.COMMENT)

    if update.message == None:
        if update.callback_query:
            await update.callback_query.answer()
            data = string_helper.get_callback_data(update.callback_query.data)
            if data == str(END):
                return await back_navigation(update, context)
    else:
        booking_comment = update.message.text
        redis_service.update_booking_field(update, "booking_comment", booking_comment)
        LoggerService.info(
            __name__, "Write comment", update, kwargs={"comment": booking_comment}
        )

    # NEW: Check if Incognito tariff and route to questionnaire
    booking = redis_service.get_booking(update)
    if (
        booking.tariff == Tariff.INCOGNITA_DAY
        or booking.tariff == Tariff.INCOGNITA_HOURS
        or booking.tariff == Tariff.INCOGNITA_WORKER
    ):
        return await wine_preference_message(update, context)
    else:
        return await confirm_pay(update, context)
```

#### Task 14-15: Update Database Storage

```python
# MODIFY: src/handlers/booking_handler.py save_booking_information() (line 1574)

cache_booking = redis_service.get_booking(update)
booking = database_service.add_booking(
    cache_booking.user_contact,
    cache_booking.start_booking_date,
    cache_booking.finish_booking_date,
    cache_booking.tariff,
    cache_booking.is_photoshoot_included,
    cache_booking.is_sauna_included,
    cache_booking.is_white_room_included,
    cache_booking.is_green_room_included,
    cache_booking.is_secret_room_included,
    cache_booking.number_of_guests,
    cache_booking.price,
    cache_booking.booking_comment,
    chat_id,
    cache_booking.gift_id,
    cache_booking.wine_preference,      # NEW
    cache_booking.transfer_address,      # NEW
)

# MODIFY: src/services/database_service.py add_booking() signature
def add_booking(
    self,
    # ... existing parameters ...
    gift_id: Optional[int] = None,
    wine_preference: Optional[str] = None,     # NEW
    transfer_address: Optional[str] = None,     # NEW
) -> BookingBase:
    # ... existing code ...
    booking = BookingBase(
        # ... existing fields ...
        wine_preference=wine_preference,        # NEW
        transfer_address=transfer_address,       # NEW
    )
```

### Integration Points

```yaml
HANDLER REGISTRATION:
  - file: src/handlers/booking_handler.py
  - function: get_handler()
  - add: CallbackQueryHandler for wine preference
  - add: CallbackQueryHandler for transfer skip
  - add: MessageHandler for transfer address input (state-specific)

STATE MANAGEMENT:
  - enum: BookingStep.WINE_PREFERENCE, BookingStep.TRANSFER_ADDRESS
  - constants: INCOGNITO_WINE, INCOGNITO_TRANSFER
  - flow: COMMENT → WINE_PREFERENCE → TRANSFER_ADDRESS → CONFIRM_BOOKING

REDIS STORAGE:
  - fields: wine_preference, transfer_address
  - methods: redis_service.update_booking_field()
  - pattern: Temporary storage during booking flow

DATABASE STORAGE:
  - table: bookings
  - columns: wine_preference (String, nullable), transfer_address (String, nullable)
  - migration: Auto-generate via alembic

CONDITIONAL FLOW:
  - trigger: After comment step, check tariff
  - condition: If INCOGNITA_* tariff → show questionnaire
  - else: Skip to confirm_pay (existing flow)
```

## Validation Loop

### Level 1: Syntax & Style

```bash
# Run these FIRST - fix any errors before proceeding
uv run ruff check src/ --fix
uv run ruff format src/

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Database Migration

```bash
# Generate migration
ALEMBIC_OFFLINE=true uv run alembic revision --autogenerate -m "Add incognito questionnaire fields"

# Review the generated migration file in alembic/versions/
# Verify:
# - wine_preference column added (String, nullable=True)
# - transfer_address column added (String, nullable=True)

# Run migration (if database is available)
# uv run alembic upgrade head
```

### Level 3: Manual Integration Test

```bash
# Start the bot
timeout 30 python apps/telegram_bot/main.py

# Test Steps:
# 1. Start booking flow: /start → "Забронировать дом"
# 2. Select Incognito tariff (INCOGNITA_DAY, INCOGNITA_HOURS, or INCOGNITA_WORKER)
# 3. Complete all booking steps up to comment
# 4. After comment (or skip), verify wine question appears
# 5. Select wine preference → verify transfer question appears
# 6. Test both paths:
#    a. Click "Не нужно" → should proceed to payment
#    b. Type address → should proceed to payment
# 7. Complete booking and verify:
#    - Wine preference saved in database
#    - Transfer address saved in database (or NULL if skipped)

# Test Non-Incognito flow:
# 1. Select non-Incognito tariff (DAY, HOURS_12, WORKER, etc.)
# 2. Complete booking steps
# 3. After comment → should go DIRECTLY to payment (skip questionnaire)

# Check logs for errors
# Expected: All state transitions logged, no exceptions
```

## Final Validation Checklist

- [ ] No linting errors: `uv run ruff check src/`
- [ ] No formatting issues: `uv run ruff format src/`
- [ ] Database migration generated successfully
- [ ] Wine question appears only for Incognito tariffs
- [ ] Wine question shows 5 options + back button
- [ ] Transfer question appears after wine selection
- [ ] Transfer "Не нужно" button works (proceeds to payment)
- [ ] Transfer address text input works (proceeds to payment)
- [ ] Non-Incognito tariffs skip questionnaire (go directly to payment)
- [ ] Wine preference stored in Redis during booking
- [ ] Transfer address stored in Redis during booking
- [ ] Both fields saved to database in final booking record
- [ ] Logs show all state transitions
- [ ] Back button works at any step (clears booking)
- [ ] Address validation rejects empty/short addresses
- [ ] Manual test successful for all 3 Incognito tariffs

---

## Anti-Patterns to Avoid

- ❌ Don't show questionnaire for non-Incognito tariffs
- ❌ Don't make wine/transfer fields required (they're optional premium services)
- ❌ Don't skip state management - use BookingStep enum properly
- ❌ Don't forget to update database model AND migration
- ❌ Don't exceed 64-byte callback_data limit (current patterns are safe)
- ❌ Don't forget HTML parse mode when using <b> tags
- ❌ Don't skip logging for state transitions
- ❌ Don't forget update.callback_query.answer() for button clicks
- ❌ Don't create separate handlers - integrate into booking_handler.py
- ❌ Don't forget to update DatabaseService.add_booking() signature
- ❌ Don't forget to update save_booking_information() call with new fields

## Questions to Consider

**Q: Should wine/transfer be required fields for Incognito tariffs?**
A: No, they're optional premium services. Users can select "Не нужно" or skip.

**Q: What if user types address but it's invalid format?**
A: Validate minimum length (5 chars). No strict format validation - addresses vary widely.

**Q: Should we show questionnaire for gift certificates with Incognito tariff?**
A: Check existing gift flow (lines 1471-1545). If gift has Incognito tariff, show questionnaire.

**Q: Can user go back from questionnaire to comment?**
A: No need for explicit back - "Назад в меню" clears entire booking (existing pattern).

**Q: Should transfer address have max length?**
A: Yes, limit to 500 characters to prevent abuse. Add validation in handle_transfer_input().

**Q: What about existing bookings without these fields?**
A: Fields are nullable, so existing records remain valid. Only new Incognito bookings have data.

---

## PRP Confidence Score

**Score: 8.5/10**

**Rationale:**
- ✅ Comprehensive context from codebase analysis (booking_handler.py fully reviewed)
- ✅ Clear integration point identified (after comment, before payment)
- ✅ Existing patterns extensively documented and referenced
- ✅ Database schema changes specified with migration steps
- ✅ Redis storage patterns match existing implementation
- ✅ State management follows BookingStep enum pattern
- ✅ Validation steps executable
- ⚠️ Minor: Text input handler routing needs careful state management
- ⚠️ Minor: DatabaseService.add_booking() modification not verified in detail

**Risk Areas:**
1. **MessageHandler Routing**: Text input for address needs proper state-based routing
   - Mitigation: Use ConversationHandler states dictionary in get_handler() registration
   - Alternative: Check navigation_step in a routing function

2. **DatabaseService Changes**: add_booking() signature change affects all callers
   - Mitigation: Search for all add_booking() calls and update them
   - Grep pattern: `database_service.add_booking`

3. **Gift Certificate Flow**: Need to verify questionnaire appears for gift-based Incognito bookings
   - Mitigation: Test gift flow manually after implementation

**Strengths:**
- Integration point is clear and non-disruptive (inserts between existing steps)
- Pattern matching is extensive (10+ direct code references)
- Conditional logic is simple (3 tariff types, clear boolean check)
- Database changes are minimal (2 nullable columns)
- No breaking changes to existing flows (non-Incognito bypasses entirely)

**Updated Confidence After Mitigation:**
- With MessageHandler properly configured in get_handler(): **9/10**
- With all add_booking() calls verified and updated: **9.5/10**
