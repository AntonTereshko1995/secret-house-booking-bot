# Architecture Refactoring Implementation Status

## Overview
This document tracks the progress of splitting the monolithic Telegram bot into two services:
1. **Backend API Service** (FastAPI)
2. **Telegram Bot Service** (presentation layer)

---

## ✅ PHASE 1: Backend API Core Infrastructure (COMPLETED)

### Completed Tasks

#### 1. Project Structure ✅
- Created `backend/` directory with proper structure
- Set up API versioning (`api/v1/`)
- Created routers, schemas, middleware directories
- Added all necessary `__init__.py` files

#### 2. Configuration ✅
- Created `backend/config/config.py` with all settings
- Added API-specific configuration (API_HOST, API_PORT, BACKEND_API_KEY)
- Created `.env.example` file
- Supports both debug and production modes (with Google Secret Manager)

#### 3. Dependencies & Database ✅
- Created `backend/api/v1/dependencies.py`
  - `get_db()` - Database session dependency
  - `verify_api_key()` - API key authentication
  - `verify_admin()` - Admin-only endpoint protection
- Updated `db/database.py` to export `SessionLocal` for FastAPI
- Database layer remains at project root (shared with both services)

#### 4. Pydantic Schemas ✅
Created type-safe request/response models:
- `backend/api/v1/schemas/booking.py` - Booking CRUD schemas
- `backend/api/v1/schemas/user.py` - User management schemas
- `backend/api/v1/schemas/gift.py` - Gift certificate schemas
- `backend/api/v1/schemas/promocode.py` - Promocode schemas
- `backend/api/v1/schemas/pricing.py` - Price calculation schemas

#### 5. API Routers ✅
Implemented complete REST API endpoints:

**Bookings Router** (`/api/v1/bookings`)
- POST `/` - Create booking
- GET `/` - List bookings (with filters)
- GET `/{booking_id}` - Get booking details
- PATCH `/{booking_id}` - Update booking
- DELETE `/{booking_id}` - Cancel booking
- GET `/user/{user_contact}` - Get user's bookings

**Availability Router** (`/api/v1/availability`)
- POST `/check` - Check if dates available
- GET `/month/{year}/{month}` - Get month availability
- GET `/dates` - Get occupied dates in range

**Pricing Router** (`/api/v1/pricing`)
- POST `/calculate` - Calculate booking price with breakdown
- GET `/tariffs` - List all available tariffs

**Users Router** (`/api/v1/users`)
- POST `/` - Create or update user
- GET `/{user_contact}` - Get user by contact
- GET `/chat/{chat_id}` - Get user by chat ID
- GET `/` - List all users (admin only)

**Gifts Router** (`/api/v1/gifts`)
- POST `/` - Create gift certificate
- GET `/{gift_id}` - Get gift details
- POST `/validate` - Validate gift certificate
- PATCH `/{gift_id}/redeem` - Mark gift as used

**Promocodes Router** (`/api/v1/promocodes`)
- POST `/` - Create promocode (admin only)
- GET `/` - List promocodes (admin only)
- POST `/validate` - Validate promocode
- DELETE `/{promocode_id}` - Delete promocode (admin only)

#### 6. FastAPI Application ✅
- Created `backend/main.py` with complete setup
- Configured CORS middleware for future web frontend
- Registered all routers with proper prefixes
- Added health check endpoint `/health`
- Added root endpoint `/` with API info
- Configured automatic Swagger UI at `/docs`
- Configured ReDoc at `/redoc`
- Added startup event for database migrations

#### 7. Business Logic Services ✅
Copied all services to `backend/services/`:
- booking_service.py
- user_service.py
- gift_service.py
- calculation_rate_service.py
- date_pricing_service.py
- calendar_service.py
- gpt_service.py
- file_service.py
- logger_service.py
- statistics_service.py
- database/ (repositories)

#### 8. Models & Helpers ✅
- Copied `src/models/` to `backend/models/`
- Copied `src/helpers/` to `backend/helpers/`
- All enums and domain models available

#### 9. Containerization ✅
- Created `backend/Dockerfile`
- Created `backend/requirements.txt` with all dependencies
- Ready for Docker deployment

#### 10. Testing ✅
- Backend imports successfully without errors
- All routers properly wired to main app
- Ready for API testing

---

## ⏳ PHASE 1: Remaining Tasks

### 11. Job Scheduler (Pending)
**Status:** Not implemented yet
**What's needed:**
- Move `src/services/job_service.py` to backend
- Integrate APScheduler into `backend/main.py`
- Add startup event to initialize scheduler
- Create `backend/services/notification_service.py` for sending reminders

**Implementation:**
```python
# In backend/main.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.services.notification_service import send_reminders

@app.on_event("startup")
async def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_reminders, 'cron', hour=10)
    scheduler.start()
```

### 12. Advanced Health Checks (Optional Enhancement)
**Current:** Basic `/health` endpoint exists
**Enhancement:**
- Add `/health/db` - Database connectivity check
- Add `/health/redis` - Redis connectivity check
- Add `/health/external` - Google Calendar, OpenAI checks

---

## 🚧 PHASE 2: Telegram Bot Refactoring (NOT STARTED)

### Critical Tasks

#### 1. Create Bot HTTP Client ⏳
**File:** `telegram_bot/client/backend_api.py`
**What's needed:**
- Async HTTP client using `aiohttp`
- Methods for all API endpoints
- Error handling and retries
- Logging of API calls

#### 2. Bot Configuration ⏳
**File:** `telegram_bot/config/config.py`
**What's needed:**
- TELEGRAM_TOKEN
- BACKEND_API_URL (e.g., "http://backend:8000")
- BACKEND_API_KEY
- ADMIN_CHAT_ID
- REDIS_URL (for bot state only)
- Remove: DATABASE_URL, Google Calendar, OpenAI keys

#### 3. Refactor All Bot Handlers ⏳
**Files to update:**
- `telegram_bot/handlers/booking_handler.py`
- `telegram_bot/handlers/available_dates_handler.py`
- `telegram_bot/handlers/admin_handler.py`
- `telegram_bot/handlers/promocode_handler.py`
- `telegram_bot/handlers/gift_certificate_handler.py`
- `telegram_bot/handlers/user_booking.py`
- `telegram_bot/handlers/menu_handler.py`
- All other handlers

**Pattern:**
```python
# BEFORE
booking_service = BookingService()
booking = booking_service.add_booking(...)

# AFTER
from telegram_bot.client.backend_api import BackendAPIClient
api_client = BackendAPIClient()
booking = await api_client.create_booking({...})
```

#### 4. Remove Direct Database Access ⏳
- Remove all imports from `db.models`
- Remove all imports from `src.services` (except Redis)
- Ensure bot only communicates via API

#### 5. Bot Requirements & Dockerfile ⏳
**File:** `telegram_bot/requirements.txt`
**Lighter dependencies:**
- python-telegram_bot[job-queue]
- aiohttp
- redis
- python-dotenv
- loguru

**Remove:**
- sqlalchemy
- alembic
- google-api-python-client
- openai

**File:** `telegram_bot/Dockerfile`

---

## 🔧 PHASE 3: Integration & Deployment (NOT STARTED)

### 1. Docker Compose ⏳
**File:** `docker-compose.yml`
**Services:**
- backend (port 8000)
- telegram_bot
- redis

### 2. Documentation ⏳
- Update main `README.md` with new architecture
- Create `backend/README.md` (API documentation)
- Create `telegram_bot/README.md` (Bot documentation)
- Create `DEPLOYMENT.md` (deployment guide)

### 3. Integration Testing ⏳
- Test backend starts independently
- Test bot starts and connects to backend
- Test complete booking flow end-to-end
- Test error handling (API down, invalid input)

---

## 📊 Progress Summary

### Phase 1: Backend API
**Status:** ~90% Complete
**Completed:** 10/12 tasks
**Remaining:** Job scheduler, advanced health checks

### Phase 2: Bot Refactoring
**Status:** 0% Complete
**Estimated effort:** 2-3 days
**Critical path:** Create API client → Refactor handlers

### Phase 3: Integration
**Status:** 0% Complete
**Estimated effort:** 1-2 days
**Blockers:** Phase 2 completion

---

## 🎯 Next Steps

### Immediate Actions (To Complete Phase 1)

1. **Add Job Scheduler to Backend**
   ```bash
   # Add to backend/requirements.txt
   apscheduler

   # Create backend/services/notification_service.py
   # Update backend/main.py with scheduler
   ```

2. **Test Backend API Independently**
   ```bash
   cd backend
   ENV=debug uvicorn main:app --reload --port 8000

   # Open http://localhost:8000/docs
   # Test endpoints with Swagger UI
   ```

### Starting Phase 2 (Bot Refactoring)

1. **Create Bot Structure**
   ```bash
   mkdir -p telegram_bot/client telegram_bot/config telegram_bot/handlers
   ```

2. **Create API Client**
   - Implement `BackendAPIClient` with aiohttp
   - Add methods for all endpoints
   - Add error handling and logging

3. **Refactor Handlers**
   - Start with simple handlers (menu, price)
   - Move to complex handlers (booking flow)
   - Test each handler individually

---

## 🔑 Key Decisions & Patterns

### Database Access
- **Backend:** Full access via SQLAlchemy
- **Bot:** NO direct access, only via API
- **Shared:** Database remains at project root for now

### Authentication
- **API:** X-API-Key header authentication
- **Bot ↔ Backend:** Bot uses BACKEND_API_KEY
- **Admin endpoints:** `verify_admin()` dependency

### Error Handling
- **Backend:** Return structured JSON errors
- **Bot:** Translate API errors to user-friendly messages

### Configuration
- **Shared:** Redis URL, Admin Chat ID
- **Backend-only:** Database, Google Calendar, OpenAI, GPT
- **Bot-only:** Telegram Token, Backend API URL

---

## 🧪 Validation Commands

### Backend Validation
```bash
# Test imports
python -c "import backend.main"

# Start backend
cd backend
ENV=debug uvicorn main:app --reload

# Test health check
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs

# Test API endpoint
curl -X GET "http://localhost:8000/api/v1/pricing/tariffs" \
  -H "X-API-Key: dev-api-key-12345"
```

### Full Stack Validation (After Phase 2-3)
```bash
# Start all services
docker-compose up --build

# Test bot interaction
# Send /start to bot in Telegram
```

---

## 📝 Notes

- All code follows PRP guidelines and anti-patterns
- API versioning (/api/v1/) implemented for future changes
- CORS configured for future web frontend
- Swagger/OpenAPI docs auto-generated
- Database schema unchanged - no migration needed
- Services use singleton pattern (can be refactored to DI later)

---

**Last Updated:** $(date)
**Status:** Phase 1 nearly complete, ready to begin Phase 2
