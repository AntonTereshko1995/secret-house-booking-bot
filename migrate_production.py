#!/usr/bin/env python3
"""
Скрипт для ручной миграции данных из SQLite в PostgreSQL на продакшене.

ВАЖНО: Запускать только на сервере Amvera!

Использование:
    python migrate_production.py
"""

import sys
import os

# Set AMVERA environment to use production config
os.environ['AMVERA'] = '1'

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from db.migrate_sqlite_to_postgres import migrate_data

# SQLite database path on Amvera server
SQLITE_PATH = "/data/the_secret_house.db"

print("=" * 80)
print("PRODUCTION DATA MIGRATION")
print("=" * 80)

# Import config after setting AMVERA env
from src.config.config import DATABASE_URL

print(f"\nSource: sqlite:///{SQLITE_PATH}")
print(f"Target: {DATABASE_URL}")
print("\n" + "=" * 80)

# Check if SQLite file exists
if not os.path.exists(SQLITE_PATH):
    print(f"\nERROR: SQLite database not found at {SQLITE_PATH}")
    print("Please check the file path!")
    sys.exit(1)

print(f"\n✓ SQLite database found: {SQLITE_PATH}")

file_size = os.path.getsize(SQLITE_PATH) / (1024 * 1024)  # MB
print(f"✓ File size: {file_size:.2f} MB")

print("\nThis will migrate all data from SQLite to PostgreSQL.")
print("=" * 80)

response = input("\nContinue? (type 'yes' to confirm): ")
if response.lower() != 'yes':
    print("Cancelled by user")
    sys.exit(0)

# Construct URLs
sqlite_url = f"sqlite:///{SQLITE_PATH}"
postgres_url = DATABASE_URL

# Run migration
try:
    migrate_data(sqlite_url, postgres_url)
    print("\n" + "=" * 80)
    print("✓ MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)
except Exception as e:
    print("\n" + "=" * 80)
    print(f"✗ MIGRATION FAILED: {e}")
    print("=" * 80)
    sys.exit(1)
