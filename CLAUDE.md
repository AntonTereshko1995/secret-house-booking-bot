# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram booking bot for a house rental service built with Python and the python-telegram-bot library. The bot automates the booking workflow, handles payments, integrates with Google Calendar, and includes AI-powered customer support via OpenAI GPT.

## Development Commands

### Running the Application
```bash
python src/main.py
```

### Database Management
```bash
# Run database migrations
python -m alembic upgrade head

# Create new migration
python -m alembic revision --autogenerate -m "description"
```

### Dependencies
```bash
# Install dependencies
pip install -r requirements.txt
```

### Environment Setup
Set environment variable to choose configuration:
```bash
# For debug mode
export ENV=debug

# For production mode
export ENV=production

# For cloud deployment with Google Secret Manager
export secrets-production=1

# For Amvera deployment (sets environment variables directly)
export AMVERA=1
```

### Database Configuration

The bot supports both SQLite (development) and PostgreSQL (production):

#### SQLite (Local Development)
```bash
# Used for local development and testing
# .env.debug configuration:
DATABASE_URL="sqlite:///test_the_secret_house.db"
```

#### PostgreSQL (Production / Amvera)
```bash
# Local PostgreSQL testing:
# .env.production configuration:
DATABASE_URL="postgresql://localhost:5432/test_secret_house"

# Amvera PostgreSQL (set as environment variable):
DATABASE_URL="postgresql://admin:ganja1488@amvera-the-secret-house-cnpg-tsh-prod-db-rw/the_secret_house"
```

#### Environment Detection
The configuration automatically detects the environment:
- **AMVERA=1**: Amvera deployment mode (uses env vars directly, no .env file)
- **ENV=debug**: Uses `.env.debug` (SQLite)
- **ENV=production**: Uses `.env.production` (PostgreSQL)
- **secrets-production**: Uses Google Secret Manager (not used on Amvera)

#### Database Migration

**AUTOMATIC MIGRATION**: The bot automatically migrates data from SQLite to PostgreSQL on first startup if:
- DATABASE_URL points to PostgreSQL
- PostgreSQL database is empty
- SQLite file exists (test_the_secret_house.db)

Simply set DATABASE_URL to PostgreSQL and start the bot - migration happens automatically!

```bash
# Automatic migration (recommended):
# 1. Set DATABASE_URL to PostgreSQL
set DATABASE_URL=postgresql://admin:ganja1488@amvera-host/the_secret_house

# 2. Start bot - migration runs automatically
python src/main.py

# Logs will show:
# [AUTO-MIGRATION] Detected PostgreSQL database
# [AUTO-MIGRATION] PostgreSQL database is empty
# [AUTO-MIGRATION] Found SQLite file: test_the_secret_house.db
# [AUTO-MIGRATION] Starting automatic data migration...
# [AUTO-MIGRATION] ✓ Migration completed successfully!
```

**Manual migration** (if automatic fails or for testing):

```bash
python db/migrate_sqlite_to_postgres.py \
    sqlite:///test_the_secret_house.db \
    postgresql://localhost:5432/test_secret_house
```

See `docs/AUTO_MIGRATION.md` for detailed automatic migration guide.
See `db/MIGRATION.md` for manual migration guide.

#### Troubleshooting

**Connection Issues:**
- Ensure PostgreSQL is running: `psql -U postgres -c "SELECT version();"`
- Check database exists: `psql -U postgres -l`
- Verify connection string format: `postgresql://user:password@host:port/database`
- For Amvera, ensure AMVERA=1 is set

**Migration Issues:**
- Run Alembic migrations first: `python -m alembic upgrade head`
- Check table count: `psql -d database_name -c "\\dt"`
- Verify sequences after migration: Check max IDs in tables
- Backup SQLite before migration: `copy test_the_secret_house.db backup.db`

**Boolean Field Compatibility:**
- SQLite uses Integer (0/1) for booleans
- PostgreSQL has native Boolean type
- SQLAlchemy handles conversion automatically
- Current models use `Integer` for backward compatibility

### Docker Deployment
```bash
# Build and run with Docker
docker build -t secret-house-bot .
docker run -p 8080:8080 secret-house-bot
```

## Architecture

### Core Structure
- **`src/main.py`**: Application entry point, sets up Telegram bot handlers and job scheduler
- **`src/config/config.py`**: Configuration management with environment-based secrets (production uses Google Secret Manager)
- **`src/handlers/`**: Telegram bot conversation handlers for different workflows
- **`src/services/`**: Business logic services (database, calendar, rate calculation, etc.)
- **`src/models/`**: Data models and enums
- **`db/`**: Database models and migration utilities
- **`alembic/`**: Database migration files

### Key Components

**Database Layer:**
- Uses SQLAlchemy ORM with SQLite database
- Models: UserBase, BookingBase, GiftBase
- Singleton DatabaseService pattern for connection management

**Telegram Bot:**
- Handler-based architecture using python-telegram-bot ConversationHandler
- State management through Redis for booking workflows
- Admin commands and user commands with different permissions

**External Integrations:**
- Google Calendar API for availability checking
- Google Secret Manager for production secrets
- OpenAI GPT for customer service responses
- Redis for session state management

**Business Logic:**
- Multi-step booking workflow with tariff calculation
- Gift certificate system
- Automatic booking reminders via job scheduler

### Configuration Environments
- **Debug**: Uses `.env.debug` file
- **Production**: Uses `.env.production` file
- **Cloud Production**: Uses Google Secret Manager with "secrets-production" environment variable

### State Management
The bot uses a complex state machine for booking workflows managed through:
- `src/models/enum/booking_step.py` - Defines workflow states
- `src/services/redis_service.py` - Manages session state persistence
- Handler pattern with callback query routing

### Rate Calculation
Sophisticated pricing system in `src/services/calculation_rate_service.py` that considers:
- Base tariffs (loaded from JSON config files)
- Seasonal/sale pricing modifications
- Add-on services (sauna, photoshoot, etc.)
- Booking duration and guest count

## Important Notes

### Security Considerations
- **Environment files contain sensitive data**: The `.env.debug` and `.env.production` files contain real API keys, tokens, and credentials
- **Never commit environment files**: These files should be git-ignored and handled securely
- **Production uses Google Secret Manager**: In cloud deployments, secrets are managed through Google Cloud Secret Manager

### Database
- **Development**: Uses SQLite database (`test_the_secret_house.db` for debug)
- **Migrations**: Managed through Alembic, run automatically on startup via `run_migrations.py`
- **No formal testing framework**: The codebase doesn't include unit tests or testing infrastructure

### Bot Commands Structure
- **User commands**: `/start` - opens main menu
- **Admin commands**: `/booking_list`, `/change_password` - require admin chat ID permission
- **Handler routing**: Uses callback query patterns with specific prefixes (e.g., `BOOKING-TARIFF_`, `BOOKING-PHOTO_`)