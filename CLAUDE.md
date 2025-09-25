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
```

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
- Models: UserBase, BookingBase, GiftBase, SubscriptionBase
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
- Subscription management
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