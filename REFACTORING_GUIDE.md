# 🔧 Handler Refactoring Guide

## Overview

This guide shows how to refactor bot handlers to use the Backend API instead of direct database access.

---

## Pattern: Replace Service Calls with API Calls

### Before (Direct Database)
```python
from src.services.booking_service import BookingService
from src.services.user_service import UserService

booking_service = BookingService()
user_service = UserService()

# In handler function
booking = booking_service.add_booking(
    user_contact=contact,
    start_date=start_date,
    end_date=end_date,
    tariff=tariff,
    # ... many parameters
)

user = user_service.get_user_by_contact(contact)
```

### After (Via API)
```python
from telegram_bot.client.backend_api import BackendAPIClient, APIError
import logging

logger = logging.getLogger(__name__)

# In handler function
api_client = BackendAPIClient()

try:
    # Create booking via API
    booking = await api_client.create_booking({
        "user_contact": contact,
        "start_date": start_date.isoformat(),  # Convert to ISO format
        "end_date": end_date.isoformat(),
        "tariff": tariff.value,  # Get enum value
        "number_of_guests": guests,
        "has_sauna": has_sauna,
        "chat_id": update.effective_chat.id,
        "price": calculated_price
    })

    # Get user via API
    user = await api_client.get_user(contact)

except APIError as e:
    logger.error(f"API call failed: {e}")
    await update.message.reply_text(
        "Извините, произошла ошибка. Попробуйте позже."
    )
    return ConversationHandler.END
```

---

## Common Replacements

### 1. User Operations

```python
# OLD
from src.services.user_service import UserService
user_service = UserService()
user = user_service.get_user_by_contact(contact)
user = user_service.get_or_create_user(contact)
user_service.update_chat_id(contact, chat_id)

# NEW
from telegram_bot.client.backend_api import BackendAPIClient
api_client = BackendAPIClient()
user = await api_client.get_user(contact)
user = await api_client.create_or_update_user({"contact": contact})
user = await api_client.create_or_update_user({"contact": contact, "chat_id": chat_id})
```

### 2. Booking Operations

```python
# OLD
from src.services.booking_service import BookingService
booking_service = BookingService()
booking = booking_service.add_booking(...)
bookings = booking_service.get_booking_by_user_contact(contact)
booking = booking_service.get_booking_by_id(booking_id)
booking_service.update_booking(booking_id, is_canceled=True)

# NEW
from telegram_bot.client.backend_api import BackendAPIClient
api_client = BackendAPIClient()
booking = await api_client.create_booking({...})
bookings = await api_client.get_user_bookings(contact)
booking = await api_client.get_booking(booking_id)
await api_client.cancel_booking(booking_id)
```

### 3. Price Calculation

```python
# OLD
from src.services.calculation_rate_service import CalculationRateService
calc_service = CalculationRateService()
price = calc_service.calculate_price_for_date(
    booking_date=start_date.date(),
    tariff=tariff,
    duration_hours=duration,
    is_sauna=has_sauna,
    # ...
)

# NEW
from telegram_bot.client.backend_api import BackendAPIClient
api_client = BackendAPIClient()
result = await api_client.calculate_price({
    "tariff": tariff.value,
    "start_date": start_date,
    "end_date": end_date,
    "has_sauna": has_sauna,
    "number_of_guests": guests
})
price = result["total_price"]
```

### 4. Availability Check

```python
# OLD
from src.services.booking_service import BookingService
booking_service = BookingService()
is_booked = booking_service.is_booking_between_dates(start_date, end_date)
bookings = booking_service.get_bookings_by_month(month, year)

# NEW
from telegram_bot.client.backend_api import BackendAPIClient
api_client = BackendAPIClient()
result = await api_client.check_availability(start_date, end_date)
is_available = result["available"]

availability = await api_client.get_month_availability(year, month)
occupied_dates = availability["occupied_dates"]
```

### 5. Gift Certificates

```python
# OLD
from src.services.gift_service import GiftService
gift_service = GiftService()
gift = gift_service.get_gift_by_number(number)
gift_service.mark_gift_as_used(gift_id)

# NEW
from telegram_bot.client.backend_api import BackendAPIClient
api_client = BackendAPIClient()
result = await api_client.validate_gift(number)
if result["valid"]:
    gift = result["gift"]
    await api_client.redeem_gift(gift["id"])
```

### 6. Promocodes

```python
# OLD
from src.services.database.promocode_repository import PromocodeRepository
promo_repo = PromocodeRepository()
promo = promo_repo.get_promocode_by_code(code)
promocodes = promo_repo.get_all_promocodes()

# NEW
from telegram_bot.client.backend_api import BackendAPIClient
api_client = BackendAPIClient()
result = await api_client.validate_promocode(code)
if result["valid"]:
    discount = result["discount_percentage"]

promocodes = await api_client.list_promocodes()
```

---

## Import Updates

### Remove These Imports
```python
# DELETE - Direct database access
from src.services.booking_service import BookingService
from src.services.user_service import UserService
from src.services.gift_service import GiftService
from src.services.calculation_rate_service import CalculationRateService
from src.services.database.promocode_repository import PromocodeRepository
from src.services.calendar_service import CalendarService
from db.models.booking import BookingBase
from db.models.user import UserBase
```

### Add These Imports
```python
# ADD - API client
from telegram_bot.client.backend_api import BackendAPIClient, APIError
import logging

logger = logging.getLogger(__name__)
```

### Keep These Imports
```python
# KEEP - Bot UI and navigation
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from src.constants import *  # State constants
from telegram_bot.services.redis import *  # Redis for state management
```

---

## Error Handling Pattern

```python
async def some_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_client = BackendAPIClient()

    try:
        # Try API call
        result = await api_client.some_method(...)

    except APIError as e:
        # Log error
        logger.error(f"API Error in {__name__}: {e}")

        # User-friendly message
        await update.effective_message.reply_text(
            "Извините, произошла ошибка при обработке вашего запроса. "
            "Пожалуйста, попробуйте позже или свяжитесь с администратором."
        )

        # Return to appropriate state
        return ConversationHandler.END  # or MENU, or other state

    except Exception as e:
        # Unexpected error
        logger.exception(f"Unexpected error in {__name__}: {e}")

        await update.effective_message.reply_text(
            "Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже."
        )

        return ConversationHandler.END
```

---

## DateTime Handling

The API expects ISO format strings for datetime values:

```python
from datetime import datetime

# Convert datetime to ISO string for API
start_date = datetime(2025, 12, 20, 14, 0)
api_data = {
    "start_date": start_date.isoformat(),  # "2025-12-20T14:00:00"
    "end_date": end_date.isoformat()
}

# API returns ISO strings, convert back if needed
booking = await api_client.create_booking(api_data)
start_str = booking["start_date"]  # "2025-12-20T14:00:00"
start_dt = datetime.fromisoformat(start_str)
```

---

## Enum Handling

```python
from backend.models.enum.tariff import Tariff

# Get enum value for API
tariff = Tariff.DAY
api_data = {
    "tariff": tariff.value  # "DAY" string, not enum
}

# Convert API response back to enum if needed
tariff_str = booking["tariff"]
tariff_enum = Tariff[tariff_str]  # or Tariff(tariff_str)
```

---

## Step-by-Step Refactoring

### 1. Read Handler File
- Identify all service imports
- Find all database calls
- Note conversation flow and states

### 2. Update Imports
```python
# At top of file
from telegram_bot.client.backend_api import BackendAPIClient, APIError
import logging

logger = logging.getLogger(__name__)
```

### 3. Replace Service Calls
- Find each `service.method()` call
- Replace with `await api_client.method()`
- Add error handling

### 4. Update Data Formatting
- Convert datetime objects to ISO strings
- Convert enums to values
- Match API schema format

### 5. Test Handler
- Start backend API
- Start bot
- Test the specific handler flow
- Check logs for errors

---

## Example: Complete Handler Refactoring

**Before:**
```python
from src.services.booking_service import BookingService

async def create_booking_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    booking_service = BookingService()

    booking = booking_service.add_booking(
        user_contact=context.user_data["contact"],
        start_date=context.user_data["start_date"],
        end_date=context.user_data["end_date"],
        tariff=context.user_data["tariff"],
        number_of_guests=context.user_data["guests"],
        has_sauna=context.user_data.get("sauna", False),
        price=context.user_data["price"],
        comment=context.user_data.get("comment", ""),
        chat_id=update.effective_chat.id
    )

    await update.message.reply_text(f"Бронирование создано! ID: {booking.id}")
    return ConversationHandler.END
```

**After:**
```python
from telegram_bot.client.backend_api import BackendAPIClient, APIError
import logging

logger = logging.getLogger(__name__)

async def create_booking_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_client = BackendAPIClient()

    try:
        booking = await api_client.create_booking({
            "user_contact": context.user_data["contact"],
            "start_date": context.user_data["start_date"].isoformat(),
            "end_date": context.user_data["end_date"].isoformat(),
            "tariff": context.user_data["tariff"].value,
            "number_of_guests": context.user_data["guests"],
            "has_sauna": context.user_data.get("sauna", False),
            "has_photoshoot": context.user_data.get("photoshoot", False),
            "has_white_bedroom": context.user_data.get("white_bedroom", False),
            "has_green_bedroom": context.user_data.get("green_bedroom", False),
            "has_secret_room": context.user_data.get("secret_room", False),
            "price": context.user_data["price"],
            "comment": context.user_data.get("comment", ""),
            "chat_id": update.effective_chat.id
        })

        await update.message.reply_text(
            f"✅ Бронирование создано!\n"
            f"ID: {booking['id']}\n"
            f"Сумма: {booking['price']} BYN"
        )

    except APIError as e:
        logger.error(f"Failed to create booking: {e}")
        await update.message.reply_text(
            "Извините, не удалось создать бронирование. "
            "Пожалуйста, попробуйте позже."
        )

    return ConversationHandler.END
```

---

## Handler Priority Order

Refactor in this order (easiest to hardest):

1. ✅ **price_handler.py** - Simple price calculation
2. ✅ **available_dates_handler.py** - Date availability
3. ✅ **booking_details_handler.py** - View bookings
4. ✅ **cancel_booking_handler.py** - Cancel operation
5. ✅ **change_booking_date_handler.py** - Update operation
6. ✅ **gift_certificate_handler.py** - Gift operations
7. ✅ **promocode_handler.py** - Promocode operations
8. ✅ **question_handler.py** - GPT integration
9. ✅ **feedback_handler.py** - Minimal changes
10. ✅ **admin_handler.py** - Admin operations
11. ✅ **menu_handler.py** - Main menu and navigation
12. ⚠️ **booking_handler.py** - Complex booking flow
13. ⚠️ **user_booking.py** - Most complex, full flow

---

## Testing Checklist

After refactoring each handler:

- [ ] No import errors
- [ ] Handler can be imported
- [ ] Backend API is running
- [ ] Bot starts without errors
- [ ] Handler responds to command
- [ ] API calls succeed
- [ ] Error handling works
- [ ] User sees appropriate messages
- [ ] Conversation flow preserved

---

## Common Issues

### Issue: Import Errors
**Solution:** Update all import paths to use `telegram_bot.` prefix

### Issue: Async/Await Errors
**Solution:** All API calls must use `await`

### Issue: datetime not serializable
**Solution:** Convert to ISO string with `.isoformat()`

### Issue: Enum not JSON serializable
**Solution:** Use `.value` to get string value

### Issue: API returns 401
**Solution:** Check `BACKEND_API_KEY` in bot config

### Issue: API returns 404
**Solution:** Check backend is running and endpoint exists

---

**Ready to refactor?** Start with `price_handler.py` - it's the simplest!
