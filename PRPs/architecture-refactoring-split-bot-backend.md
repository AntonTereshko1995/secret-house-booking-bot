name: "Architecture Refactoring: Split Telegram Bot and Backend API"
description: |
  Refactor monolithic Python Telegram bot application into two separate services:
  1. Telegram Bot Service (presentation layer)
  2. Backend API Service (business logic + data layer)

  This enables future web frontend integration and independent scaling.

---

## Goal
Разделить текущий монолитный проект на две независимые части:
1. **Telegram Bot Service** - обрабатывает взаимодействие с пользователями через Telegram
2. **Backend API Service** - REST API с бизнес-логикой и доступом к базе данных

Обе части должны работать независимо, при этом бот будет использовать API для всех операций. В будущем веб-сайт сможет использовать тот же Backend API для бронирования дома.

## Why
- **Разделение ответственности**: Telegram bot только для UI/UX, backend для бизнес-логики
- **Масштабируемость**: Независимое масштабирование бота и backend
- **Переиспользование**: Один backend API может обслуживать и бота, и будущий веб-сайт
- **Maintainability**: Проще тестировать, развивать и деплоить отдельные сервисы
- **Technology flexibility**: Веб-фронтенд может быть написан на любой технологии

## What
Создать микросервисную архитектуру с двумя сервисами:

### Telegram Bot Service
- Обрабатывает Telegram events (messages, callbacks)
- Управляет conversation states через Redis
- Отображает интерфейс пользователю (keyboards, messages)
- Все данные получает/отправляет через Backend API
- **Не имеет прямого доступа к базе данных**

### Backend API Service (FastAPI)
- REST API endpoints для всех операций (bookings, users, gifts, promocodes)
- Бизнес-логика (rate calculation, date validation, calendar integration)
- Прямой доступ к PostgreSQL/SQLite database
- Интеграции с внешними сервисами (Google Calendar, OpenAI GPT)
- Аутентификация и авторизация

### Success Criteria
- [ ] Backend API запускается независимо на отдельном порту
- [ ] Telegram Bot запускается независимо и взаимодействует с API
- [ ] Все существующие функции бота работают через API
- [ ] API документирован через Swagger/OpenAPI
- [ ] Оба сервиса можно деплоить отдельно (separate Docker containers)
- [ ] Тесты проходят для обоих сервисов
- [ ] Миграция данных не требуется (shared database)

## All Needed Context

### Documentation & References
```yaml
# FastAPI Documentation
- url: https://fastapi.tiangolo.com/tutorial/sql-databases/
  why: Structuring FastAPI with SQLAlchemy, dependency injection patterns

- url: https://fastapi.tiangolo.com/tutorial/bigger-applications/
  why: Project structure for larger applications with multiple routers

# Microservices Architecture
- url: https://medium.com/@amverait/friends-hello-8460dfe86ef1
  why: Telegram bot + FastAPI + webhooks architecture example

- url: https://viktorsapozhok.github.io/fastapi-oauth2-postgres/
  why: 3-tier FastAPI design pattern (routers, services, schemas, models)

# REST API Design
- url: https://stackoverflow.blog/2020/03/02/best-practices-for-rest-api-design/
  why: REST API endpoint naming, versioning, error handling best practices

# Python Telegram Bot
- url: https://docs.python-telegram-bot.org/en/stable/
  why: Working with python-telegram-bot library, async patterns

# Current Project Files (patterns to follow)
- file: src/services/booking_service.py
  why: Business logic pattern to extract into API endpoints

- file: src/handlers/user_booking.py
  why: Handler pattern showing conversation flow to preserve

- file: db/models/booking.py
  why: Database models to reuse in backend

- file: src/config/config.py
  why: Configuration management pattern

- file: src/main.py
  why: Current application entry point and handler registration
```

### Current Codebase Structure
```
secret-house-booking-bot/
├── src/
│   ├── main.py                      # Telegram bot entry point
│   ├── config/
│   │   └── config.py               # Environment-based configuration
│   ├── handlers/                   # Telegram conversation handlers
│   │   ├── menu_handler.py
│   │   ├── user_booking.py
│   │   ├── admin_handler.py
│   │   ├── promocode_handler.py
│   │   └── ... (11+ handlers)
│   ├── services/                   # Business logic services
│   │   ├── booking_service.py     # Booking CRUD operations
│   │   ├── user_service.py        # User management
│   │   ├── calculation_rate_service.py  # Price calculations
│   │   ├── calendar_service.py    # Google Calendar integration
│   │   ├── gpt_service.py         # OpenAI integration
│   │   ├── redis/                 # Redis session management
│   │   └── database/              # Database repositories
│   ├── models/                    # Domain models and enums
│   │   ├── booking_draft.py
│   │   ├── enum/tariff.py
│   │   └── ...
│   ├── helpers/                   # Utility functions
│   └── decorators/                # Error handling decorators
├── db/
│   ├── database.py                # SQLAlchemy engine setup
│   ├── models/                    # ORM models
│   │   ├── booking.py
│   │   ├── user.py
│   │   ├── gift.py
│   │   └── promocode.py
│   └── run_migrations.py
├── alembic/                       # Database migrations
├── requirements.txt
└── Dockerfile

Key Dependencies:
- python-telegram-bot (bot framework)
- sqlalchemy (ORM)
- alembic (migrations)
- redis (session state)
- google-api-python-client (Calendar API)
- openai (GPT integration)
- logtail-python (logging)
```

### Desired Codebase Structure
```
secret-house-booking-bot/
├── backend/                        # NEW: Backend API Service
│   ├── main.py                    # FastAPI application entry
│   ├── api/
│   │   ├── v1/                    # API versioning
│   │   │   ├── __init__.py
│   │   │   ├── routers/           # API route handlers
│   │   │   │   ├── bookings.py   # Booking endpoints
│   │   │   │   ├── users.py      # User endpoints
│   │   │   │   ├── gifts.py      # Gift certificate endpoints
│   │   │   │   ├── promocodes.py # Promocode endpoints
│   │   │   │   ├── availability.py # Date availability
│   │   │   │   └── pricing.py    # Price calculation
│   │   │   ├── schemas/           # Pydantic request/response models
│   │   │   │   ├── booking.py
│   │   │   │   ├── user.py
│   │   │   │   ├── gift.py
│   │   │   │   └── promocode.py
│   │   │   └── dependencies.py   # Dependency injection (DB session, auth)
│   │   └── middleware/            # Auth, logging, CORS
│   ├── services/                  # Business logic (moved from src/)
│   │   ├── booking_service.py
│   │   ├── calculation_rate_service.py
│   │   ├── calendar_service.py
│   │   ├── gpt_service.py
│   │   └── ...
│   ├── db/                        # Database layer (shared with bot)
│   │   ├── database.py           # SQLAlchemy engine
│   │   ├── models/               # ORM models
│   │   └── repositories/         # Data access layer
│   ├── config/
│   │   └── config.py             # Backend-specific config
│   ├── requirements.txt          # Backend dependencies
│   └── Dockerfile               # Backend container
│
├── telegram-bot/                  # REFACTORED: Telegram Bot Service
│   ├── main.py                   # Bot entry point
│   ├── handlers/                 # Telegram handlers (refactored)
│   │   ├── menu_handler.py
│   │   ├── booking_handler.py
│   │   ├── admin_handler.py
│   │   └── ...
│   ├── client/                   # NEW: API client
│   │   └── backend_api.py       # HTTP client for Backend API
│   ├── services/
│   │   └── redis/               # Redis for bot state only
│   ├── config/
│   │   └── config.py           # Bot-specific config
│   ├── requirements.txt        # Bot dependencies (lighter)
│   └── Dockerfile             # Bot container
│
├── shared/                      # OPTIONAL: Shared code
│   ├── models/                 # Domain models/enums
│   └── utils/                  # Common utilities
│
├── docker-compose.yml          # Orchestrate both services
└── README.md                   # Updated documentation

File Responsibilities:
- backend/api/v1/routers/bookings.py: REST endpoints for booking CRUD
- backend/api/v1/schemas/booking.py: Pydantic models for request/response validation
- backend/services/: All business logic, calculations, external API integrations
- telegram-bot/handlers/: Only UI logic - display keyboards, handle callbacks
- telegram-bot/client/backend_api.py: HTTP client to call Backend API
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Current codebase uses singleton pattern heavily
# Example: BookingService, CalculationRateService are singletons
# In FastAPI, use dependency injection instead:
from fastapi import Depends
def get_booking_service() -> BookingService:
    return BookingService()

# CRITICAL: python-telegram-bot is fully async
# All handlers must be async functions
# When calling Backend API from bot, use aiohttp (not requests)
import aiohttp
async with aiohttp.ClientSession() as session:
    async with session.post(url, json=data) as resp:
        return await resp.json()

# CRITICAL: Current code directly imports from src/services
# After refactoring, bot should NEVER import backend services
# All communication via HTTP API

# GOTCHA: SQLAlchemy sessions in FastAPI
# Use dependency injection with yield for proper session management
async def get_db():
    async with AsyncSession(engine) as session:
        yield session

# GOTCHA: Redis is used for TWO purposes currently
# 1. Telegram conversation state (RedisPersistence) - stays in bot
# 2. Session management (redis_session_service.py) - might need refactoring

# GOTCHA: Config management currently in src/config/config.py
# Split into backend/config.py and telegram-bot/config.py
# Shared secrets can use same Secret Manager approach

# CRITICAL: Database migrations (Alembic)
# Should run from Backend service only
# Bot should never run migrations

# GOTCHA: Job scheduler (job_service.py) runs in main.py
# Move to Backend API as background tasks or separate worker
# Use FastAPI BackgroundTasks or APScheduler

# CRITICAL: Error handling
# Backend API should return structured JSON errors
# Bot handlers should translate API errors to user-friendly messages
```

## Implementation Blueprint

### Phase 1: Backend API Core Infrastructure

#### Data Models - Pydantic Schemas
Create Pydantic models for API request/response validation:

```python
# backend/api/v1/schemas/booking.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class BookingBase(BaseModel):
    start_date: datetime
    end_date: datetime
    tariff: str
    number_of_guests: int
    has_sauna: bool = False
    has_photoshoot: bool = False
    has_white_bedroom: bool = False
    has_green_bedroom: bool = False
    has_secret_room: bool = False
    comment: Optional[str] = None
    wine_preference: Optional[str] = None
    transfer_address: Optional[str] = None

class BookingCreate(BookingBase):
    user_contact: str
    chat_id: int
    gift_id: Optional[int] = None
    promocode_id: Optional[int] = None

class BookingResponse(BookingBase):
    id: int
    user_id: int
    price: float
    is_prepaymented: bool
    is_canceled: bool
    is_done: bool

    class Config:
        from_attributes = True  # For SQLAlchemy ORM compatibility

class BookingUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_canceled: Optional[bool] = None
    is_prepaymented: Optional[bool] = None
    price: Optional[float] = None

# Similar schemas for User, Gift, Promocode
```

### List of Implementation Tasks

```yaml
Task 1: Setup Backend FastAPI Project Structure
  GOAL: Create basic FastAPI application with project structure

  CREATE backend/main.py:
    - Initialize FastAPI app with metadata (title, version, description)
    - Add CORS middleware for future web frontend
    - Include health check endpoint
    - Setup startup/shutdown events for database connection

  CREATE backend/api/v1/__init__.py:
    - Create APIRouter for v1 endpoints

  CREATE backend/api/v1/dependencies.py:
    - Implement get_db() dependency for database sessions
    - Implement get_current_user() for authentication (placeholder)

  CREATE backend/config/config.py:
    - Copy from src/config/config.py
    - Add API_HOST, API_PORT, API_PREFIX settings
    - Keep database, Redis, external API configurations

  CREATE backend/requirements.txt:
    - fastapi
    - uvicorn[standard]
    - sqlalchemy
    - alembic
    - python-dotenv
    - google-api-python-client
    - openai
    - redis
    - aiohttp
    - pydantic
    - python-multipart

Task 2: Move Database Layer to Backend
  GOAL: Centralize all database access in backend service

  COPY db/ directory to backend/db/:
    - Keep models/ directory (booking.py, user.py, gift.py, promocode.py)
    - Keep database.py (SQLAlchemy engine setup)
    - Keep alembic/ for migrations

  MODIFY backend/db/database.py:
    - Update imports to reference backend/ paths
    - Keep existing engine and session factory
    - Add async session support if needed

  CREATE backend/db/repositories/:
    - Move src/services/database/booking_repository.py
    - Move src/services/database/user_repository.py
    - Move src/services/database/gift_repository.py
    - Move src/services/database/promocode_repository.py
    - Update imports to use backend paths

Task 3: Move Business Logic Services to Backend
  GOAL: Centralize business logic in backend

  COPY services to backend/services/:
    - booking_service.py (booking CRUD)
    - user_service.py (user management)
    - gift_service.py (gift certificates)
    - calculation_rate_service.py (price calculations)
    - date_pricing_service.py (date-based pricing)
    - calendar_service.py (Google Calendar integration)
    - gpt_service.py (OpenAI integration)
    - file_service.py (read tariff config files)
    - logger_service.py (logging)
    - statistics_service.py (statistics)

  MODIFY backend/services/*.py:
    - Update all imports to reference backend/ paths
    - Replace src.services imports with backend.services
    - Replace db.models imports with backend.db.models
    - Keep singleton pattern OR refactor to dependency injection

  KEEP job_service.py discussion:
    - Option A: Move to backend as APScheduler background task
    - Option B: Separate worker service
    - Recommend: Move to backend with FastAPI BackgroundTasks

Task 4: Create Pydantic Schemas for API
  GOAL: Define request/response models for type safety

  CREATE backend/api/v1/schemas/booking.py:
    - BookingBase (common fields)
    - BookingCreate (for POST /bookings)
    - BookingUpdate (for PATCH /bookings/{id})
    - BookingResponse (response with all fields + computed)
    - AvailabilityRequest (check date availability)
    - AvailabilityResponse

  CREATE backend/api/v1/schemas/user.py:
    - UserBase, UserCreate, UserResponse
    - UserStatistics (booking counts)

  CREATE backend/api/v1/schemas/gift.py:
    - GiftCertificateCreate
    - GiftCertificateResponse
    - GiftCertificateValidate (check validity)

  CREATE backend/api/v1/schemas/promocode.py:
    - PromocodeCreate
    - PromocodeResponse
    - PromocodeValidate

  CREATE backend/api/v1/schemas/pricing.py:
    - PriceCalculationRequest
    - PriceCalculationResponse (with breakdown)

Task 5: Implement Booking API Endpoints
  GOAL: Create REST API for booking operations

  CREATE backend/api/v1/routers/bookings.py:
    - POST /api/v1/bookings - create new booking
      * Accept BookingCreate schema
      * Call booking_service.add_booking()
      * Return BookingResponse
      * Handle conflicts (dates already booked)

    - GET /api/v1/bookings - list bookings with filters
      * Query params: start_date, end_date, user_contact, is_admin
      * Call booking_service.get_booking_by_start_date_period()
      * Return List[BookingResponse]

    - GET /api/v1/bookings/{booking_id} - get booking details
      * Call booking_service.get_booking_by_id()
      * Return BookingResponse or 404

    - PATCH /api/v1/bookings/{booking_id} - update booking
      * Accept BookingUpdate schema
      * Call booking_service.update_booking()
      * Return updated BookingResponse

    - DELETE /api/v1/bookings/{booking_id} - cancel booking
      * Set is_canceled=True
      * Delete Google Calendar event
      * Return 204 No Content

    - GET /api/v1/bookings/user/{user_contact} - user's bookings
      * Call booking_service.get_booking_by_user_contact()
      * Return List[BookingResponse]

Task 6: Implement Availability API Endpoints
  GOAL: Check date availability for bookings

  CREATE backend/api/v1/routers/availability.py:
    - GET /api/v1/availability/dates - get available dates
      * Query params: start_date, end_date, month, year
      * Call booking_service.get_bookings_by_month()
      * Return list of occupied dates

    - POST /api/v1/availability/check - check if dates available
      * Accept start_date, end_date
      * Call booking_service.is_booking_between_dates()
      * Return {available: bool, conflicting_bookings: [...]}

    - GET /api/v1/availability/month/{year}/{month} - month view
      * Call booking_service.get_bookings_by_month()
      * Return calendar-friendly format

Task 7: Implement Pricing API Endpoints
  GOAL: Price calculation endpoints

  CREATE backend/api/v1/routers/pricing.py:
    - POST /api/v1/pricing/calculate - calculate booking price
      * Accept PriceCalculationRequest (tariff, dates, add-ons)
      * Call calculation_rate_service.calculate_price_for_date()
      * Return PriceCalculationResponse with breakdown:
        {
          base_price: 500,
          sauna_price: 100,
          extra_hours_price: 50,
          total: 650,
          currency: "BYN"
        }

    - GET /api/v1/pricing/tariffs - list available tariffs
      * Call calculation_rate_service._try_load_tariffs()
      * Return list of RentalPrice objects

Task 8: Implement User API Endpoints
  GOAL: User management endpoints

  CREATE backend/api/v1/routers/users.py:
    - POST /api/v1/users - create/update user
      * Accept UserCreate schema
      * Call user_service.get_or_create_user()
      * Return UserResponse

    - GET /api/v1/users/{user_contact} - get user details
      * Call user_service.get_user_by_contact()
      * Return UserResponse with statistics

    - GET /api/v1/users - list all users (admin only)
      * Call user_service through repository
      * Return List[UserResponse]

    - GET /api/v1/users/chat/{chat_id} - get user by chat_id
      * Call user_service.get_user_by_chat_id()
      * Return UserResponse or 404

Task 9: Implement Gift Certificate API Endpoints
  GOAL: Gift certificate management

  CREATE backend/api/v1/routers/gifts.py:
    - POST /api/v1/gifts - create gift certificate
      * Accept GiftCertificateCreate
      * Call gift_service.add_gift()
      * Return GiftCertificateResponse

    - GET /api/v1/gifts/{gift_id} - get gift details
      * Call gift_service.get_gift_by_id()
      * Return GiftCertificateResponse

    - POST /api/v1/gifts/validate - validate gift certificate
      * Accept {certificate_number: str}
      * Call gift_service.get_gift_by_number()
      * Return {valid: bool, gift: GiftCertificateResponse or null}

    - PATCH /api/v1/gifts/{gift_id}/redeem - mark gift as used
      * Set is_done=True
      * Return updated gift

Task 10: Implement Promocode API Endpoints
  GOAL: Promocode management

  CREATE backend/api/v1/routers/promocodes.py:
    - POST /api/v1/promocodes - create promocode (admin only)
      * Accept PromocodeCreate
      * Call promocode repository
      * Return PromocodeResponse

    - GET /api/v1/promocodes - list all promocodes (admin only)
      * Query params: is_active
      * Return List[PromocodeResponse]

    - POST /api/v1/promocodes/validate - validate promocode
      * Accept {code: str}
      * Check if exists, active, not expired
      * Return {valid: bool, discount: float, promocode: ...}

    - DELETE /api/v1/promocodes/{promocode_id} - delete promocode
      * Soft delete or hard delete
      * Return 204

Task 11: Register All Routers in Main App
  GOAL: Wire up all endpoints

  MODIFY backend/main.py:
    - Import all routers from backend.api.v1.routers
    - Include each router with prefix:
      app.include_router(
          bookings_router,
          prefix="/api/v1/bookings",
          tags=["bookings"]
      )
    - Add health check endpoint:
      @app.get("/health")
      async def health():
          return {"status": "healthy"}
    - Add root endpoint with API documentation link
    - Configure CORS for future web frontend

Task 12: Add Authentication Middleware (Basic)
  GOAL: Secure admin endpoints

  CREATE backend/api/middleware/auth.py:
    - Implement simple API key authentication for MVP
    - Check X-API-Key header
    - For admin endpoints, verify API key matches config

  CREATE backend/api/v1/dependencies.py additions:
    - async def verify_admin(api_key: str = Header(alias="X-API-Key")):
        if api_key != ADMIN_API_KEY:
            raise HTTPException(401, "Unauthorized")

  APPLY to admin routes:
    - Promocode creation/deletion
    - User listing
    - Booking listing (admin view)

Task 13: Move Job Scheduler to Backend
  GOAL: Move reminder jobs to backend

  MODIFY backend/main.py:
    - Install APScheduler: pip install apscheduler
    - Import job_service logic
    - Create startup event to initialize scheduler:
      @app.on_event("startup")
      async def start_scheduler():
          scheduler = AsyncIOScheduler()
          scheduler.add_job(send_reminders, 'cron', hour=10)
          scheduler.start()

  CREATE backend/services/notification_service.py:
    - Extract send_reminders logic from job_service.py
    - Send notifications via Telegram Bot API directly
    - Use TELEGRAM_TOKEN and ADMIN_CHAT_ID from config

Task 14: Create Backend Dockerfile and Run Configuration
  GOAL: Containerize backend service

  CREATE backend/Dockerfile:
    FROM python:3.10-slim
    WORKDIR /app
    COPY backend/requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    COPY backend/ ./backend/
    COPY db/ ./db/
    COPY shared/ ./shared/
    EXPOSE 8000
    CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

  CREATE backend/.env.example:
    - Document all required environment variables
    - DATABASE_URL, REDIS_URL, API keys, etc.

---

### Phase 2: Telegram Bot Refactoring

Task 15: Create Bot HTTP Client for Backend API
  GOAL: Create async HTTP client to communicate with backend

  CREATE telegram-bot/client/backend_api.py:
    - Use aiohttp for async HTTP requests
    - Base class with common methods:
      * _request(method, endpoint, data=None, params=None)
      * _get(endpoint, params=None)
      * _post(endpoint, data)
      * _patch(endpoint, data)
      * _delete(endpoint)

    - Booking methods:
      * create_booking(booking_data: dict) -> dict
      * get_bookings(filters: dict) -> list
      * get_booking(booking_id: int) -> dict
      * update_booking(booking_id: int, updates: dict) -> dict
      * cancel_booking(booking_id: int) -> bool
      * get_user_bookings(user_contact: str) -> list

    - Availability methods:
      * check_availability(start_date, end_date) -> dict
      * get_month_availability(year: int, month: int) -> list

    - Pricing methods:
      * calculate_price(calculation_data: dict) -> dict
      * get_tariffs() -> list

    - User methods:
      * create_or_update_user(user_data: dict) -> dict
      * get_user(user_contact: str) -> dict

    - Gift methods:
      * validate_gift(certificate_number: str) -> dict
      * redeem_gift(gift_id: int) -> dict

    - Promocode methods:
      * validate_promocode(code: str) -> dict
      * list_promocodes() -> list (admin)
      * create_promocode(promo_data: dict) -> dict (admin)

    - Error handling:
      * Catch aiohttp exceptions
      * Parse API error responses
      * Return user-friendly error messages
      * Log errors with LoggerService

Task 16: Refactor Bot Configuration
  GOAL: Separate bot config from backend config

  CREATE telegram-bot/config/config.py:
    - TELEGRAM_TOKEN (bot token)
    - BACKEND_API_URL (e.g., "http://backend:8000")
    - BACKEND_API_KEY (for authenticated requests)
    - ADMIN_CHAT_ID (for admin commands)
    - REDIS_URL, REDIS_PORT (for bot state only)
    - Remove: DATABASE_URL, Google Calendar, OpenAI keys
      (these now only in backend config)

Task 17: Refactor Booking Handler to Use API
  GOAL: Update booking flow to use backend API instead of direct DB

  MODIFY telegram-bot/handlers/booking_handler.py:
    - Import BackendAPIClient from telegram-bot.client
    - Replace all booking_service calls with API calls:

      BEFORE:
      booking = booking_service.add_booking(...)

      AFTER:
      api_client = BackendAPIClient()
      booking = await api_client.create_booking({
          "user_contact": contact,
          "start_date": start_date.isoformat(),
          "end_date": end_date.isoformat(),
          "tariff": tariff.value,
          ...
      })

    - Update price calculation:
      BEFORE: calculation_rate_service.calculate_price_for_date(...)
      AFTER: await api_client.calculate_price({...})

    - Update availability check:
      BEFORE: booking_service.is_booking_between_dates(...)
      AFTER: result = await api_client.check_availability(start, end)
              is_available = result["available"]

    - Handle API errors gracefully:
      try:
          booking = await api_client.create_booking(data)
      except APIError as e:
          await update.message.reply_text(
              "Извините, произошла ошибка при создании бронирования."
          )
          logger.error(f"Booking creation failed: {e}")

Task 18: Refactor Available Dates Handler to Use API
  GOAL: Update date picker to use backend availability API

  MODIFY telegram-bot/handlers/available_dates_handler.py:
    - Replace booking_service.get_bookings_by_month() with:
      api_client = BackendAPIClient()
      availability = await api_client.get_month_availability(year, month)

    - Update calendar rendering to use API response

Task 19: Refactor Admin Handler to Use API
  GOAL: Update admin commands to use backend API

  MODIFY telegram-bot/handlers/admin_handler.py:
    - get_booking_list:
      bookings = await api_client.get_bookings({"is_admin": True})

    - get_statistics:
      # Backend should provide statistics endpoint
      stats = await api_client.get_statistics()

    - broadcast commands:
      users = await api_client.get_users()
      # Send messages to users

Task 20: Refactor Promocode Handler to Use API
  GOAL: Update promocode management to use backend

  MODIFY telegram-bot/handlers/promocode_handler.py:
    - list_promocodes:
      promocodes = await api_client.list_promocodes()

    - create_promocode:
      promo = await api_client.create_promocode({
          "code": code,
          "discount_percentage": discount,
          "promocode_type": type.value
      })

    - delete_promocode:
      await api_client.delete_promocode(promo_id)

Task 21: Refactor Gift Certificate Handler to Use API
  GOAL: Update gift certificate flow

  MODIFY telegram-bot/handlers/gift_certificate_handler.py:
    - Validate gift:
      result = await api_client.validate_gift(certificate_number)
      if result["valid"]:
          # Proceed with booking

    - Redeem gift after booking:
      await api_client.redeem_gift(gift_id)

Task 22: Update User Booking Handler
  GOAL: Refactor user booking flow

  MODIFY telegram-bot/handlers/user_booking.py:
    - Replace all service calls with API calls
    - Preserve conversation flow and state management
    - Update error handling for API errors

Task 23: Update Menu Handler
  GOAL: Ensure menu handler works with API

  MODIFY telegram-bot/handlers/menu_handler.py:
    - Replace user_service calls with API:
      user = await api_client.get_user(contact)
      if not user:
          user = await api_client.create_or_update_user({
              "contact": contact,
              "chat_id": chat_id
          })

Task 24: Remove Direct Database Access from Bot
  GOAL: Ensure bot doesn't import any database code

  DELETE from telegram-bot/:
    - All imports from db.models
    - All imports from src.services.database
    - All imports from src.services except redis

  VERIFY:
    - grep -r "from db.models" telegram-bot/
    - grep -r "from src.services.booking_service" telegram-bot/
    - Should return no results

Task 25: Create Bot Dockerfile
  GOAL: Containerize bot service

  CREATE telegram-bot/Dockerfile:
    FROM python:3.10-slim
    WORKDIR /app
    COPY telegram-bot/requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    COPY telegram-bot/ ./telegram-bot/
    COPY shared/ ./shared/
    CMD ["python", "telegram-bot/main.py"]

  CREATE telegram-bot/requirements.txt:
    - python-telegram-bot[job-queue]
    - aiohttp
    - redis
    - python-dotenv
    - loguru

    REMOVE:
    - sqlalchemy
    - alembic
    - google-api-python-client
    - openai

---

### Phase 3: Integration and Deployment

Task 26: Create Docker Compose Configuration
  GOAL: Orchestrate both services together

  CREATE docker-compose.yml:
    version: '3.8'

    services:
      backend:
        build:
          context: .
          dockerfile: backend/Dockerfile
        container_name: secret-house-backend
        ports:
          - "8000:8000"
        environment:
          - DATABASE_URL=${DATABASE_URL}
          - REDIS_URL=redis://redis:6379
          - GOOGLE_CREDENTIALS=${GOOGLE_CREDENTIALS}
          - CALENDAR_ID=${CALENDAR_ID}
          - GPT_KEY=${GPT_KEY}
        depends_on:
          - redis
        volumes:
          - ./data:/app/data
        restart: unless-stopped

      telegram-bot:
        build:
          context: .
          dockerfile: telegram-bot/Dockerfile
        container_name: secret-house-telegram-bot
        environment:
          - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
          - BACKEND_API_URL=http://backend:8000
          - BACKEND_API_KEY=${BACKEND_API_KEY}
          - REDIS_URL=redis://redis:6379
          - ADMIN_CHAT_ID=${ADMIN_CHAT_ID}
        depends_on:
          - backend
          - redis
        restart: unless-stopped

      redis:
        image: redis:7-alpine
        container_name: secret-house-redis
        ports:
          - "6379:6379"
        restart: unless-stopped

  CREATE .env.example:
    # Backend
    DATABASE_URL=sqlite:///./data/the_secret_house.db
    GOOGLE_CREDENTIALS=...
    CALENDAR_ID=...
    GPT_KEY=...
    BACKEND_API_KEY=...

    # Telegram Bot
    TELEGRAM_TOKEN=...
    ADMIN_CHAT_ID=...

Task 27: Update Documentation
  GOAL: Document new architecture

  UPDATE README.md:
    - Add architecture diagram (bot -> API -> DB)
    - Update setup instructions for both services
    - Document API endpoints (link to Swagger)
    - Docker compose usage
    - Environment variables for each service
    - Development workflow (run backend, then bot)

  CREATE backend/README.md:
    - API documentation
    - Endpoint list with examples
    - Authentication
    - Development setup

  CREATE telegram-bot/README.md:
    - Bot functionality
    - Handler descriptions
    - How to add new commands

Task 28: Add API Documentation with Swagger
  GOAL: Auto-generate API docs

  MODIFY backend/main.py:
    - FastAPI automatically generates Swagger UI at /docs
    - Customize:
      app = FastAPI(
          title="Secret House Booking API",
          description="Backend API for house booking system",
          version="1.0.0",
          docs_url="/docs",
          redoc_url="/redoc"
      )
    - Add response models and status codes to all endpoints
    - Add example values to schemas

Task 29: Implement Health Checks
  GOAL: Add health endpoints for monitoring

  CREATE backend/api/v1/routers/health.py:
    - GET /health - basic health check
    - GET /health/db - database connection check
    - GET /health/redis - Redis connection check
    - GET /health/external - Google Calendar, OpenAI checks
    - Return: {status: "healthy", checks: {...}}

  ADD to telegram-bot/main.py:
    - Startup check: ping backend API
    - If backend unreachable, retry with backoff
    - Log health status

Task 30: Add Logging and Monitoring
  GOAL: Structured logging for both services

  ENSURE backend/services/logger_service.py:
    - Log all API requests (path, method, status, duration)
    - Log database queries (slow query logging)
    - Log external API calls (Google Calendar, OpenAI)
    - Use structured JSON logging for production

  ENSURE telegram-bot/main.py:
    - Log all incoming Telegram updates
    - Log API calls to backend (endpoint, status, duration)
    - Log errors with full context

Task 31: Create Migration Script (Optional)
  GOAL: Smooth transition from monolith to microservices

  CREATE scripts/migrate.sh:
    - Backup current database
    - Run Alembic migrations (if any schema changes)
    - Verify data integrity
    - Test API endpoints
    - Test bot functionality

  Note: Since database schema doesn't change,
  migration is mostly about code deployment

Task 32: Testing - Backend API
  GOAL: Ensure backend works independently

  CREATE backend/tests/test_api_bookings.py:
    - Test POST /api/v1/bookings (create booking)
    - Test GET /api/v1/bookings (list bookings)
    - Test GET /api/v1/bookings/{id} (get booking)
    - Test PATCH /api/v1/bookings/{id} (update)
    - Test DELETE /api/v1/bookings/{id} (cancel)
    - Test conflict scenarios (overlapping bookings)

  CREATE backend/tests/test_api_pricing.py:
    - Test price calculation with different tariffs
    - Test date-based pricing rules
    - Test add-ons (sauna, photoshoot, etc.)

  RUN:
    cd backend && pytest tests/ -v

Task 33: Testing - Integration Tests
  GOAL: Test bot <-> backend communication

  CREATE tests/integration/test_booking_flow.py:
    - Start backend API (in test mode)
    - Mock Telegram updates
    - Simulate complete booking flow
    - Verify API calls are made correctly
    - Verify bot responds correctly

  CREATE tests/integration/test_api_client.py:
    - Test BackendAPIClient methods
    - Test error handling
    - Test retries on failure

Task 34: Performance Testing
  GOAL: Ensure backend can handle load

  CREATE tests/performance/locustfile.py:
    - Use Locust for load testing
    - Simulate concurrent booking requests
    - Test availability checks
    - Measure response times
    - Target: <200ms for simple endpoints

  RUN:
    locust -f tests/performance/locustfile.py

Task 35: Deployment Instructions
  GOAL: Document production deployment

  CREATE DEPLOYMENT.md:
    - Prerequisites (Docker, Docker Compose)
    - Environment variable setup
    - Database initialization
    - Running migrations
    - Starting services with docker-compose
    - Monitoring and logs (docker-compose logs -f)
    - Backup strategy
    - Rollback procedure
    - Scaling considerations (multiple bot instances)
```

### Integration Points
```yaml
DATABASE:
  - No schema changes required
  - Alembic migrations run from backend only
  - Both services can share same DATABASE_URL (backend writes, bot doesn't)

CONFIG:
  - Split src/config/config.py into:
    * backend/config/config.py (all secrets)
    * telegram-bot/config/config.py (bot token, API URL)
  - Shared: REDIS_URL, ADMIN_CHAT_ID

REDIS:
  - Bot uses Redis for conversation state (RedisPersistence)
  - Backend could use Redis for caching (optional)
  - Same Redis instance, different keys/namespaces

EXTERNAL APIs:
  - Google Calendar: backend only
  - OpenAI GPT: backend only
  - Telegram Bot API: bot only (for updates), backend only (for notifications)

AUTHENTICATION:
  - Backend API: API key authentication (X-API-Key header)
  - Bot authenticates to backend using BACKEND_API_KEY
  - Admin commands: validate chat_id in bot, validate API key in backend
```

## Validation Loop

### Level 1: Syntax & Linting
```bash
# Backend
cd backend
ruff check . --fix
mypy .

# Telegram Bot
cd telegram-bot
ruff check . --fix
mypy .

# Expected: No errors
```

### Level 2: Unit Tests
```bash
# Backend tests
cd backend
pytest tests/ -v --cov=. --cov-report=term-missing

# Bot tests (if any)
cd telegram-bot
pytest tests/ -v

# Expected: All tests pass
```

### Level 3: Integration Testing
```bash
# Start backend in terminal 1
cd backend
ENV=debug uvicorn main:app --reload --port 8000

# Test backend health
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# Test API documentation
open http://localhost:8000/docs
# Verify Swagger UI loads with all endpoints

# Test booking creation
curl -X POST http://localhost:8000/api/v1/bookings \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${BACKEND_API_KEY}" \
  -d '{
    "user_contact": "+375291234567",
    "start_date": "2025-12-01T14:00:00",
    "end_date": "2025-12-02T12:00:00",
    "tariff": "DAY",
    "number_of_guests": 2,
    "has_sauna": true,
    "chat_id": 123456789
  }'
# Expected: 201 Created with booking response

# Start bot in terminal 2
cd telegram-bot
ENV=debug python main.py

# Test bot interaction
# Send /start command to bot in Telegram
# Try to create a booking through bot
# Verify booking appears in backend database

# Expected: Bot responds, booking created, no errors in logs
```

### Level 4: Docker Testing
```bash
# Build and start all services
docker-compose up --build

# Verify services are running
docker-compose ps
# Expected: backend, telegram-bot, redis all "Up"

# Check backend logs
docker-compose logs backend
# Expected: "Application startup complete"

# Check bot logs
docker-compose logs telegram-bot
# Expected: "Bot started"

# Test backend from host
curl http://localhost:8000/health

# Test bot interaction via Telegram
# Send /start to bot, create booking
# Verify in backend logs that API was called

# Stop services
docker-compose down
```

## Final Validation Checklist
- [ ] Backend starts independently: `cd backend && uvicorn main:app`
- [ ] Backend API docs accessible: http://localhost:8000/docs
- [ ] Backend health check passes: `curl http://localhost:8000/health`
- [ ] All backend tests pass: `cd backend && pytest`
- [ ] Bot starts independently: `cd telegram-bot && python main.py`
- [ ] Bot can communicate with backend (check logs)
- [ ] No direct database imports in bot code
- [ ] Docker Compose starts all services: `docker-compose up`
- [ ] Can create booking via API: `curl -X POST ...`
- [ ] Can create booking via bot: `/start` -> book flow
- [ ] All existing bot features work (gifts, promocodes, admin commands)
- [ ] Error handling works (API down, invalid input)
- [ ] Logs are structured and informative
- [ ] README.md updated with new architecture

---

## Anti-Patterns to Avoid
- ❌ Don't let bot directly import database models or services
- ❌ Don't use synchronous HTTP client (requests) in async bot code
- ❌ Don't skip error handling in API client (aiohttp can fail)
- ❌ Don't hardcode backend URL in bot (use config)
- ❌ Don't run database migrations from bot service
- ❌ Don't expose sensitive data in API responses (passwords, tokens)
- ❌ Don't forget to validate input in backend (don't trust bot)
- ❌ Don't use GET requests for operations that modify data (use POST/PATCH)
- ❌ Don't return raw database exceptions to API clients (sanitize errors)
- ❌ Don't skip API versioning (/api/v1/) - needed for future changes

---

## Success Metrics & Confidence Score

### Expected Outcomes After Implementation
1. **Two Independent Services**: Backend and Bot can start separately
2. **Shared Database**: Both services work with same database (backend writes, bot via API)
3. **API-First Communication**: All bot<->backend communication via REST API
4. **Documentation**: Swagger docs auto-generated for all endpoints
5. **Containerized**: Both services have Dockerfiles and docker-compose
6. **Testable**: Unit tests for backend, integration tests for API client
7. **Scalable**: Can run multiple bot instances, can scale backend separately
8. **Future-Ready**: Web frontend can use same Backend API

### Confidence Score: **8.5/10**

**Reasoning:**
- ✅ Clear separation of concerns between bot (UI) and backend (logic)
- ✅ FastAPI is well-documented and mature framework
- ✅ Existing business logic can be moved with minimal changes
- ✅ Database schema doesn't need to change
- ✅ Comprehensive task breakdown with concrete steps
- ✅ Validation loops at each stage (syntax, tests, integration)
- ⚠️ Moderate complexity: ~35 tasks, but each is well-defined
- ⚠️ Need to refactor all bot handlers (13 handlers)
- ⚠️ Need to create API client with proper error handling
- ⚠️ Redis usage needs clarity (bot state vs. caching)
- ⚠️ Job scheduler (reminders) needs testing in backend

**Risk Mitigation:**
- Start with backend core + 1-2 simple endpoints (health, tariffs)
- Test thoroughly before refactoring complex bot handlers
- Keep git branches for rollback
- Test end-to-end with Docker Compose early
- Have fallback plan (can deploy monolith if critical bugs)

**Timeline Estimate:**
- Phase 1 (Backend API): 2-3 days
- Phase 2 (Bot Refactoring): 2-3 days
- Phase 3 (Integration & Testing): 1-2 days
- **Total: 5-8 days** (for experienced developer)

This PRP provides sufficient context, step-by-step tasks, validation gates, and examples for successful one-pass implementation. The architecture is sound, industry-standard, and future-proof for web frontend integration.
