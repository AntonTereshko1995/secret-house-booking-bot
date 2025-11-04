# Database Repositories

## Overview

Database layer organized into specialized repositories following the **Repository Pattern**.

## Structure

```
services/database/
├── __init__.py                # Package exports
├── base.py                    # BaseRepository - session management
├── user_repository.py         # UserRepository - user operations
├── gift_repository.py         # GiftRepository - gift operations
└── booking_repository.py      # BookingRepository - booking operations
```

## Repositories

### BaseRepository
Base class providing database session management.

```python
from src.services.database.base import BaseRepository

class MyRepository(BaseRepository):
    def my_method(self):
        with self.Session() as session:
            # Use session here
            pass
```

### UserRepository
User-related database operations.

**Methods (8):**
- `add_user(contact)` - Create new user
- `get_or_create_user(contact)` - Get or create user
- `get_user_by_contact(contact)` - Find user by contact
- `get_user_by_id(user_id)` - Find user by ID
- `update_user_chat_id(contact, chat_id)` - Store/update chat ID
- `get_all_user_chat_ids()` - Get all chat IDs
- `remove_user_chat_id(chat_id)` - Remove chat ID

**Usage:**
```python
from src.services.database import UserRepository

user_repo = UserRepository()
user = user_repo.get_or_create_user("@username")
user_repo.update_user_chat_id("@username", 123456789)
```

### GiftRepository
Gift certificate database operations.

**Methods (4):**
- `add_gift(...)` - Create new gift certificate
- `update_gift(gift_id, ...)` - Update gift fields
- `get_gift_by_code(code)` - Find valid gift by code
- `get_gift_by_id(id)` - Find gift by ID

**Usage:**
```python
from src.services.database import GiftRepository

gift_repo = GiftRepository()
gift = gift_repo.get_gift_by_code("GIFT123")
```

### BookingRepository
Booking database operations.

**Methods (14):**
- `add_booking(...)` - Create new booking
- `get_booking_by_id(booking_id)` - Find booking by ID
- `get_booking_by_start_date(date)` - Find bookings by start date
- `get_booking_by_finish_date(date)` - Find bookings by end date
- `get_booking_by_period(from, to)` - Find bookings in date range
- `get_booking_by_day(date)` - Find bookings on specific day
- `get_bookings_by_month(month, year)` - Find bookings in month
- `get_booking_by_user_contact(contact)` - Find user's bookings
- `get_unpaid_bookings()` - Find all unpaid bookings
- `is_booking_between_dates(start, end)` - Check for overlaps
- `get_done_booking_count(user_id)` - Count completed bookings
- `get_all_chat_ids()` - Get unique chat IDs from bookings
- `update_booking(booking_id, ...)` - Update booking fields

**Usage:**
```python
from src.services.database import BookingRepository

booking_repo = BookingRepository()
bookings = booking_repo.get_booking_by_start_date(date(2025, 1, 1))
```

## Import Patterns

### Recommended (New Code)
```python
# Import specific repositories
from src.services.database import UserRepository, BookingRepository

user_repo = UserRepository()
booking_repo = BookingRepository()
```

### Legacy (Existing Code)
```python
# Facade pattern for backward compatibility
from src.services.database_service import DatabaseService

db = DatabaseService()  # Works as before, delegates to repositories
```

## Benefits

✅ **Repository Pattern**: Clear separation of data access logic
✅ **Better Naming**: "Repository" indicates data access layer
✅ **Organized Structure**: All DB code in `services/database/`
✅ **Single Responsibility**: One repository per entity
✅ **Easy to Find**: Clear location for all database operations
✅ **Testable**: Easy to mock repositories
✅ **Backward Compatible**: Legacy code still works

## File Sizes

| File | Lines | Responsibility |
|------|-------|---------------|
| `base.py` | 20 | Session management |
| `user_repository.py` | 156 | User operations |
| `gift_repository.py` | 112 | Gift operations |
| `booking_repository.py` | 437 | Booking operations |
| **Total** | **725** | **All DB operations** |

## Singleton Pattern

All repositories use `@singleton` decorator:

```python
from src.services.database import UserRepository

repo1 = UserRepository()
repo2 = UserRepository()
# repo1 is repo2 == True (same instance)
```

## Example: Complete User Flow

```python
from src.services.database import UserRepository, BookingRepository
from datetime import datetime

# Initialize repositories
user_repo = UserRepository()
booking_repo = BookingRepository()

# Create or get user
user = user_repo.get_or_create_user("@john_doe")

# Store chat ID when user starts bot
user_repo.update_user_chat_id("@john_doe", chat_id=123456789)

# Create booking for user
booking = booking_repo.add_booking(
    user_contact="@john_doe",
    start_date=datetime(2025, 1, 15),
    end_date=datetime(2025, 1, 17),
    # ... other parameters
)

# Get all user's bookings
user_bookings = booking_repo.get_booking_by_user_contact("@john_doe")

# Get all active chat IDs for broadcasting
chat_ids = user_repo.get_all_user_chat_ids()
```

## Migration from Old Code

**Before:**
```python
from src.services.database_service import DatabaseService

db = DatabaseService()
user = db.get_user_by_contact("@username")
```

**After (Recommended):**
```python
from src.services.database import UserRepository

user_repo = UserRepository()
user = user_repo.get_user_by_contact("@username")
```

**Or keep using DatabaseService** (it delegates to repositories automatically).
