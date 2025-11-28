# 🚀 Deployment Checklist

## Pre-Deployment Verification

### ✅ Code Quality
- [x] All 13 handlers refactored to use BackendAPIClient
- [x] No direct database access in telegram_bot handlers
- [x] All syntax checks passed
- [x] Error handling implemented (129 try/except blocks)
- [x] Logging configured in all handlers

### ✅ Architecture
- [x] Telegram Bot separated from Backend API
- [x] REST API with 42 methods implemented
- [x] Database migrations ready (Alembic)
- [x] Redis for session persistence
- [x] Docker Compose configured

### ✅ Documentation
- [x] README.md updated
- [x] QUICK_START.md created
- [x] REFACTORING_SUMMARY.md created
- [x] API documentation available at /docs

---

## Environment Setup

### 1. Backend API Configuration

**File:** `.env.debug` or `.env.production`

```bash
# Required
TELEGRAM_TOKEN=your_bot_token_from_botfather
BACKEND_API_KEY=generate_random_string_32_chars
ADMIN_CHAT_ID=your_telegram_chat_id
DATABASE_URL=sqlite:///./data/the_secret_house.db

# Optional but recommended
GOOGLE_CREDENTIALS=path/to/credentials.json
CALENDAR_ID=your_calendar_id@group.calendar.google.com
GPT_KEY=sk-your-openai-key
BANK_CARD_NUMBER=1234567890123456
BANK_PHONE_NUMBER=+375291234567
ADMINISTRATION_CONTACT=@admin_username
```

**Generate API Key:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Find your Chat ID:**
1. Start your bot
2. Send a message to the bot
3. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
4. Look for `"chat":{"id": 123456789}`

### 2. Redis Setup

**Local:**
```bash
redis-server
```

**Docker:**
Already configured in docker-compose.yml

### 3. Database Setup

**Run migrations:**
```bash
cd /Users/a/secret-house-booking-bot
export ENV=debug
python -m alembic upgrade head
```

---

## Testing Before Deployment

### 1. System Integration Test
```bash
python3 test_system.py
```

**Expected results:**
- ✅ Backend app imports successfully
- ✅ No DatabaseService imports found
- ✅ Statistics: 13 handlers, 9,620+ lines

### 2. Backend API Health Check

**Start Backend:**
```bash
export ENV=debug
python backend/main.py
```

**Test health endpoint:**
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"secret-house-backend","version":"1.0.0"}
```

**Test API docs:**
Open browser: http://localhost:8000/docs

### 3. Telegram Bot Connection Test

**Start Bot:**
```bash
export ENV=debug
python telegram_bot/main.py
```

**Expected output:**
```
✅ Backend API is healthy
📡 Connected to: http://localhost:8000
✅ Redis persistence initialized
✅ Application initialized
📝 Registering handlers...
✅ All handlers registered successfully
🚀 Bot is starting...
```

**Test in Telegram:**
1. Send `/start` to your bot
2. You should see the main menu
3. Try creating a test booking

---

## Deployment Methods

### Method 1: Local Development

**Terminal 1 - Backend:**
```bash
cd /Users/a/secret-house-booking-bot
export ENV=debug
python backend/main.py
```

**Terminal 2 - Bot:**
```bash
cd /Users/a/secret-house-booking-bot
export ENV=debug
python telegram_bot/main.py
```

### Method 2: Docker Compose

**1. Create .env file:**
```bash
cp .env.docker.example .env
# Edit .env with your actual values
```

**2. Start all services:**
```bash
docker-compose up --build
```

**3. View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f telegram_bot
```

**4. Stop services:**
```bash
docker-compose down
```

### Method 3: Production (Azure)

**Prerequisites:**
- Azure account with Container Instances
- Container Registry configured
- Secrets stored in Azure Key Vault or Google Secret Manager

**Build and push images:**
```bash
# Backend
docker build -t your-registry/secret-house-backend:latest -f backend/Dockerfile .
docker push your-registry/secret-house-backend:latest

# Bot
docker build -t your-registry/secret-house-bot:latest -f telegram_bot/Dockerfile .
docker push your-registry/secret-house-bot:latest
```

**Deploy to Azure:**
```bash
# Using Azure CLI
az container create \
  --resource-group secret-house-rg \
  --name secret-house-backend \
  --image your-registry/secret-house-backend:latest \
  --dns-name-label secret-house-api \
  --ports 8000 \
  --environment-variables ENV=production
```

---

## Post-Deployment Verification

### 1. Service Health Checks

**Backend API:**
```bash
curl https://your-domain.com/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "secret-house-backend",
  "version": "1.0.0"
}
```

### 2. Bot Functionality

**Test basic commands:**
- [ ] `/start` - Shows main menu
- [ ] New booking flow - Can select dates
- [ ] `/booking_list` (admin) - Shows bookings
- [ ] Price calculation - Shows correct prices
- [ ] Payment - Generates payment instructions

### 3. Integration Points

- [ ] Google Calendar sync working
- [ ] OpenAI GPT responses working
- [ ] Redis session persistence working
- [ ] Database operations successful

### 4. Error Handling

**Test error scenarios:**
- [ ] Backend offline - Bot shows appropriate error
- [ ] Invalid booking dates - Shows validation error
- [ ] Expired promocode - Shows clear message
- [ ] Network timeout - Graceful degradation

---

## Monitoring Setup

### 1. Health Check Endpoints

**Backend API:**
- `GET /health` - Basic health check
- `GET /` - API information

**Set up monitoring:**
```bash
# Using cron for simple monitoring
*/5 * * * * curl -f http://localhost:8000/health || echo "Backend down!"
```

### 2. Logging

**View logs:**
```bash
# Docker
docker-compose logs -f --tail=100

# Local
tail -f logs/backend.log
tail -f logs/bot.log
```

**Log rotation (production):**
```bash
# Add to /etc/logrotate.d/secret-house
/var/log/secret-house/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

### 3. Metrics (Optional)

**Recommended tools:**
- Prometheus + Grafana
- Azure Application Insights
- DataDog
- New Relic

---

## Rollback Plan

### If deployment fails:

**Docker:**
```bash
# Stop new version
docker-compose down

# Start previous version
git checkout <previous-commit>
docker-compose up -d
```

**Azure:**
```bash
# Redeploy previous image
az container create ... --image your-registry/secret-house-backend:previous-tag
```

### Database rollback:
```bash
# Rollback one migration
python -m alembic downgrade -1

# Rollback to specific version
python -m alembic downgrade <revision>
```

---

## Troubleshooting

### Backend won't start

**Check:**
1. Environment variables set correctly
2. Database accessible
3. Port 8000 not in use: `lsof -i :8000`
4. Dependencies installed: `pip install -r requirements.txt`

**Common issues:**
```bash
# Port already in use
kill $(lsof -t -i:8000)

# Database locked
rm data/the_secret_house.db-wal
rm data/the_secret_house.db-shm
```

### Bot can't connect to Backend

**Check:**
1. Backend is running and healthy
2. `BACKEND_API_URL` is correct
3. `BACKEND_API_KEY` matches between bot and backend
4. Firewall allows connection

**Test connection:**
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/health
```

### Redis connection failed

**Check:**
1. Redis is running: `redis-cli ping`
2. Redis host/port correct in config
3. Redis password (if set)

**Start Redis:**
```bash
# Linux/Mac
redis-server

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### Database migrations failed

**Fix:**
```bash
# Reset to initial state
python -m alembic downgrade base
python -m alembic upgrade head

# Or recreate database
rm data/the_secret_house.db
python -m alembic upgrade head
```

---

## Security Checklist

### Before Production:

- [ ] Change all default passwords/keys
- [ ] Use strong random `BACKEND_API_KEY`
- [ ] Store secrets in Secret Manager (not in code)
- [ ] Enable HTTPS/SSL for Backend API
- [ ] Restrict CORS origins (not `allow_origins=["*"]`)
- [ ] Enable rate limiting on API
- [ ] Regular security updates
- [ ] Backup strategy in place

### Secrets Management:

**Never commit:**
- `.env` files
- API keys
- Telegram bot tokens
- Database passwords
- Credentials.json

**Add to .gitignore:**
```
.env
.env.*
!.env.*.example
credentials.json
*.db
*.db-wal
*.db-shm
```

---

## Backup Strategy

### Database Backup

**Daily backup script:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp data/the_secret_house.db backups/the_secret_house_$DATE.db
find backups/ -name "*.db" -mtime +30 -delete
```

**Restore from backup:**
```bash
cp backups/the_secret_house_20250127_120000.db data/the_secret_house.db
python -m alembic upgrade head
```

### Configuration Backup

```bash
# Backup all configs
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
  .env.production \
  settings/ \
  docker-compose.yml
```

---

## Performance Optimization

### For Production:

**Backend:**
- Use Gunicorn/Uvicorn with multiple workers
- Enable response caching
- Database connection pooling
- CDN for static files (if web UI added)

**Database:**
- Migrate to PostgreSQL for better performance
- Add indexes on frequently queried fields
- Regular VACUUM/ANALYZE

**Redis:**
- Configure persistence (AOF + RDB)
- Set max memory policy
- Monitor memory usage

---

## Success Criteria

### Deployment is successful when:

- ✅ Backend API responds to /health with 200 OK
- ✅ Telegram bot starts without errors
- ✅ Users can create bookings through bot
- ✅ Admin commands work (/booking_list, etc.)
- ✅ Database operations successful
- ✅ Redis sessions persist correctly
- ✅ External integrations work (Calendar, GPT)
- ✅ Error handling works gracefully
- ✅ Logs show no critical errors
- ✅ Response times < 2 seconds

---

## Contact & Support

**Documentation:**
- [QUICK_START.md](QUICK_START.md) - Setup guide
- [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) - Architecture details
- API Docs: http://localhost:8000/docs

**For issues:**
1. Check logs first
2. Review troubleshooting section
3. Check GitHub issues
4. Contact development team

---

**Last Updated:** 2025-11-27
**Version:** 1.0.0 (Microservices Architecture)
