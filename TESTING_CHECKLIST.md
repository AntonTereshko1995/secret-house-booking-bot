# ✅ Testing Checklist

## Backend API Testing

### Prerequisites
- [ ] Backend is running (`cd backend && python main.py`)
- [ ] Redis is running
- [ ] Database file exists
- [ ] API key is set (`BACKEND_API_KEY`)

### Automated Tests
```bash
# Run automated test script
./test_backend.sh
```

Expected results:
- [ ] ✓ Test 1: Health Check (200 OK)
- [ ] ✓ Test 2: List Tariffs (200 OK, returns array)
- [ ] ✓ Test 3: Calculate Price (200 OK, returns total_price)
- [ ] ✓ Test 4: Check Availability (200 OK, returns available: true/false)
- [ ] ✓ Test 5: Authentication (401 without API key)

### Manual API Tests

#### 1. Health Check
```bash
curl http://localhost:8000/health
```
- [ ] Returns: `{"status":"healthy",...}`
- [ ] HTTP 200

#### 2. API Documentation
```bash
open http://localhost:8000/docs
```
- [ ] Swagger UI loads
- [ ] All 6 routers visible (bookings, availability, pricing, users, gifts, promocodes)
- [ ] Can see all endpoints
- [ ] Can test endpoints interactively

#### 3. List Tariffs
```bash
curl -X GET "http://localhost:8000/api/v1/pricing/tariffs" \
  -H "X-API-Key: dev-api-key-12345"
```
- [ ] Returns array of tariffs
- [ ] Each has: tariff, name, price, duration_hours, etc.
- [ ] HTTP 200

#### 4. Calculate Price
```bash
curl -X POST "http://localhost:8000/api/v1/pricing/calculate" \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "tariff": "DAY",
    "start_date": "2025-12-20T14:00:00",
    "end_date": "2025-12-21T12:00:00",
    "number_of_guests": 2,
    "has_sauna": true,
    "has_secret_room": false,
    "has_second_bedroom": false,
    "has_photoshoot": false
  }'
```
- [ ] Returns price breakdown
- [ ] Has: base_price, sauna_price, total_price, etc.
- [ ] total_price = base_price + sauna_price
- [ ] HTTP 200

#### 5. Check Availability
```bash
curl -X POST "http://localhost:8000/api/v1/availability/check" \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-12-20T14:00:00",
    "end_date": "2025-12-21T12:00:00"
  }'
```
- [ ] Returns: `{"available": true/false, "conflicting_bookings": [...]}`
- [ ] HTTP 200

#### 6. Create User
```bash
curl -X POST "http://localhost:8000/api/v1/users" \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "+375291234567",
    "user_name": "Test User",
    "chat_id": 123456789
  }'
```
- [ ] Returns user object with id
- [ ] HTTP 200

#### 7. Create Booking
```bash
curl -X POST "http://localhost:8000/api/v1/bookings" \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "user_contact": "+375291234567",
    "start_date": "2025-12-25T14:00:00",
    "end_date": "2025-12-26T12:00:00",
    "tariff": "DAY",
    "number_of_guests": 2,
    "has_sauna": true,
    "has_photoshoot": false,
    "has_white_bedroom": true,
    "has_green_bedroom": false,
    "has_secret_room": false,
    "comment": "Test booking",
    "chat_id": 123456789,
    "price": 500
  }'
```
- [ ] Returns booking object with id
- [ ] HTTP 201

#### 8. Get Bookings
```bash
curl -X GET "http://localhost:8000/api/v1/bookings?start_date=2025-12-01&end_date=2025-12-31" \
  -H "X-API-Key: dev-api-key-12345"
```
- [ ] Returns array of bookings
- [ ] Includes previously created booking
- [ ] HTTP 200

#### 9. Validate Gift Certificate
```bash
curl -X POST "http://localhost:8000/api/v1/gifts/validate" \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"certificate_number": "GIFT123"}'
```
- [ ] Returns: `{"valid": true/false, "message": "..."}`
- [ ] HTTP 200

#### 10. Validate Promocode
```bash
curl -X POST "http://localhost:8000/api/v1/promocodes/validate" \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"code": "SUMMER2025"}'
```
- [ ] Returns: `{"valid": true/false, "discount_percentage": ...}`
- [ ] HTTP 200

### Error Handling Tests

#### 11. Missing API Key
```bash
curl -X GET "http://localhost:8000/api/v1/pricing/tariffs"
```
- [ ] Returns error
- [ ] HTTP 401 Unauthorized

#### 12. Invalid API Key
```bash
curl -X GET "http://localhost:8000/api/v1/pricing/tariffs" \
  -H "X-API-Key: wrong-key"
```
- [ ] Returns error
- [ ] HTTP 401 Unauthorized

#### 13. Invalid Tariff
```bash
curl -X POST "http://localhost:8000/api/v1/pricing/calculate" \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "tariff": "INVALID",
    "start_date": "2025-12-20T14:00:00",
    "end_date": "2025-12-21T12:00:00",
    "number_of_guests": 2
  }'
```
- [ ] Returns error message
- [ ] HTTP 400 Bad Request

#### 14. Booking Not Found
```bash
curl -X GET "http://localhost:8000/api/v1/bookings/99999" \
  -H "X-API-Key: dev-api-key-12345"
```
- [ ] Returns error "Booking not found"
- [ ] HTTP 404 Not Found

---

## Docker Compose Testing

### Prerequisites
- [ ] `.env` file created from `.env.docker.example`
- [ ] `.env` has valid `TELEGRAM_TOKEN`
- [ ] `.env` has valid `ADMIN_CHAT_ID`

### Start Services
```bash
docker-compose up --build
```

#### Container Checks
- [ ] 3 containers start: backend, telegram_bot, redis
- [ ] No error messages in startup logs
- [ ] Backend log shows: "🚀 Starting Secret House Booking API"
- [ ] Backend log shows: "Application startup complete"
- [ ] Bot log shows startup (or error about missing handlers)
- [ ] Redis log shows: "Ready to accept connections"

#### Service Health Checks
```bash
# Check running containers
docker-compose ps
```
- [ ] All containers status: "Up"

```bash
# Test backend from host
curl http://localhost:8000/health
```
- [ ] Returns: `{"status":"healthy"}`

```bash
# Test backend from bot container
docker-compose exec telegram_bot curl http://backend:8000/health
```
- [ ] Returns: `{"status":"healthy"}`

```bash
# Test Redis
docker-compose exec redis redis-cli ping
```
- [ ] Returns: "PONG"

#### Network Checks
```bash
# Check network
docker network ls | grep secret-house
```
- [ ] Network exists: `secret-house-booking-bot_secret-house-network`

```bash
# Inspect network
docker network inspect secret-house-booking-bot_secret-house-network
```
- [ ] All 3 containers connected
- [ ] Each has IP address

#### Volume Checks
```bash
# Check volumes
docker volume ls | grep secret-house
```
- [ ] Volume exists: `secret-house-booking-bot_redis-data`

#### Log Checks
```bash
# Backend logs
docker-compose logs backend | grep ERROR
```
- [ ] No critical errors (some warnings OK)

```bash
# Bot logs
docker-compose logs telegram_bot | grep ERROR
```
- [ ] May have import errors (expected until handlers refactored)

```bash
# Redis logs
docker-compose logs redis | grep -i error
```
- [ ] No errors

### Stop Services
```bash
docker-compose down
```
- [ ] All containers stopped
- [ ] All containers removed
- [ ] Network removed (redis-data volume persists)

---

## Integration Tests (After Bot Refactoring)

### Prerequisites
- [ ] Backend running
- [ ] Bot running
- [ ] Both connected to same Redis
- [ ] Bot handlers refactored to use API

### Bot Tests

#### 1. Start Command
- [ ] Send `/start` to bot
- [ ] Bot responds with main menu
- [ ] No errors in logs

#### 2. Price Calculation
- [ ] Select "Узнать цену" (Get Price)
- [ ] Select tariff
- [ ] Select dates
- [ ] Select add-ons
- [ ] Bot shows calculated price
- [ ] Check backend logs: API call to `/api/v1/pricing/calculate`

#### 3. Booking Creation
- [ ] Start booking flow
- [ ] Fill in all details
- [ ] Complete booking
- [ ] Bot confirms booking created
- [ ] Check backend logs: API call to `/api/v1/bookings` (POST)
- [ ] Query backend: `curl -H "X-API-Key: ..." http://localhost:8000/api/v1/bookings`
- [ ] Booking appears in list

#### 4. Admin Commands
- [ ] Send `/booking_list` (from admin account)
- [ ] Bot shows bookings
- [ ] Check backend logs: API call to `/api/v1/bookings?is_admin=true`

#### 5. Promocode
- [ ] Send `/create_promocode` (admin)
- [ ] Create promocode
- [ ] Check backend logs: API call to `/api/v1/promocodes` (POST)
- [ ] Use promocode in booking
- [ ] Check backend logs: API call to `/api/v1/promocodes/validate` (POST)

#### 6. Error Handling
- [ ] Stop backend
- [ ] Try to interact with bot
- [ ] Bot shows friendly error message (not crash)
- [ ] Bot logs show connection error
- [ ] Restart backend
- [ ] Bot works again

---

## Performance Tests (Optional)

### Response Time Tests
```bash
# Install apache bench
brew install httpd  # macOS
apt-get install apache2-utils  # Linux

# Test health endpoint
ab -n 1000 -c 10 http://localhost:8000/health
```
- [ ] Average response time < 50ms
- [ ] No failed requests

### Load Tests
```bash
# Test tariffs endpoint (requires API key header - harder to test with ab)
# Use wrk or similar tool

# Or use Python script for API key tests
python -c "
import asyncio
import aiohttp
import time

async def test():
    start = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(100):
            task = session.get(
                'http://localhost:8000/api/v1/pricing/tariffs',
                headers={'X-API-Key': 'dev-api-key-12345'}
            )
            tasks.append(task)
        responses = await asyncio.gather(*tasks)
        end = time.time()
        print(f'100 requests in {end-start:.2f}s')
        print(f'Average: {(end-start)/100*1000:.0f}ms per request')

asyncio.run(test())
"
```
- [ ] Can handle 100 concurrent requests
- [ ] Average response time < 200ms

---

## Production Readiness Checklist

### Security
- [ ] `BACKEND_API_KEY` changed from default
- [ ] API key is strong (32+ random characters)
- [ ] `.env` file not committed to git
- [ ] `.env` file in `.gitignore`
- [ ] No hardcoded secrets in code
- [ ] Admin endpoints require authentication
- [ ] CORS configured for specific origins (not `*`)

### Configuration
- [ ] `DEBUG=false` in production
- [ ] `DATABASE_URL` points to production database
- [ ] Logging configured (Logtail, etc.)
- [ ] Error tracking configured
- [ ] Monitoring configured

### Database
- [ ] Database backed up regularly
- [ ] Migrations tested
- [ ] Database connection pooling configured
- [ ] Database credentials secured

### Infrastructure
- [ ] SSL/TLS configured (if API exposed)
- [ ] Firewall configured
- [ ] Health checks configured
- [ ] Auto-restart configured (Docker restart policy)
- [ ] Log rotation configured
- [ ] Monitoring alerts configured

### Documentation
- [ ] README.md updated
- [ ] API documentation accessible
- [ ] Deployment guide written
- [ ] Rollback procedure documented
- [ ] Incident response plan documented

---

## Sign-Off

### Backend API
- [ ] All automated tests pass
- [ ] All manual API tests pass
- [ ] Error handling works correctly
- [ ] Authentication works correctly
- [ ] Performance is acceptable
- [ ] Documentation is complete

**Backend Status:** ✅ Production Ready

### Integration (After Bot Refactoring)
- [ ] Bot can communicate with backend
- [ ] All bot features work via API
- [ ] No direct database access in bot
- [ ] Error handling works end-to-end
- [ ] Performance is acceptable

**Integration Status:** ⏳ Pending Bot Refactoring

### Production Deployment
- [ ] Security checklist complete
- [ ] Configuration verified
- [ ] Database ready
- [ ] Infrastructure ready
- [ ] Documentation complete
- [ ] Team trained
- [ ] Rollback plan ready

**Production Status:** ⏳ Not Ready Yet

---

**Last Updated:** 2025-01-XX
**Tested By:** [Your Name]
**Environment:** Development / Staging / Production
