# 🏠 Secret House Booking System

> **Microservices Architecture:** Telegram Bot + FastAPI Backend

A comprehensive house rental booking system split into two independent services for scalability and future web frontend integration.

---

## 🎯 Architecture Overview

```
┌─────────────────┐
│  Telegram Bot   │ ←─── Users interact via Telegram
│   (UI Layer)    │
└────────┬────────┘
         │ HTTP/REST
         │ (aiohttp)
         ↓
┌─────────────────┐
│  Backend API    │ ←─── Business Logic & Data
│   (FastAPI)     │
└────────┬────────┘
         │
         ├──→ Database (SQLite/PostgreSQL)
         ├──→ Google Calendar API
         ├──→ OpenAI GPT
         └──→ Redis (state management)
```

### Services

1. **🤖 Telegram Bot Service** (Port: N/A)
   - User interface via Telegram
   - Conversation state management
   - UI rendering (keyboards, messages)
   - **No direct database access** - all via API

2. **⚡ Backend API Service** (Port: 8000)
   - REST API with OpenAPI/Swagger docs
   - Business logic (pricing, availability, bookings)
   - Database operations (SQLAlchemy ORM)
   - External API integrations (Calendar, GPT)
   - API key authentication

3. **💾 Redis** (Port: 6379)
   - Bot conversation state
   - Session management

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.10+ (for local development)
- Telegram Bot Token ([Create one](https://t.me/botfather))

### 1. Clone & Configure

```bash
# Copy environment file
cp .env.docker.example .env

# Edit .env with your credentials
nano .env
```

**Required variables:**
```bash
TELEGRAM_TOKEN=your-bot-token-from-botfather
ADMIN_CHAT_ID=your-telegram-chat-id
BACKEND_API_KEY=your-secret-api-key
```

### 2. Start Services

```bash
# Start all services with Docker Compose
docker-compose up --build

# Or run in background
docker-compose up -d
```

### 3. Verify

```bash
# Check services are running
docker-compose ps

# Test backend API
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs
```

### 4. Test Bot

- Open Telegram
- Find your bot
- Send `/start`
- Bot should respond! 🎉

---

## 📁 Project Structure

```
secret-house-booking-bot/
│
├── backend/                      # Backend API Service ✅ COMPLETE
│   ├── main.py                  # FastAPI app
│   ├── api/v1/
│   │   ├── routers/             # API endpoints
│   │   │   ├── bookings.py      # Booking CRUD
│   │   │   ├── availability.py  # Date availability
│   │   │   ├── pricing.py       # Price calculation
│   │   │   ├── users.py         # User management
│   │   │   ├── gifts.py         # Gift certificates
│   │   │   └── promocodes.py    # Promocodes
│   │   ├── schemas/             # Pydantic models
│   │   └── dependencies.py      # Auth & DB
│   ├── services/                # Business logic
│   ├── config/                  # Configuration
│   ├── Dockerfile               # Backend container
│   └── requirements.txt
│
├── telegram_bot/                 # Telegram Bot Service ⏳ IN PROGRESS
│   ├── main.py                  # Bot entry point (TODO)
│   ├── client/
│   │   └── backend_api.py       # HTTP client ✅
│   ├── config/
│   │   └── config.py            # Bot config ✅
│   ├── handlers/                # Bot handlers (TODO: refactor)
│   ├── services/redis/          # Conversation state
│   ├── Dockerfile               # Bot container ✅
│   └── requirements.txt         # Bot dependencies ✅
│
├── db/                          # Database Layer (Shared)
│   ├── models/                  # SQLAlchemy ORM
│   │   ├── booking.py
│   │   ├── user.py
│   │   ├── gift.py
│   │   └── promocode.py
│   └── database.py              # DB connection
│
├── docker-compose.yml           # Service orchestration ✅
├── .env.docker.example          # Environment template ✅
├── QUICKSTART.md                # Quick setup guide ✅
├── IMPLEMENTATION_STATUS.md     # Detailed progress ✅
├── test_backend.sh              # API test script ✅
└── README.md                    # This file
```

---

## 🔌 API Endpoints

### 📚 Bookings
- `POST /api/v1/bookings` - Create booking
- `GET /api/v1/bookings` - List bookings (with filters)
- `GET /api/v1/bookings/{id}` - Get booking details
- `PATCH /api/v1/bookings/{id}` - Update booking
- `DELETE /api/v1/bookings/{id}` - Cancel booking
- `GET /api/v1/bookings/user/{contact}` - User's bookings

### 📅 Availability
- `POST /api/v1/availability/check` - Check if dates available
- `GET /api/v1/availability/month/{year}/{month}` - Month calendar view
- `GET /api/v1/availability/dates` - Get occupied dates

### 💰 Pricing
- `POST /api/v1/pricing/calculate` - Calculate price with breakdown
- `GET /api/v1/pricing/tariffs` - List all tariffs

### 👤 Users
- `POST /api/v1/users` - Create/update user
- `GET /api/v1/users/{contact}` - Get user
- `GET /api/v1/users/chat/{chat_id}` - Get by chat ID
- `GET /api/v1/users` - List users (admin only)

### 🎁 Gifts
- `POST /api/v1/gifts` - Create gift certificate
- `GET /api/v1/gifts/{id}` - Get gift details
- `POST /api/v1/gifts/validate` - Validate certificate
- `PATCH /api/v1/gifts/{id}/redeem` - Redeem gift

### 🏷️ Promocodes
- `POST /api/v1/promocodes` - Create promocode (admin)
- `GET /api/v1/promocodes` - List promocodes (admin)
- `POST /api/v1/promocodes/validate` - Validate code
- `DELETE /api/v1/promocodes/{id}` - Delete promocode

**🔍 Explore all endpoints:** http://localhost:8000/docs

---

## 🔑 Authentication

All API endpoints require authentication via API key:

```bash
curl -X GET "http://localhost:8000/api/v1/pricing/tariffs" \
  -H "X-API-Key: your-api-key"
```

**Security Notes:**
- Change `BACKEND_API_KEY` in production
- Use strong random values (32+ characters)
- Never commit API keys to git
- Rotate keys regularly

---

## 🧪 Testing

### Test Backend API

```bash
# Quick test
./test_backend.sh

# Or manually
export API_URL=http://localhost:8000
export API_KEY=dev-api-key-12345

# Health check
curl $API_URL/health

# List tariffs
curl -H "X-API-Key: $API_KEY" $API_URL/api/v1/pricing/tariffs

# Calculate price
curl -X POST $API_URL/api/v1/pricing/calculate \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "tariff": "DAY",
    "start_date": "2025-12-20T14:00:00",
    "end_date": "2025-12-21T12:00:00",
    "number_of_guests": 2,
    "has_sauna": true
  }'
```

### Interactive Testing

Open Swagger UI in browser:
```
http://localhost:8000/docs
```

---

## 📊 Implementation Status

### ✅ Phase 1: Backend API (COMPLETE)
- [x] FastAPI application setup
- [x] Configuration management
- [x] Pydantic schemas (type-safe)
- [x] 6 API routers with 30+ endpoints
- [x] Authentication middleware
- [x] Database integration
- [x] Business logic services
- [x] Docker containerization
- [x] Auto-generated API docs

### ⏳ Phase 2: Bot Refactoring (IN PROGRESS)
- [x] Bot directory structure
- [x] Backend API client (async HTTP)
- [x] Bot configuration (minimal)
- [x] Bot Dockerfile & requirements
- [ ] Refactor bot handlers (13 handlers)
- [ ] Remove direct DB access from bot
- [ ] Bot main.py entry point
- [ ] Integration testing

### ⏳ Phase 3: Integration (PENDING)
- [x] Docker Compose configuration
- [x] Documentation (Quickstart, README)
- [ ] End-to-end testing
- [ ] Performance testing
- [ ] Production deployment guide

**Overall Progress:** ~60% complete

See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for detailed breakdown.

---

## 🏗️ Development

### Run Backend Locally

```bash
cd backend
pip install -r requirements.txt
export ENV=debug
python main.py
```

Backend runs on `http://localhost:8000`

### Run Bot Locally (TODO)

```bash
cd telegram_bot
pip install -r requirements.txt
export ENV=debug
export BACKEND_API_URL=http://localhost:8000
export TELEGRAM_TOKEN=your-token
python main.py
```

### Database Migrations

```bash
# Create migration
python -m alembic revision --autogenerate -m "description"

# Apply migrations
python -m alembic upgrade head

# Rollback
python -m alembic downgrade -1
```

---

## 📖 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Quick setup guide
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Detailed progress tracking
- **[PRPs/architecture-refactoring-split-bot-backend.md](PRPs/architecture-refactoring-split-bot-backend.md)** - Complete PRP with all tasks
- **API Docs** - http://localhost:8000/docs (auto-generated)

---

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check Python version
python --version  # Should be 3.10+

# Check dependencies
pip list | grep fastapi

# Check database file
ls -la *.db

# View logs
docker-compose logs backend
```

### Bot can't connect to backend

```bash
# Test connectivity from bot container
docker-compose exec telegram_bot curl http://backend:8000/health

# Check environment variables
docker-compose exec telegram_bot env | grep BACKEND
```

### API returns 401 Unauthorized

```bash
# Check API key
echo $BACKEND_API_KEY

# Test with correct header
curl -H "X-API-Key: your-key" http://localhost:8000/api/v1/pricing/tariffs
```

---

## 🌟 Features

### Current (Backend API)
- ✅ Complete REST API with 30+ endpoints
- ✅ Auto-generated OpenAPI/Swagger documentation
- ✅ API key authentication
- ✅ Price calculation with date-specific pricing
- ✅ Availability checking (day, month, range)
- ✅ Booking CRUD operations
- ✅ Gift certificate management
- ✅ Promocode system
- ✅ User management
- ✅ Google Calendar integration
- ✅ OpenAI GPT integration
- ✅ Docker containerization

### Coming Soon (Bot Refactoring)
- ⏳ Refactored bot handlers using API
- ⏳ No direct database access in bot
- ⏳ Improved error handling
- ⏳ Better separation of concerns

### Future (After Bot Refactoring)
- 🔮 Web frontend (React/Next.js)
- 🔮 Mobile app (React Native)
- 🔮 Analytics dashboard
- 🔮 Multi-language support
- 🔮 Payment gateway integration

---

## 🤝 Contributing

### Adding New API Endpoint

1. Create Pydantic schema in `backend/api/v1/schemas/`
2. Create router in `backend/api/v1/routers/`
3. Register router in `backend/main.py`
4. Add method to bot API client
5. Update documentation

### Code Style

- Python 3.10+ with type hints
- FastAPI best practices
- Async/await patterns
- Pydantic for validation
- SQLAlchemy for ORM

---

## 📝 License

[Add your license here]

---

## 👥 Authors

[Add author information]

---

## 🙏 Acknowledgments

- FastAPI framework
- python-telegram_bot library
- SQLAlchemy ORM
- Docker & Docker Compose

---

## 📞 Support

For issues or questions:
1. Check [QUICKSTART.md](QUICKSTART.md)
2. Review [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)
3. Check API docs at `/docs`
4. Review Docker logs

---

**Status:** Backend API Complete ✅ | Bot Refactoring In Progress ⏳ | Integration Pending ⏳

**Last Updated:** 2025-01-XX
