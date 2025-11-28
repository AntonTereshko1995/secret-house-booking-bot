# 🚀 Quickstart Guide - Secret House Booking System

## Overview

The system is now split into two services:
1. **Backend API** (FastAPI) - Handles all business logic, database, external APIs
2. **Telegram Bot** - User interface, communicates with backend via REST API

---

## 📋 Prerequisites

- Python 3.10+
- Docker & Docker Compose (for containerized deployment)
- Redis (for bot conversation state)
- PostgreSQL or SQLite (database)

---

## 🏃 Quick Start (Development)

### Option 1: Run with Docker Compose (Recommended)

1. **Copy environment file:**
   ```bash
   cp .env.docker.example .env
   ```

2. **Edit `.env` file with your credentials:**
   ```bash
   # Required: Set your Telegram bot token
   TELEGRAM_TOKEN=your-actual-bot-token

   # Required: Set admin chat ID
   ADMIN_CHAT_ID=123456789

   # Optional: Change API key (default: dev-api-key-12345)
   BACKEND_API_KEY=your-secret-key
   ```

3. **Start all services:**
   ```bash
   docker-compose up --build
   ```

4. **Verify services are running:**
   ```bash
   # Check service status
   docker-compose ps

   # Check backend health
   curl http://localhost:8000/health

   # View logs
   docker-compose logs -f backend
   docker-compose logs -f telegram_bot
   ```

5. **Test the bot:**
   - Open Telegram
   - Send `/start` to your bot
   - Bot should respond (communicating with backend API)

---

### Option 2: Run Locally (Development)

#### Step 1: Start Backend API

```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt

# Set environment
export ENV=debug

# Run backend
python main.py
```

Backend will start on `http://localhost:8000`

#### Step 2: View API Documentation

Open in browser:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### Step 3: Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# List tariffs (requires API key)
curl -X GET "http://localhost:8000/api/v1/pricing/tariffs" \
  -H "X-API-Key: dev-api-key-12345"

# Calculate price
curl -X POST "http://localhost:8000/api/v1/pricing/calculate" \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "tariff": "DAY",
    "start_date": "2025-12-20T14:00:00",
    "end_date": "2025-12-21T12:00:00",
    "number_of_guests": 2,
    "has_sauna": true
  }'
```

#### Step 4: Start Telegram Bot (TODO - Phase 2)

```bash
# Install bot dependencies
cd telegram_bot
pip install -r requirements.txt

# Set environment
export ENV=debug
export BACKEND_API_URL=http://localhost:8000
export TELEGRAM_TOKEN=your-bot-token

# Run bot
python main.py
```

---

## 🧪 Testing

### Backend API Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=term-missing
```

### Integration Tests

```bash
# Start backend first
cd backend && python main.py

# In another terminal, test API
curl http://localhost:8000/health
curl -X GET http://localhost:8000/api/v1/pricing/tariffs \
  -H "X-API-Key: dev-api-key-12345"
```

---

## 📁 Project Structure

```
secret-house-booking-bot/
├── backend/                    # Backend API Service
│   ├── main.py                # FastAPI app entry point
│   ├── config/                # Configuration
│   ├── api/v1/               # API endpoints
│   │   ├── routers/          # API route handlers
│   │   └── schemas/          # Pydantic models
│   ├── services/             # Business logic
│   ├── Dockerfile            # Backend container
│   └── requirements.txt      # Backend dependencies
│
├── telegram_bot/              # Telegram Bot Service (TODO)
│   ├── main.py               # Bot entry point
│   ├── client/               # Backend API client
│   │   └── backend_api.py    # HTTP client
│   ├── config/               # Bot configuration
│   ├── handlers/             # Bot command handlers
│   ├── Dockerfile            # Bot container
│   └── requirements.txt      # Bot dependencies
│
├── db/                        # Database layer (shared)
│   ├── models/               # ORM models
│   └── database.py           # DB connection
│
├── docker-compose.yml         # Orchestration
├── .env.docker.example        # Environment template
└── README.md                 # Main documentation
```

---

## 🔑 Environment Variables

### Backend API

| Variable | Description | Required |
|----------|-------------|----------|
| `BACKEND_API_KEY` | API authentication key | Yes |
| `DATABASE_URL` | Database connection string | Yes |
| `TELEGRAM_TOKEN` | Bot token (for notifications) | Yes |
| `ADMIN_CHAT_ID` | Admin Telegram chat ID | Yes |
| `GOOGLE_CREDENTIALS` | Google Calendar credentials | Optional |
| `CALENDAR_ID` | Google Calendar ID | Optional |
| `GPT_KEY` | OpenAI API key | Optional |
| `REDIS_URL` | Redis host | Yes |
| `REDIS_PORT` | Redis port | Yes |

### Telegram Bot

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_TOKEN` | Bot token | Yes |
| `BACKEND_API_URL` | Backend API URL | Yes |
| `BACKEND_API_KEY` | API authentication key | Yes |
| `ADMIN_CHAT_ID` | Admin chat ID | Yes |
| `REDIS_URL` | Redis host (for state) | Yes |

---

## 🔍 API Endpoints

### Bookings
- `POST /api/v1/bookings` - Create booking
- `GET /api/v1/bookings` - List bookings
- `GET /api/v1/bookings/{id}` - Get booking
- `PATCH /api/v1/bookings/{id}` - Update booking
- `DELETE /api/v1/bookings/{id}` - Cancel booking

### Availability
- `POST /api/v1/availability/check` - Check dates
- `GET /api/v1/availability/month/{year}/{month}` - Month view

### Pricing
- `POST /api/v1/pricing/calculate` - Calculate price
- `GET /api/v1/pricing/tariffs` - List tariffs

### Users
- `POST /api/v1/users` - Create/update user
- `GET /api/v1/users/{contact}` - Get user

### Gifts & Promocodes
- `POST /api/v1/gifts` - Create gift certificate
- `POST /api/v1/gifts/validate` - Validate gift
- `POST /api/v1/promocodes` - Create promocode (admin)
- `POST /api/v1/promocodes/validate` - Validate promocode

**Full API documentation:** http://localhost:8000/docs

---

## 🛠️ Development Workflow

### Adding New API Endpoint

1. Create Pydantic schema in `backend/api/v1/schemas/`
2. Create router in `backend/api/v1/routers/`
3. Register router in `backend/main.py`
4. Add method to `telegram_bot/client/backend_api.py`
5. Use in bot handlers

### Database Changes

```bash
# Create migration
python -m alembic revision --autogenerate -m "description"

# Apply migration
python -m alembic upgrade head
```

---

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check dependencies
pip list | grep fastapi

# Check database
ls -la test_the_secret_house.db

# Check logs
docker-compose logs backend
```

### Bot can't connect to backend

```bash
# Test backend from bot container
docker-compose exec telegram_bot curl http://backend:8000/health

# Check network
docker network inspect secret-house-booking-bot_secret-house-network
```

### Redis connection issues

```bash
# Test Redis
docker-compose exec redis redis-cli ping
# Should return: PONG
```

---

## 📊 Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Redis health
docker-compose exec redis redis-cli ping
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f telegram_bot

# Last 100 lines
docker-compose logs --tail=100 backend
```

---

## 🚢 Deployment

### Production Checklist

- [ ] Change `BACKEND_API_KEY` to strong random value
- [ ] Set `DEBUG=false`
- [ ] Configure production database (PostgreSQL)
- [ ] Set up proper logging (Logtail, etc.)
- [ ] Configure firewall (only expose port 8000 if needed)
- [ ] Set up SSL/TLS for API (if exposing externally)
- [ ] Enable Google Secret Manager for secrets
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy

### Deploy with Docker Compose

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up --build -d

# Check status
docker-compose ps
```

---

## 📚 Additional Documentation

- **Backend API:** See `backend/README.md` (TODO)
- **Bot Handlers:** See `telegram_bot/README.md` (TODO)
- **Full Architecture:** See `PRPs/architecture-refactoring-split-bot-backend.md`
- **Implementation Status:** See `IMPLEMENTATION_STATUS.md`

---

## 💡 Tips

1. **Always start backend before bot** - Bot depends on backend API
2. **Use Swagger UI** - Great for testing API endpoints interactively
3. **Check logs** - Most issues are visible in Docker logs
4. **API Key** - Keep it secret, rotate regularly in production

---

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Verify environment variables: `docker-compose config`
3. Test backend health: `curl http://localhost:8000/health`
4. Review implementation status: `cat IMPLEMENTATION_STATUS.md`

---

**Current Status:** Backend API fully implemented ✅ | Bot refactoring in progress ⏳
