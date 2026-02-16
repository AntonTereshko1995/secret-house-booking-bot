#!/usr/bin/env python3
"""
Migrate missing gift certificates from SQLite to PostgreSQL (production).

Run this on Amvera server:
    python migrate_missing_gifts.py

Note: DATABASE_URL will be read from environment (production config).
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models.gift import GiftBase
from src.config.config import DATABASE_URL

print("=" * 80)
print("MIGRATE MISSING GIFTS TO PRODUCTION")
print("=" * 80)
print()

# Find SQLite database
sqlite_paths = [
    "/data/the_secret_house.db",  # Amvera production
    "./the_secret_house.db",
    "./test_the_secret_house.db",
]

sqlite_path = None
for path in sqlite_paths:
    if os.path.exists(path):
        sqlite_path = path
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"✓ Found SQLite: {path} ({size_mb:.2f} MB)")
        break

if not sqlite_path:
    print("❌ SQLite database not found!")
    print("Checked paths:")
    for path in sqlite_paths:
        print(f"  - {path}")
    sys.exit(1)

print(f"✓ PostgreSQL: {DATABASE_URL[:60]}...")
print()

# Connect to databases
sqlite_url = f"sqlite:///{sqlite_path}"
source_engine = create_engine(sqlite_url)
target_engine = create_engine(DATABASE_URL)

SourceSession = sessionmaker(bind=source_engine)
TargetSession = sessionmaker(bind=target_engine)

source_session = SourceSession()
target_session = TargetSession()

try:
    # Get ALL gifts from SQLite (including those with NULL user_id)
    all_gifts = source_session.query(GiftBase).all()
    print(f"SQLite has {len(all_gifts)} gifts total")

    # Get existing gift codes in PostgreSQL
    existing_codes = set()
    with target_engine.connect() as conn:
        result = conn.execute(text("SELECT code FROM gift"))
        existing_codes = {row[0] for row in result}
        result = conn.execute(text("SELECT COUNT(*) FROM gift"))
        pg_count = result.scalar()
        print(f"PostgreSQL has {pg_count} gifts currently")
    print()

    # Find missing gifts
    missing_gifts = [g for g in all_gifts if g.code not in existing_codes]

    if len(missing_gifts) == 0:
        print("✓ All gifts already migrated!")
        sys.exit(0)

    print(f"Found {len(missing_gifts)} missing gifts:")
    for gift in missing_gifts:
        user_status = "NULL" if gift.user_id is None else f"user_id={gift.user_id}"
        done_status = "DONE" if gift.is_done else "active"
        print(f"  - ID={gift.id}, code={gift.code}, {user_status}, {done_status}, buyer={gift.buyer_contact}")
    print()

    # Ask confirmation
    response = input("Migrate these gifts to PostgreSQL? (yes/no): ")
    if response.lower() not in ["yes", "y"]:
        print("Migration cancelled")
        sys.exit(0)
    print()

    # Convert to dictionaries
    gifts_data = []
    for gift in missing_gifts:
        gift_dict = {
            column.name: getattr(gift, column.name)
            for column in gift.__table__.columns
        }
        gifts_data.append(gift_dict)

    # Insert into PostgreSQL (preserving IDs)
    print(f"Inserting {len(gifts_data)} gifts...")
    target_session.bulk_insert_mappings(GiftBase, gifts_data)
    target_session.commit()
    print("✓ Gifts inserted")

    # Reset sequence
    max_id_result = target_session.execute(text('SELECT MAX(id) FROM "gift"'))
    max_id = max_id_result.scalar() or 0
    target_session.execute(
        text(f'ALTER SEQUENCE "gift_id_seq" RESTART WITH {max_id + 1}')
    )
    target_session.commit()
    print(f"✓ Sequence reset to {max_id + 1}")

    # Verify
    with target_engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM gift"))
        total = result.scalar()
        print(f"✓ PostgreSQL now has {total} gifts total")
    print()
    print("=" * 80)
    print("✓ SUCCESS: Gifts migrated successfully!")
    print("=" * 80)

except Exception as e:
    target_session.rollback()
    print()
    print("=" * 80)
    print(f"❌ ERROR: {e}")
    print("=" * 80)
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    source_session.close()
    target_session.close()
