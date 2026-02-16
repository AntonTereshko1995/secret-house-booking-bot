#!/usr/bin/env python3
"""
Диагностический скрипт для проверки состояния миграции.
Запускать на сервере Amvera для диагностики проблем с миграцией.

Использование:
    python check_migration_status.py
"""

import sys
import os

# Set AMVERA environment
os.environ['AMVERA'] = '1'

print("=" * 80)
print("MIGRATION STATUS DIAGNOSTIC")
print("=" * 80)

# Step 1: Check environment
print("\n[STEP 1] Checking environment...")
print(f"AMVERA env: {os.environ.get('AMVERA', 'NOT SET')}")

# Step 2: Check DATABASE_URL
print("\n[STEP 2] Checking database configuration...")
try:
    from src.config.config import DATABASE_URL
    print(f"DATABASE_URL: {DATABASE_URL[:50]}...")  # Show first 50 chars

    if DATABASE_URL.startswith("postgresql"):
        print("✓ PostgreSQL database configured")
    else:
        print("✗ Not using PostgreSQL!")
except Exception as e:
    print(f"✗ Error loading config: {e}")
    sys.exit(1)

# Step 3: Check SQLite file
print("\n[STEP 3] Checking SQLite database file...")

sqlite_paths = [
    "/data/the_secret_house.db",
    "./the_secret_house.db",
    "./test_the_secret_house.db",
]

sqlite_found = None
for path in sqlite_paths:
    if os.path.exists(path):
        sqlite_found = path
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"✓ Found SQLite database: {path}")
        print(f"  File size: {size_mb:.2f} MB")
        break

if not sqlite_found:
    print("✗ SQLite database NOT FOUND!")
    print("  Checked paths:")
    for path in sqlite_paths:
        print(f"    - {path}")

# Step 4: Check PostgreSQL connection
print("\n[STEP 4] Checking PostgreSQL connection...")
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"✓ PostgreSQL connected")
        print(f"  Version: {version[:50]}...")

        # Check tables
        print("\n[STEP 5] Checking table counts...")
        tables = ['user', 'booking', 'gift', 'promocode']

        for table in tables:
            result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
            count = result.scalar()
            status = "✗ EMPTY" if count == 0 else "✓"
            print(f"  {table}: {count} records {status}")

except Exception as e:
    print(f"✗ Database connection error: {e}")

# Step 6: Check if migration would run
print("\n[STEP 6] Checking if auto-migration would trigger...")
try:
    from db.run_migrations import is_database_empty, check_sqlite_file_exists

    needs_migration = is_database_empty(engine)
    sqlite_exists, sqlite_path = check_sqlite_file_exists()

    print(f"Booking table empty: {needs_migration}")
    print(f"SQLite file found: {sqlite_exists} ({sqlite_path})")

    if needs_migration and sqlite_exists:
        print("\n✓ AUTO-MIGRATION SHOULD RUN on next bot start")
    elif not needs_migration:
        print("\n✗ Auto-migration won't run: booking table not empty")
    elif not sqlite_exists:
        print("\n✗ Auto-migration won't run: SQLite file not found")
    else:
        print("\n? Unknown state")

except Exception as e:
    print(f"✗ Error checking migration status: {e}")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)

# Step 7: Recommendations
print("\nRECOMMENDATIONS:")

if sqlite_found and needs_migration:
    print("1. Restart the bot - auto-migration should run automatically")
    print("2. Check bot startup logs for [AUTO-MIGRATION] messages")
elif not sqlite_found:
    print("1. Upload the_secret_house.db to /data/ directory on server")
    print("2. Restart the bot")
elif not needs_migration:
    print("1. Database already has data - migration not needed")
    print("2. If data is incorrect, you may need to clear and re-migrate")
