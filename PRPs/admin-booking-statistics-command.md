name: "Admin Booking Statistics Command"
description: |
  Implement a comprehensive statistics command for admins to view booking and user metrics.

## Goal
Create an admin-only Telegram bot command `/statistics` that displays comprehensive booking and user statistics with filtering by time periods (year, month, all-time).

## Why
- **Business Intelligence**: Enable data-driven decisions about pricing, capacity, and marketing
- **Performance Tracking**: Monitor business health with key metrics
- **User Insights**: Understand user behavior and retention patterns
- **Quick Access**: No need for external analytics tools - data at admin's fingertips

## What
A Telegram bot command that returns formatted statistics with emoji-enhanced presentation, similar to existing admin commands pattern.

### Success Criteria
- [x] `/statistics` command accessible only to ADMIN_CHAT_ID
- [x] Shows all required metrics (bookings, users, revenue)
- [x] Includes year-to-date and month-to-date breakdown
- [x] Beautiful formatting with emojis and clear sections
- [x] Fast response time (<2 seconds for typical database size)
- [x] Error handling for edge cases (no bookings, no users, etc.)

## All Needed Context

### Documentation & References
```yaml
- file: src/handlers/admin_handler.py
  why: Pattern for admin commands with ADMIN_CHAT_ID check
  lines: 228-273
  example: get_booking_list(), get_unpaid_bookings()

- file: src/services/database_service.py
  why: Existing database query patterns and available methods
  methods: get_done_booking_count(), get_all_user_chat_ids()

- file: src/services/database/booking_repository.py
  why: Direct database access patterns with SQLAlchemy
  pattern: Using select() with filters and aggregations

- file: db/models/booking.py
  why: BookingBase model structure - fields available for queries
  fields: is_done, is_canceled, is_prepaymented, start_date, price, user_id

- file: db/models/user.py
  why: UserBase model structure
  fields: total_bookings, completed_bookings, has_bookings

- file: src/config/config.py
  why: ADMIN_CHAT_ID configuration pattern
  line: 24

- doc: https://docs.python-telegram-bot.org/en/stable/telegram.update.html
  section: Message handling and formatting
  why: Format multi-line statistics message with HTML parse_mode

- doc: https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html
  section: Aggregation functions (func.count, func.sum)
  critical: Use func.count() for counting, func.sum() for revenue totals
```

### Current Codebase Structure
```bash
src/
├── handlers/
│   ├── admin_handler.py          # Admin commands (add statistics here)
│   └── menu_handler.py
├── services/
│   ├── database_service.py        # Main DB service facade
│   └── database/
│       ├── booking_repository.py  # Booking queries
│       └── user_repository.py     # User queries
├── config/
│   └── config.py                  # ADMIN_CHAT_ID config
└── main.py                        # Register command handler

db/models/
├── booking.py                     # BookingBase model
└── user.py                        # UserBase model
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Boolean fields stored as INTEGER in SQLite
# Use: BookingBase.is_done == True (NOT ~BookingBase.is_done)
# See recent refactoring in booking_repository.py lines 82-106

# PATTERN: Admin authentication check
if chat_id != ADMIN_CHAT_ID:
    await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
    return END

# PATTERN: Telegram message formatting
# Use parse_mode="HTML" for bold (<b>), italic (<i>)
# Max message length: 4096 characters - split if needed

# GOTCHA: SQLAlchemy date filtering
# from datetime import datetime
# Use: func.extract('year', BookingBase.start_date) == 2025
# Or: BookingBase.start_date >= datetime(2025, 1, 1)

# PATTERN: Safe division (avoid ZeroDivisionError)
conversion_rate = (completed / total * 100) if total > 0 else 0
```

## Implementation Blueprint

### Statistics to Display

**📊 All-Time Statistics:**
- Total bookings created
- Completed bookings (is_done=True, is_canceled=False)
- Canceled bookings (is_canceled=True)
- Active/Upcoming bookings (is_prepaymented=True, is_done=False, is_canceled=False)
- Total revenue (sum of all completed booking prices)
- Average booking price

**📅 Year-to-Date (2025):**
- Total bookings this year
- Completed bookings this year
- Revenue this year
- Month-by-month breakdown (optional - top 3 months)

**📆 Current Month:**
- Total bookings this month
- Completed bookings this month
- Revenue this month
- Average booking value this month

**👥 User Statistics:**
- Total users in system
- Users with at least 1 booking (has_bookings=True)
- Users with completed bookings (completed_bookings > 0)
- Conversion rate (users with bookings / total users)
- Average bookings per active user

**💰 Revenue Insights:**
- Total revenue all-time
- Average revenue per booking
- Average revenue per user (with bookings)

### Data Structure for Statistics
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class BookingStats:
    """Statistics for a specific time period"""
    total_bookings: int
    completed_bookings: int
    canceled_bookings: int
    active_bookings: int
    total_revenue: float
    average_price: float

@dataclass
class UserStats:
    """User-related statistics"""
    total_users: int
    users_with_bookings: int
    users_with_completed: int
    conversion_rate: float
    avg_bookings_per_user: float

@dataclass
class Statistics:
    """Complete statistics report"""
    all_time: BookingStats
    year_to_date: BookingStats
    current_month: BookingStats
    users: UserStats
    generated_at: datetime
```

### Task List (Implementation Order)

```yaml
Task 1: Create Statistics Service
  LOCATION: src/services/statistics_service.py
  PURPOSE: Centralized statistics calculation logic
  PATTERN: Mirror structure from src/services/database_service.py

  CREATE new file with:
    - StatisticsService class (singleton pattern)
    - Methods for each metric category
    - Use dependency on database_service

  METHODS:
    - get_booking_stats(start_date=None, end_date=None) -> BookingStats
    - get_user_stats() -> UserStats
    - get_complete_statistics() -> Statistics

  CRITICAL:
    - Use SQLAlchemy func.count(), func.sum(), func.avg()
    - Handle NULL values with COALESCE or Python fallbacks
    - All date comparisons use start_date field
    - Filter: is_prepaymented=True for real bookings

Task 2: Add Repository Methods
  LOCATION: src/services/database/booking_repository.py
  PURPOSE: Database queries for statistics

  ADD methods after existing get methods:
    - get_bookings_count_by_period(start_date, end_date, is_completed=None) -> int
    - get_revenue_by_period(start_date, end_date) -> float
    - get_bookings_by_status(start_date, end_date) -> dict[str, int]

  PATTERN: Use existing session management pattern
    with self.Session() as session:
        try:
            result = session.scalar(select(...))
            return result
        except Exception as e:
            LoggerService.error(...)

Task 3: Add User Statistics Methods
  LOCATION: src/services/database/user_repository.py
  PURPOSE: User-related statistics queries

  ADD methods:
    - get_total_users_count() -> int
    - get_users_with_bookings_count() -> int  # has_bookings=True
    - get_users_with_completed_count() -> int  # completed_bookings > 0

  PATTERN: Simple SELECT COUNT queries with filters

Task 4: Create Admin Statistics Handler
  LOCATION: src/handlers/admin_handler.py
  PURPOSE: Telegram command handler

  ADD async function after get_unpaid_bookings (line ~273):
    async def get_statistics(update, context)

  STRUCTURE:
    1. Check ADMIN_CHAT_ID authorization
    2. Show "⏳ Генерирую статистику..." message
    3. Call statistics_service.get_complete_statistics()
    4. Format message with format_statistics_message()
    5. Send formatted message(s)

  PATTERN: Mirror get_booking_list() authorization pattern

Task 5: Create Message Formatter
  LOCATION: src/helpers/statistics_helper.py (NEW FILE)
  PURPOSE: Format statistics into beautiful Telegram message

  CREATE new helper file with:
    - format_statistics_message(stats: Statistics) -> str
    - format_booking_stats(stats: BookingStats, period: str) -> str
    - format_user_stats(stats: UserStats) -> str

  CRITICAL:
    - Use HTML parse_mode formatting (<b>, <i>, <code>)
    - Add emoji for visual appeal (📊 📅 👥 💰 ✅ ❌)
    - Check message length < 4096 chars
    - Format numbers: "1,234" for thousands, "12,345.67" for money

Task 6: Register Command Handler
  LOCATION: src/main.py
  PURPOSE: Make command accessible in Telegram

  ADD after line ~59 (after unpaid_bookings):
    application.add_handler(
        CommandHandler("statistics", admin_handler.get_statistics)
    )

  PATTERN: Same as existing admin commands

Task 7: Add Database Service Facade Methods
  LOCATION: src/services/database_service.py
  PURPOSE: Expose statistics methods through main service

  ADD methods (after line ~220):
    def get_bookings_count_by_period(...) -> int:
        return self.booking_repository.get_bookings_count_by_period(...)

    def get_revenue_by_period(...) -> float:
        return self.booking_repository.get_revenue_by_period(...)

    # ... etc for all new repository methods
```

### Pseudocode for Core Logic

```python
# Task 1: StatisticsService.get_complete_statistics()
from datetime import datetime
from dateutil.relativedelta import relativedelta

class StatisticsService:
    def __init__(self):
        self.db = DatabaseService()

    def get_complete_statistics(self) -> Statistics:
        now = datetime.now()
        year_start = datetime(now.year, 1, 1)
        month_start = datetime(now.year, now.month, 1)

        # All-time stats
        all_time = self._get_booking_stats(start_date=None, end_date=None)

        # Year-to-date
        ytd = self._get_booking_stats(start_date=year_start, end_date=now)

        # Current month
        current_month = self._get_booking_stats(start_date=month_start, end_date=now)

        # User stats
        user_stats = self._get_user_stats()

        return Statistics(
            all_time=all_time,
            year_to_date=ytd,
            current_month=current_month,
            users=user_stats,
            generated_at=now
        )

    def _get_booking_stats(self, start_date, end_date) -> BookingStats:
        # PATTERN: Count with filters
        total = self.db.get_bookings_count_by_period(
            start_date, end_date, is_completed=None
        )

        completed = self.db.get_bookings_count_by_period(
            start_date, end_date, is_completed=True
        )

        # CRITICAL: Only completed bookings count for revenue
        revenue = self.db.get_revenue_by_period(
            start_date, end_date
        )

        # PATTERN: Safe division
        avg_price = revenue / completed if completed > 0 else 0

        # Count canceled: is_canceled=True
        # Count active: is_prepaymented=True, is_done=False, is_canceled=False

        return BookingStats(...)

# Task 2: BookingRepository.get_revenue_by_period()
def get_revenue_by_period(self, start_date, end_date) -> float:
    with self.Session() as session:
        try:
            query = select(func.sum(BookingBase.price)).where(
                and_(
                    BookingBase.is_done == True,
                    BookingBase.is_canceled == False,
                    BookingBase.is_prepaymented == True,
                )
            )

            # CRITICAL: Add date filters if provided
            if start_date:
                query = query.where(BookingBase.start_date >= start_date)
            if end_date:
                query = query.where(BookingBase.start_date <= end_date)

            result = session.scalar(query)

            # GOTCHA: sum() returns None if no rows
            return float(result) if result else 0.0

        except Exception as e:
            LoggerService.error(__name__, "get_revenue_by_period", e)
            return 0.0

# Task 5: Format message
def format_statistics_message(stats: Statistics) -> str:
    """Format statistics into beautiful Telegram HTML message"""

    msg = f"<b>📊 СТАТИСТИКА БРОНИРОВАНИЙ</b>\n"
    msg += f"🕐 Сгенерировано: {stats.generated_at.strftime('%d.%m.%Y %H:%M')}\n\n"

    # All-time section
    msg += "<b>📈 ВСЕ ВРЕМЯ</b>\n"
    msg += f"├ Всего броней: <b>{stats.all_time.total_bookings}</b>\n"
    msg += f"├ ✅ Выполнено: {stats.all_time.completed_bookings}\n"
    msg += f"├ ❌ Отменено: {stats.all_time.canceled_bookings}\n"
    msg += f"├ 🏃 Активных: {stats.all_time.active_bookings}\n"
    msg += f"└ 💰 Выручка: <b>{stats.all_time.total_revenue:,.0f}</b> руб.\n\n"

    # Year-to-date
    msg += f"<b>📅 ГОД ({stats.generated_at.year})</b>\n"
    # ... same pattern

    # Current month
    msg += f"<b>📆 ТЕКУЩИЙ МЕСЯЦ</b>\n"
    # ... same pattern

    # Users
    msg += "<b>👥 ПОЛЬЗОВАТЕЛИ</b>\n"
    msg += f"├ Всего: {stats.users.total_users}\n"
    msg += f"├ С бронями: {stats.users.users_with_bookings}\n"
    msg += f"├ Завершили: {stats.users.users_with_completed}\n"
    msg += f"└ Конверсия: {stats.users.conversion_rate:.1f}%\n"

    return msg
```

### Integration Points
```yaml
DATABASE:
  - No migrations needed - using existing tables
  - Queries use existing BookingBase and UserBase models

CONFIG:
  - Uses existing ADMIN_CHAT_ID from config.py
  - No new environment variables needed

HANDLERS:
  - Register in main.py CommandHandler list
  - Add to admin_handler.py following existing patterns

LOGGING:
  - Use existing LoggerService for errors
  - Log statistics generation: LoggerService.info(__name__, "Generated statistics", ...)
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Format code
uv run black src/services/statistics_service.py src/helpers/statistics_helper.py

# Check for issues
uv run ruff check src/services/ src/helpers/ src/handlers/admin_handler.py --fix

# Expected: No errors. Statistics code follows project style.
```

### Level 2: Unit Tests (Optional - project doesn't have test suite)
```bash
# Manual testing via Telegram bot
# Send /statistics command from ADMIN_CHAT_ID
# Verify all sections display correctly
# Test edge cases: fresh database (no bookings)
```

### Level 3: Integration Test
```bash
# Start bot
ENV=debug python src/main.py

# In Telegram (from admin chat):
# 1. Send: /statistics
# Expected: Full statistics report with all sections

# 2. Check formatting:
#    - Numbers have thousand separators
#    - Emojis display correctly
#    - All percentages calculated correctly
#    - Revenue sums match database

# 3. Verify authorization:
#    - Non-admin chat should see: "⛔ Эта команда не доступна в этом чате."
```

## Final Validation Checklist
- [ ] `/statistics` command responds quickly (<2 seconds)
- [ ] All metrics display correct values (spot-check against database)
- [ ] Authorization works (admin-only access)
- [ ] Message formatting is clean and readable
- [ ] No errors in logs during statistics generation
- [ ] Handles edge cases gracefully (no bookings, no users)
- [ ] Revenue calculations match completed bookings only
- [ ] Year and month filters work correctly
- [ ] Conversion percentages calculated correctly

---

## Anti-Patterns to Avoid
- ❌ Don't include test/canceled bookings in revenue totals
- ❌ Don't query database multiple times - batch queries efficiently
- ❌ Don't expose statistics to non-admin users (security risk)
- ❌ Don't format money values without thousand separators (readability)
- ❌ Don't use string concatenation - use f-strings or .format()
- ❌ Don't ignore NULL/None values in aggregations (causes errors)
- ❌ Don't send messages >4096 chars (Telegram limit)

## Confidence Score

**8.5/10** - High confidence for one-pass implementation

**Strengths:**
- Clear patterns exist in codebase (admin commands, database queries)
- All required models and fields already exist
- Well-defined requirements with exact metrics needed
- Strong validation path (manual testing in Telegram)

**Risks:**
- SQLAlchemy date filtering edge cases
- Message length could exceed 4096 if many bookings (unlikely but possible)
- Formatting edge cases with 0 values or empty database

**Mitigation:**
- Comprehensive pseudocode for complex queries
- Clear error handling patterns documented
- Safe division patterns to avoid ZeroDivisionError
