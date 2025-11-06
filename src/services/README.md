# Database Services Architecture

## Overview

The database layer has been refactored into specialized services by entity type for better code organization and maintainability.

## Service Structure

```
services/
├── base_database_service.py    # Base class with session management
├── user_service.py             # User operations (8 methods)
├── gift_service.py             # Gift certificate operations (4 methods)
├── booking_service.py          # Booking operations (14 methods)
└── database_service.py         # Facade for backward compatibility
```

## Services

### BaseDatabaseService
Base class providing database session management.

```python
from src.services.base_database_service import BaseDatabaseService

class MyService(BaseDatabaseService):
    def my_method(self):
        with self.Session() as session:
            # Use session here
            pass
```

### UserService
Handles all user-related operations.

**Methods:**
- `add_user(contact)` - Create new user
- `get_or_create_user(contact)` - Get or create user
- `get_user_by_contact(contact)` - Find user by contact
- `get_user_by_id(user_id)` - Find user by ID
- `update_user_chat_id(contact, chat_id)` - Store/update chat ID
- `get_all_user_chat_ids()` - Get all chat IDs
- `remove_user_chat_id(chat_id)` - Remove chat ID

**Usage:**
```python
from src.services.user_service import UserService

user_service = UserService()
user = user_service.get_or_create_user("@username")
user_service.update_user_chat_id("@username", 123456789)
```

### GiftService
Handles gift certificate operations.

**Methods:**
- `add_gift(...)` - Create new gift certificate
- `update_gift(gift_id, ...)` - Update gift fields
- `get_gift_by_code(code)` - Find valid gift by code
- `get_gift_by_id(id)` - Find gift by ID

**Usage:**
```python
from src.services.gift_service import GiftService

gift_service = GiftService()
gift = gift_service.get_gift_by_code("GIFT123")
```

### BookingService
Handles all booking operations.

**Methods:**
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
- `update_booking(booking_id, ...)` - Update booking fields

**Usage:**
```python
from src.services.booking_service import BookingService

booking_service = BookingService()
bookings = booking_service.get_booking_by_start_date(date(2025, 1, 1))
```

### DatabaseService (Facade)
Provides backward compatibility by delegating to specialized services.

**Usage (Legacy - for existing code):**
```python
from src.services.database_service import DatabaseService

db_service = DatabaseService()
user = db_service.get_or_create_user("@username")  # Delegates to UserService
booking = db_service.get_booking_by_id(1)  # Delegates to BookingService
```

## Migration Guide

### For New Code
Use specialized services directly:

**Before:**
```python
from src.services.database_service import DatabaseService

db = DatabaseService()
user = db.get_user_by_contact("@username")
```

**After:**
```python
from src.services.user_service import UserService

user_service = UserService()
user = user_service.get_user_by_contact("@username")
```

### For Existing Code
No changes required! `DatabaseService` maintains full backward compatibility.

## Benefits

✅ **Better Organization**: Code grouped by entity type
✅ **Easier to Navigate**: ~150-200 lines per service vs 660 lines
✅ **Single Responsibility**: Each service handles one entity
✅ **Reusability**: Services can be used independently
✅ **Testability**: Easier to mock and test individual services
✅ **Backward Compatible**: Existing code continues to work

## File Size Comparison

| File | Lines | Responsibility |
|------|-------|---------------|
| `base_database_service.py` | 18 | Session management |
| `user_service.py` | 159 | User operations |
| `gift_service.py` | 116 | Gift operations |
| `booking_service.py` | 477 | Booking operations |
| `database_service.py` | 259 | Facade (delegates) |
| **Old database_service.py** | **660** | **Everything** |

## Singleton Pattern

All services use the `@singleton` decorator to ensure single instance:

```python
from src.services.user_service import UserService

user_service1 = UserService()
user_service2 = UserService()
# user_service1 is user_service2 == True
```
