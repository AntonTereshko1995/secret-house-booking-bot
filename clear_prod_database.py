#!/usr/bin/env python3
"""
Скрипт для очистки продакшен PostgreSQL базы данных перед миграцией.

ВАЖНО: Запускать только на сервере Amvera!

Использование:
    python clear_prod_database.py
"""

import sys
import os

# Set AMVERA environment to use production config
os.environ['AMVERA'] = '1'

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from sqlalchemy import create_engine, text
from src.config.config import DATABASE_URL

print("=" * 80)
print("CLEARING PRODUCTION POSTGRESQL DATABASE")
print("=" * 80)
print(f"\nDatabase: {DATABASE_URL}")
print("\nWARNING: This will delete ALL data from production database!")
print("=" * 80)

response = input("\nContinue? (type 'yes' to confirm): ")
if response.lower() != 'yes':
    print("Cancelled by user")
    sys.exit(0)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("\n[STEP 1] Clearing tables...")

    # Delete in correct order (bookings first due to foreign keys)
    tables = ['booking', 'gift', 'promocode', 'user']

    for table in tables:
        print(f"  - Clearing {table}...")
        conn.execute(text(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE'))
        conn.commit()
        print(f"    ✓ Cleared {table}")

    print("\n[STEP 2] Verifying...")

    for table in ['user', 'booking', 'gift', 'promocode']:
        result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
        count = result.scalar()
        print(f"  {table}: {count} records")

print("\n" + "=" * 80)
print("SUCCESS: Database cleared!")
print("=" * 80)
print("\nNext steps:")
print("1. Check that SQLite database exists: ls -la /data/the_secret_house.db")
print("2. Restart the bot - automatic migration will run")
print("3. Check logs for: [AUTO-MIGRATION] Starting automatic data migration...")
print("=" * 80)
