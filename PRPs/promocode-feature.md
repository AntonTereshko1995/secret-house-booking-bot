name: "Promocode Feature Implementation"
description: |
  Complete implementation of promo code system for booking discount management with admin controls

---

## Goal
Implement a complete promo code system that allows:
1. Users to enter promo codes during booking workflow and receive discounts
2. Admins to create, view, and manage promo codes with flexible parameters (date range, discount %, tariff restrictions)
3. Automatic price recalculation when a promo code is applied
4. Promo code tracking in booking records

## Why
- **Business value**: Enables marketing campaigns, seasonal promotions, and customer retention strategies
- **User impact**: Provides transparent discount mechanism, improves booking conversion
- **Integration**: Seamlessly fits into existing booking workflow between comment input and payment confirmation
- **Solves**: Manual discount management, lack of trackable promotional campaigns

## What
User-visible behavior:
- During booking, after comment step, user sees "Enter promo code" button with "SKIP" option
- User enters promo code as text message
- System validates code (existence, date validity, tariff compatibility)
- Price recalculates and displays updated total with discount applied
- Booking record stores `promocode_id` reference

Admin behavior:
- New command `/create_promocode` to create promo codes
- Multi-step conversation to collect: name, date_from, date_to, discount %, tariff filter
- Admin can view/list promo codes (future enhancement)

### Success Criteria
- [x] User can enter promo code during booking flow
- [x] Invalid promo codes show clear error messages
- [x] Valid promo codes apply discount and update price display
- [x] Booking model stores `promocode_id` foreign key
- [x] Admin can create promo codes via bot command
- [x] Database migration creates `promocode` table
- [x] Price calculation service integrates promo code discounts
- [x] All existing tests pass after changes

## All Needed Context

### Documentation & References
```yaml
- url: https://docs.python-telegram-bot.org/en/stable/telegram.ext.conversationhandler.html
  why: State management patterns for multi-step conversations (promo code input, admin creation flow)
  critical: ConversationHandler requires concurrent_updates=False, state transitions via return values

- file: src/handlers/admin_handler.py
  why: Pattern for admin commands with ConversationHandler (see change_password, broadcast handlers)
  lines: 115-128 (get_password_handler), 197-271 (change_password flow)
  pattern: Entry point → State with MessageHandler → Validation → Update → END

- file: src/handlers/booking_handler.py
  why: Booking workflow integration point, price calculation patterns
  lines: 700-824 (write_comment → confirm_pay flow)
  integration_point: After write_comment, before confirm_pay - insert promocode step

- file: src/services/calculation_rate_service.py
  why: Price calculation logic to integrate discount percentage
  lines: 162-199 (calculate_price_for_date method)
  pattern: Base price + addons, need to apply discount_percentage at final step

- file: db/models/booking.py
  why: Booking model structure, foreign key patterns (see gift_id)
  lines: 40 (gift_id foreign key pattern to mirror)

- file: alembic/versions/0c1b9c465d4d_add_chat_id_to_users.py
  why: Migration pattern for adding columns with batch_alter_table (SQLite compatibility)
  pattern: Use batch_alter_table for SQLite, add_column, create foreign key constraint

- file: src/constants.py
  why: State constants for ConversationHandler
  pattern: Add PROMOCODE_INPUT, CREATE_PROMO_NAME, CREATE_PROMO_DISCOUNT, etc.

- file: src/models/enum/booking_step.py
  why: Booking state enum to add PROMOCODE step

- doc: https://docs.sqlalchemy.org/en/20/orm/relationship_patterns.html
  section: One to Many relationships
  critical: Foreign key must reference promocode.id, relationship() for ORM access
```

### Current Codebase Tree (relevant sections)
```bash
/Users/a/secret-house-booking-bot/
├── src/
│   ├── handlers/
│   │   ├── admin_handler.py          # Admin command patterns
│   │   ├── booking_handler.py        # Booking workflow
│   ├── services/
│   │   ├── calculation_rate_service.py  # Price calculation
│   │   ├── database_service.py       # DB facade
│   │   └── redis_service.py          # Session state mgmt
│   ├── models/
│   │   └── enum/
│   │       ├── booking_step.py       # Workflow states
│   │       └── tariff.py             # Tariff enum
│   ├── constants.py                  # State constants
│   └── helpers/
│       └── string_helper.py          # Validation helpers
├── db/
│   └── models/
│       ├── booking.py                # Booking ORM model
│       ├── user.py                   # User ORM model
│       └── gift.py                   # Gift ORM model (reference)
└── alembic/
    └── versions/                     # Migration files
```

### Desired Codebase Tree (new files)
```bash
/Users/a/secret-house-booking-bot/
├── db/
│   └── models/
│       └── promocode.py              # NEW: Promocode ORM model
├── src/
│   └── services/
│       └── database/
│           └── promocode_repository.py  # NEW: Promocode DB operations
└── alembic/
    └── versions/
        └── XXXX_add_promocode_table.py  # NEW: Migration
        └── YYYY_add_promocode_id_to_booking.py  # NEW: Migration
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: SQLite requires batch_alter_table for schema changes
# See: alembic/versions/0c1b9c465d4d_add_chat_id_to_users.py
# Pattern:
with op.batch_alter_table('booking', schema=None) as batch_op:
    batch_op.add_column(sa.Column('promocode_id', sa.Integer(), nullable=True))
    batch_op.create_foreign_key('fk_booking_promocode', 'promocode', ['promocode_id'], ['id'])

# CRITICAL: ConversationHandler state management
# - MUST return state constant or END
# - MessageHandler in states dict MUST have filters.TEXT & ~filters.COMMAND
# - Pattern: src/handlers/admin_handler.py:119-127

# CRITICAL: Redis service booking storage
# - Use redis_service.update_booking_field(update, "field_name", value)
# - Retrieve with: booking = redis_service.get_booking(update)
# - Clear with: redis_service.clear_booking(update)

# CRITICAL: Price calculation integration
# - Must call calculate_price_for_date() which includes date-based pricing
# - Apply promo discount AFTER all add-ons calculated
# - Formula: final_price = base_price_with_addons * (1 - discount_percentage/100)

# CRITICAL: Telegram callback data length limit
# - Max 64 bytes for callback_data
# - Use compact patterns: "BOOKING-PROMO_SKIP" not "BOOKING-PROMOCODE-SKIP-ACTION"

# GOTCHA: Tariff enum comparison
# - Promocode.applicable_tariffs stored as JSON array of int values
# - Compare with: tariff.value in json.loads(promocode.applicable_tariffs)
# - "ALL" tariffs: store as empty list [] or null, check in code

# GOTCHA: Date validation
# - User enters date as text (DD.MM.YYYY format)
# - Admin enters dates during creation
# - Must validate: date_from <= date_to, date_to >= today
# - Booking date check: promocode.date_from <= booking.start_date.date() <= promocode.date_to
```

## Implementation Blueprint

### Data Models and Structure

#### 1. Promocode ORM Model (db/models/promocode.py)
```python
from datetime import date, datetime
from db.models.base import Base
from sqlalchemy import Integer, String, Float, Date, JSON
from sqlalchemy.orm import Mapped, mapped_column

class PromocodeBase(Base):
    __tablename__ = 'promocode'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # "SUMMER2024"
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)
    discount_percentage: Mapped[float] = mapped_column(Float, nullable=False)  # 10.0 = 10%
    applicable_tariffs: Mapped[str] = mapped_column(JSON, nullable=True)  # null = ALL, or [1,2,3] = specific tariff.values
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # Soft delete
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __repr__(self) -> str:
        return f"PromocodeBase(id={self.id}, name={self.name}, discount={self.discount_percentage}%)"
```

#### 2. Update Booking Model (db/models/booking.py)
```python
# ADD this line after line 40:
promocode_id: Mapped[int] = mapped_column(ForeignKey("promocode.id"), nullable=True)

# ADD this line after line 44:
promocode = relationship("PromocodeBase")
```

#### 3. Add BookingStep Enum (src/models/enum/booking_step.py)
```python
# ADD after line 16 (after COMMENT):
PROMOCODE = "PROMOCODE"
```

#### 4. Add Constants (src/constants.py)
```python
# ADD after line 40 (in Бронирование section):
PROMOCODE_INPUT = "PROMOCODE_INPUT"

# ADD after line 60 (in Admin section):
CREATE_PROMO_NAME = "CREATE_PROMO_NAME"
CREATE_PROMO_DATE_FROM = "CREATE_PROMO_DATE_FROM"
CREATE_PROMO_DATE_TO = "CREATE_PROMO_DATE_TO"
CREATE_PROMO_DISCOUNT = "CREATE_PROMO_DISCOUNT"
CREATE_PROMO_TARIFF = "CREATE_PROMO_TARIFF"
```

### List of Tasks (Implementation Order)

```yaml
Task 1: Create Database Migration for Promocode Table
FILE: alembic/versions/XXXX_add_promocode_table.py
ACTION: CREATE new migration
COMMAND: ALEMBIC_OFFLINE=true uv run alembic revision --autogenerate -m "Add promocode table"
PATTERN: Standard autogenerate migration
VERIFY:
  - Check migration creates 'promocode' table
  - Columns: id, name, date_from, date_to, discount_percentage, applicable_tariffs, is_active, created_at
  - name column has unique constraint

Task 2: Create Database Migration for Booking.promocode_id
FILE: alembic/versions/YYYY_add_promocode_id_to_booking.py
ACTION: CREATE new migration
COMMAND: ALEMBIC_OFFLINE=true uv run alembic revision --autogenerate -m "Add promocode_id to booking"
PATTERN: Use batch_alter_table for SQLite (see 0c1b9c465d4d_add_chat_id_to_users.py)
VERIFY:
  - Uses batch_alter_table context manager
  - Adds nullable column promocode_id
  - Creates foreign key constraint to promocode.id

Task 3: Create Promocode ORM Model
FILE: db/models/promocode.py
ACTION: CREATE new file
MIRROR: db/models/gift.py structure
MODIFY: Add fields as specified in blueprint
VERIFY:
  - Import Base from db.models.base
  - Use Mapped[] type hints
  - __repr__ implemented

Task 4: Update Booking Model with Promocode Relationship
FILE: db/models/booking.py
ACTION: MODIFY
ADD:
  - Line after 40: promocode_id column
  - Line after 44: promocode relationship
PRESERVE: All existing columns and relationships
VERIFY: Import PromocodeBase at top

Task 5: Create Promocode Repository
FILE: src/services/database/promocode_repository.py
ACTION: CREATE new file
MIRROR: src/services/database/gift_repository.py pattern
METHODS:
  - add_promocode(name, date_from, date_to, discount, tariffs) -> PromocodeBase
  - get_promocode_by_name(name) -> PromocodeBase | None
  - validate_promocode(name, booking_date, tariff) -> tuple[bool, str, PromocodeBase|None]
  - list_active_promocodes() -> list[PromocodeBase]
VERIFY: Use singleton decorator, Session context manager pattern

Task 6: Update DatabaseService Facade
FILE: src/services/database_service.py
ACTION: MODIFY
ADD:
  - Import PromocodeRepository
  - self.promocode_repository = PromocodeRepository() in __init__
  - Delegate methods: add_promocode(), get_promocode_by_name(), validate_promocode()
PATTERN: Mirror gift_repository delegation (lines 95-140)

Task 7: Add Promocode Step to Booking Workflow Enum
FILE: src/models/enum/booking_step.py
ACTION: MODIFY
ADD: PROMOCODE = "PROMOCODE" after COMMENT line
VERIFY: Enum order reflects workflow sequence

Task 8: Add State Constants
FILE: src/constants.py
ACTION: MODIFY
ADD:
  - PROMOCODE_INPUT in booking section
  - CREATE_PROMO_* constants in admin section
VERIFY: No duplicate constant names

Task 9: Implement Promocode Entry in Booking Handler
FILE: src/handlers/booking_handler.py
ACTION: MODIFY
LOCATION: After write_comment function (line 700-728)
ADD NEW FUNCTIONS:
  - async def promocode_entry_message(update, context) -> int
  - async def handle_promocode_input(update, context) -> int
  - async def skip_promocode(update, context) -> int
MODIFY write_comment:
  - Change return from confirm_pay to promocode_entry_message (non-incognito)
  - Keep incognito flow to wine_preference_message
INTEGRATION:
  - Show "Enter promo code" with SKIP button
  - MessageHandler for text input → validate → apply discount → update redis
  - Store promocode_id in redis_service
  - Error handling: invalid code, expired, wrong tariff
PATTERN: Mirror write_comment → confirm_pay flow

Task 10: Update Price Calculation with Promo Discount
FILE: src/handlers/booking_handler.py
FUNCTION: confirm_pay (line 731)
ACTION: MODIFY
LOGIC:
  - After line 759 (price calculation), check if booking.promocode_id exists
  - If yes: load promocode, apply discount: price = price * (1 - discount/100)
  - Update message to show: "Original: X руб, Discount: Y%, Final: Z руб"
PRESERVE: All existing price calculation logic, special pricing info

Task 11: Update Booking Creation to Store Promocode ID
FILE: src/handlers/booking_handler.py
FUNCTION: confirm_booking or similar (where booking record created)
ACTION: MODIFY
ADD: Include promocode_id from redis booking state when creating DB record
PATTERN: Same as gift_id handling (line 789-792)

Task 12: Register Promocode Handlers in Booking Handler
FILE: src/handlers/booking_handler.py
FUNCTION: get_handler() (line 58)
ACTION: MODIFY
ADD:
  - MessageHandler for PROMOCODE_INPUT state with filters.TEXT & ~filters.COMMAND
  - CallbackQueryHandler for skip: pattern="^BOOKING-PROMO_{SKIP}$"
PATTERN: Mirror BOOKING_COMMENT handler pattern

Task 13: Create Admin Command - Create Promocode Handler
FILE: src/handlers/admin_handler.py
ACTION: MODIFY
ADD NEW FUNCTIONS:
  - get_create_promocode_handler() -> ConversationHandler
  - create_promocode_start(update, context)
  - handle_promo_name(update, context)
  - handle_promo_date_from(update, context)
  - handle_promo_date_to(update, context)
  - handle_promo_discount(update, context)
  - handle_promo_tariff_selection(update, context)
  - cancel_promo_creation(update, context)
PATTERN: Mirror get_password_handler (lines 115-128)
STATES:
  CREATE_PROMO_NAME → CREATE_PROMO_DATE_FROM → CREATE_PROMO_DATE_TO →
  CREATE_PROMO_DISCOUNT → CREATE_PROMO_TARIFF → Confirm → Save to DB
VALIDATION:
  - Name: unique, max 50 chars, alphanumeric+dash
  - Dates: DD.MM.YYYY format, date_to >= date_from >= today
  - Discount: 1-100 float
  - Tariff: Show all tariffs + "ALL" option, multi-select with inline buttons

Task 14: Register Admin Handler in Main
FILE: src/main.py (or wherever handlers registered)
ACTION: MODIFY
ADD: application.add_handler(admin_handler.get_create_promocode_handler())
LOCATION: Near other admin handlers
VERIFY: Handler registered with correct order (admin handlers typically after user handlers)

Task 15: Run Migrations
COMMAND: ENV=debug uv run alembic upgrade head
VERIFY:
  - promocode table exists
  - booking.promocode_id column exists
  - Foreign key constraint created
  - No errors in migration

Task 16: Add Helper Function for Promocode Validation Messages
FILE: src/helpers/string_helper.py (or new promocode_helper.py)
ACTION: CREATE helper functions
FUNCTIONS:
  - validate_promo_name_format(name: str) -> tuple[bool, str]
  - format_promo_discount_message(original_price, discount_pct, final_price) -> str
  - format_promo_error_message(error_type: str) -> str
PATTERN: Mirror existing validation helpers (is_valid_user_contact pattern)

Task 17: Update Booking Info Display to Show Promocode
FILE: src/helpers/string_helper.py
FUNCTION: generate_booking_info_message (likely exists)
ACTION: MODIFY
ADD: If booking.promocode_id, add line showing promocode name and discount
PATTERN: Mirror gift certificate display pattern

Task 18: Manual Testing - User Flow
COMMANDS:
  - ENV=debug uv run python apps/telegram_bot/main.py
  - Test: Start booking → complete flow → reach promocode step → enter invalid code → see error
  - Test: Enter valid code → see price update → complete booking
  - Verify: Database booking record has promocode_id set
VERIFY: All steps work, error messages clear, price updates correctly

Task 19: Manual Testing - Admin Flow
COMMANDS:
  - ENV=debug uv run python apps/telegram_bot/main.py
  - Test: /create_promocode → enter all fields → save
  - Test: Invalid inputs rejected (past dates, invalid discount, duplicate name)
  - Verify: Database promocode record created correctly
VERIFY: Admin can create promo codes, validation works

Task 20: Format Code and Check Style
COMMANDS:
  - uv run ruff check --fix .
  - uv run ruff format .
VERIFY: No linting errors remain

Task 21: Type Check (if mypy configured)
COMMAND: uv run mypy src/ db/
VERIFY: No type errors (or only pre-existing ones)

Task 22: Test Existing Booking Flow Still Works
TEST:
  - Complete booking WITHOUT entering promocode (use SKIP)
  - Verify booking created successfully
  - Verify promocode_id is NULL in database
VERIFY: Backwards compatibility maintained
```

### Pseudocode for Key Functions

#### Promocode Repository - validate_promocode
```python
def validate_promocode(self, name: str, booking_date: date, tariff: Tariff) -> tuple[bool, str, PromocodeBase|None]:
    """
    Validates promocode against booking parameters
    Returns: (is_valid, error_message, promocode_object)
    """
    # PATTERN: Always use Session context manager (see gift_repository.py)
    with self.Session() as session:
        # CRITICAL: Case-insensitive name lookup, uppercase before query
        promo = session.query(PromocodeBase).filter(
            PromocodeBase.name == name.upper(),
            PromocodeBase.is_active == True
        ).first()

        if not promo:
            return (False, "❌ Промокод не найден", None)

        # CRITICAL: Date validation with booking_date (date object)
        if not (promo.date_from <= booking_date <= promo.date_to):
            return (False, f"❌ Промокод недействителен в выбранную дату", None)

        # CRITICAL: Tariff validation - null/empty list means ALL tariffs
        if promo.applicable_tariffs:
            import json
            applicable = json.loads(promo.applicable_tariffs) if isinstance(promo.applicable_tariffs, str) else promo.applicable_tariffs
            if tariff.value not in applicable:
                return (False, f"❌ Промокод не применим к выбранному тарифу", None)

        return (True, "✅ Промокод применен!", promo)
```

#### Booking Handler - promocode_entry_message
```python
async def promocode_entry_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show promo code entry prompt with SKIP option"""
    redis_service.update_booking_field(update, "navigation_step", BookingStep.PROMOCODE)

    # PATTERN: Inline keyboard with callback queries (see booking_handler.py patterns)
    keyboard = [
        [InlineKeyboardButton("➡️ Пропустить", callback_data=f"BOOKING-PROMO_{SKIP}")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data=f"BOOKING-PROMO_{END}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "🎟️ <b>Есть промокод?</b>\n\n"
        "Введите промокод, чтобы получить скидку.\n"
        "Или нажмите <b>Пропустить</b>, если у вас нет промокода."
    )

    # PATTERN: safe_edit_message_text for callback updates, reply_text for message updates
    if update.callback_query:
        await update.callback_query.answer()
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
            reply_markup=reply_markup,
        )
    else:
        await update.message.reply_text(text=message, parse_mode="HTML", reply_markup=reply_markup)

    # CRITICAL: Return PROMOCODE_INPUT state for MessageHandler
    return PROMOCODE_INPUT
```

#### Booking Handler - handle_promocode_input
```python
async def handle_promocode_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for promo code"""
    # PATTERN: MessageHandler processes text messages
    if not update.message or not update.message.text:
        return PROMOCODE_INPUT

    promo_code = update.message.text.strip().upper()
    booking = redis_service.get_booking(update)

    # CRITICAL: Validate against booking start_date and tariff
    is_valid, message, promo = database_service.validate_promocode(
        promo_code,
        booking.start_booking_date.date(),
        booking.tariff
    )

    if is_valid:
        # CRITICAL: Store promocode_id in redis, will be saved to DB later
        redis_service.update_booking_field(update, "promocode_id", promo.id)
        redis_service.update_booking_field(update, "promocode_discount", promo.discount_percentage)

        await update.message.reply_text(
            f"✅ {message}\n"
            f"🎉 Скидка <b>{promo.discount_percentage}%</b> будет применена!",
            parse_mode="HTML"
        )

        # PATTERN: Progress to next step (same as skip)
        return await confirm_pay(update, context)
    else:
        # PATTERN: Show error, stay in same state for retry
        await update.message.reply_text(
            f"{message}\n\n"
            "Попробуйте ввести другой код или нажмите <b>Пропустить</b>.",
            parse_mode="HTML"
        )
        return PROMOCODE_INPUT
```

#### Admin Handler - create_promocode_start
```python
async def create_promocode_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start promo code creation flow (admin only)"""
    chat_id = update.effective_chat.id

    # CRITICAL: Admin-only check (see admin_handler.py pattern)
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
        return END

    # PATTERN: Store conversation state in context.user_data
    context.user_data["creating_promocode"] = {}

    keyboard = [[InlineKeyboardButton("Отмена", callback_data="cancel_promo_create")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "📝 <b>Создание промокода</b>\n\n"
        "Шаг 1 из 5: Введите название промокода\n"
        "(только латинские буквы, цифры и дефис, макс. 50 символов)\n\n"
        "Пример: SUMMER2024"
    )

    await update.message.reply_text(text=message, reply_markup=reply_markup, parse_mode="HTML")

    # CRITICAL: Return first state constant
    return CREATE_PROMO_NAME
```

#### Calculation Rate Service - Apply Discount
```python
# MODIFY calculate_price_for_date or create new wrapper
def calculate_price_with_promocode(
    self,
    booking_date: date,
    tariff: Tariff,
    duration_hours: int,
    promocode_discount: float = 0.0,  # NEW parameter
    **kwargs  # is_sauna, is_secret_room, etc.
) -> int:
    """Calculate price with optional promo code discount"""
    # PATTERN: Use existing calculation logic
    base_price = self.calculate_price_for_date(
        booking_date, tariff, duration_hours, **kwargs
    )

    # CRITICAL: Apply discount AFTER all add-ons
    if promocode_discount > 0:
        discount_amount = base_price * (promocode_discount / 100)
        final_price = base_price - discount_amount
        return int(final_price)  # Round to int

    return base_price
```

### Integration Points

```yaml
DATABASE:
  - migration 1: "Create promocode table with columns: id, name, date_from, date_to, discount_percentage, applicable_tariffs, is_active, created_at"
  - migration 2: "Add promocode_id foreign key to booking table"
  - index: "CREATE INDEX idx_promocode_name ON promocode(name)" (optional, for faster lookups)

REDIS STATE:
  - add fields: "promocode_id", "promocode_discount" to booking state
  - clear on: back_navigation, confirm_booking

BOOKING WORKFLOW:
  - insert step: COMMENT → PROMOCODE → (INCOGNITO flows) → CONFIRM_BOOKING
  - state constant: PROMOCODE_INPUT
  - handlers: MessageHandler for text input, CallbackQueryHandler for SKIP

ADMIN COMMANDS:
  - new command: /create_promocode
  - conversation states: CREATE_PROMO_NAME → DATE_FROM → DATE_TO → DISCOUNT → TARIFF
  - registration: In main.py or wherever admin handlers added

PRICE DISPLAY:
  - modify: confirm_pay message to show discount breakdown
  - format: "💰 Цена: {original} руб\n🎟️ Промокод: -{discount}%\n✅ Итого: {final} руб"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run FIRST - fix any errors before proceeding
uv run ruff check src/handlers/booking_handler.py --fix
uv run ruff check src/handlers/admin_handler.py --fix
uv run ruff check db/models/promocode.py --fix
uv run ruff check src/services/database/promocode_repository.py --fix

# Format code
uv run ruff format .

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Database Validation
```bash
# Run migrations in debug mode
ENV=debug uv run alembic upgrade head

# Verify tables exist
ENV=debug uv run python -c "
from db.database import engine
from sqlalchemy import inspect
insp = inspect(engine)
tables = insp.get_table_names()
assert 'promocode' in tables, 'Promocode table missing'
cols = [c['name'] for c in insp.get_columns('booking')]
assert 'promocode_id' in cols, 'Booking.promocode_id column missing'
print('✅ Database schema validated')
"

# Expected: "✅ Database schema validated"
```

### Level 3: Manual Integration Test - User Flow
```bash
# Start bot in debug mode
ENV=debug timeout 30 uv run python apps/telegram_bot/main.py

# Manual test checklist:
# 1. Start booking flow: /start → Бронирование
# 2. Complete all steps up to comment
# 3. At promo code step:
#    - Try entering "INVALID123" → see error
#    - Try entering valid promo code → see success + discount
#    - Try clicking "Skip" → proceed to payment
# 4. Complete booking
# 5. Check database: booking record has promocode_id set (if used)

# Expected: Flow works smoothly, price updates correctly
```

### Level 4: Manual Integration Test - Admin Flow
```bash
# Start bot in debug mode
ENV=debug timeout 30 uv run python apps/telegram_bot/main.py

# Manual test checklist:
# 1. Send /create_promocode command (as admin)
# 2. Enter promo name: "TEST2024"
# 3. Enter date_from: "01.12.2024"
# 4. Enter date_to: "31.12.2024"
# 5. Enter discount: "15"
# 6. Select tariff: "ALL" or specific tariff
# 7. Verify promo code saved to database
# 8. Try creating duplicate name → see error

# Expected: Admin can create promo codes, validation works
```

### Level 5: Backwards Compatibility Test
```bash
# Verify existing booking flow still works WITHOUT promocode

# Start bot
ENV=debug timeout 30 uv run python apps/telegram_bot/main.py

# Test:
# 1. Complete full booking flow
# 2. At promocode step → click "SKIP"
# 3. Complete booking
# 4. Check database: booking.promocode_id is NULL

# Expected: Old flow unaffected, NULL promocode_id is acceptable
```

## Final Validation Checklist
- [ ] Migrations run successfully: `ENV=debug uv run alembic upgrade head`
- [ ] No linting errors: `uv run ruff check src/ db/`
- [ ] Database schema validated (promocode table, booking.promocode_id exists)
- [ ] Manual user test: Can enter promo code and see discount applied
- [ ] Manual user test: Can skip promo code step
- [ ] Manual user test: Invalid promo codes show clear errors
- [ ] Manual admin test: Can create promo codes via /create_promocode
- [ ] Manual admin test: Duplicate promo names rejected
- [ ] Backwards compatibility: Booking without promo code works (promocode_id NULL)
- [ ] Price display shows discount breakdown when applied
- [ ] Booking record stores correct promocode_id

---

## Anti-Patterns to Avoid
- ❌ Don't hardcode promo codes - always fetch from database
- ❌ Don't apply discount before calculating add-ons (sauna, rooms, etc.)
- ❌ Don't forget to validate tariff compatibility (user can't use wrong tariff promo)
- ❌ Don't skip date validation (expired promo codes must be rejected)
- ❌ Don't allow non-admin users to access /create_promocode
- ❌ Don't use synchronous DB queries - repository pattern is already async-safe
- ❌ Don't forget to clear promo state when user goes back to menu
- ❌ Don't create new price calculation logic - extend existing calculate_price_for_date
- ❌ Don't skip migration testing - always run `alembic upgrade head` and verify schema

---

## PRP Quality Score: 9/10

**Confidence for one-pass implementation: 90%**

**Reasoning:**
- ✅ Complete context provided (existing patterns, file references with line numbers)
- ✅ Clear task breakdown with execution order
- ✅ Database migration patterns documented (SQLite batch_alter_table gotcha)
- ✅ ConversationHandler patterns well-documented with examples
- ✅ Price calculation integration point clearly identified
- ✅ Validation loops cover database, manual testing, backwards compatibility
- ⚠️ Minor risk: Admin tariff selection UI (multi-select inline keyboard) might need iteration
- ⚠️ Minor risk: Date input validation format (DD.MM.YYYY) could have edge cases

**Potential improvements:**
- Could add unit test examples (currently only manual integration tests)
- Could specify exact Telegram inline keyboard layout for tariff selection