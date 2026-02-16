# secret-house-booking-bot

### **GitHub Project Description**

# 🏠 Telegram House Booking Bot

A powerful Telegram bot developed to automate the house booking process, streamlining operations and improving customer experience. Built using Python and the `python-telegram-bot` library, this project combines robust booking logic with AI-driven customer support for a seamless user experience.

---

### **Key Features**

- **Automated Booking Workflow**:  
  Streamlines the entire booking process, including:
  - Date selection
  - Booking confirmation
  - Payment processing
  - Change the booking date
  - Cancel booking  
  Automation covers over **80% of operations**, reducing manual effort and increasing efficiency.  

- **AI-Powered Customer Support**:  
  Integrated an OpenAI GPT-based LLM model for real-time client inquiries.  
  - **25% improvement** in response accuracy.  
  - Fast response times for common customer questions.

- **Performance Optimization**:  
  - Reduced booking processing time by **40%**.  
  - Configured logging and monitoring for real-time performance tracking and issue resolution.  

- **Cloud Deployment**:  
  Deployed the bot on **Microsoft Azure** using containerization for scalability and reliability.  

---

### **Tech Stack**

- **Programming Language**: Python 3.10+
- **Database**:
  - SQLite (local development)
  - PostgreSQL 17 (production on Amvera)
- **Libraries**:
  - `python-telegram-bot` for Telegram API integration
  - `sqlalchemy` for ORM and database operations
  - `alembic` for database migrations
  - `psycopg2-binary` for PostgreSQL connectivity
  - `redis` for session state management
  - OpenAI GPT for AI-powered customer interactions
  - Google Calendar API for availability checking
- **Infrastructure**: Amvera cloud platform (containerized deployment)
- **Other Tools**:
  - Logging and monitoring systems for performance tracking
  - Redis for conversation state persistence
  - Docker for containerization

---

### **Installation & Setup**

#### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- PostgreSQL 17+ (for production) or SQLite (for development)

#### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/secret-house-booking-bot.git
   cd secret-house-booking-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   - Copy `.env.debug` to `src/config/.env.debug` (if not already present)
   - Update configuration with your credentials:
     - `TELEGRAM_TOKEN`: Your Telegram bot token
     - `ADMIN_CHAT_ID`: Your admin Telegram chat ID
     - `GPT_KEY`: Your OpenAI API key
     - `GOOGLE_CREDENTIALS`: Base64-encoded Google service account credentials
     - Other settings as needed

4. **Run database migrations**
   ```bash
   set ENV=debug
   python -m alembic upgrade head
   ```

5. **Start the bot**
   ```bash
   python src/main.py
   ```

#### PostgreSQL Setup (Production)

1. **Install PostgreSQL**
   - Windows: Download from [postgresql.org](https://www.postgresql.org/download/)
   - Linux: `sudo apt install postgresql postgresql-contrib`
   - macOS: `brew install postgresql`

2. **Create database**
   ```bash
   psql -U postgres
   CREATE DATABASE test_secret_house;
   \q
   ```

3. **Configure environment**
   - Set `ENV=production`
   - Update `DATABASE_URL` in `.env.production`:
     ```
     DATABASE_URL=postgresql://postgres:password@localhost:5432/test_secret_house
     ```

4. **Run migrations**
   ```bash
   set ENV=production
   python -m alembic upgrade head
   ```

#### Migrating from SQLite to PostgreSQL

**✨ NEW: Automatic Migration!**

The bot now **automatically migrates** data from SQLite to PostgreSQL on first startup!

**Automatic Migration (Recommended):**

1. **Ensure SQLite file exists**
   ```bash
   # Backup first (safety)
   copy test_the_secret_house.db test_the_secret_house.db.backup
   ```

2. **Setup PostgreSQL** (see above)

3. **Start bot with PostgreSQL URL**
   ```bash
   set DATABASE_URL=postgresql://postgres:password@localhost:5432/test_secret_house
   set ENV=production
   python src/main.py
   ```

4. **Migration happens automatically!**
   - Bot detects empty PostgreSQL database
   - Finds SQLite file
   - Migrates all data automatically
   - Logs show progress

**Manual Migration (if needed):**

```bash
python db/migrate_sqlite_to_postgres.py \
    sqlite:///test_the_secret_house.db \
    postgresql://postgres:password@localhost:5432/test_secret_house
```

**Verify migration:**
```bash
psql -U postgres -d test_secret_house -c "SELECT COUNT(*) FROM booking;"
```

For detailed information:
- **Automatic Migration**: See `docs/AUTO_MIGRATION.md`
- **Manual Migration**: See `db/MIGRATION.md`

#### Amvera Deployment

The bot is deployed on Amvera cloud platform with:
- **PostgreSQL 17**: Managed database service
- **Redis**: Session state management
- **Environment Variables**: Set in Amvera dashboard
  - `AMVERA=1`
  - `DATABASE_URL=postgresql://admin:password@amvera-host/the_secret_house`
  - All other configuration from `.env.amvera.example`

See `.env.amvera.example` for complete Amvera configuration template.

---

### **Future Improvements**

- Add multi-language support for international clients.  
- Expand integration with other payment gateways.  
- Enable admin dashboard for booking analytics.

---

### **Contributions**

Feel free to fork the repository, open issues, or submit pull requests! All contributions are welcome. 😊
