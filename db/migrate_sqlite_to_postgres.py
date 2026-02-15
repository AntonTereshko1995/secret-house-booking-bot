"""
SQLite to PostgreSQL Data Migration Script

This script migrates data from SQLite database to PostgreSQL database while:
- Preserving all primary key IDs to maintain referential integrity
- Respecting foreign key constraints (migrate in correct order)
- Validating record counts after migration
- Resetting PostgreSQL sequences for future inserts
- Using transactions for safety

Usage:
    python db/migrate_sqlite_to_postgres.py <source_url> <target_url>

Example:
    python db/migrate_sqlite_to_postgres.py \\
        sqlite:///test_the_secret_house.db \\
        postgresql://postgres:password@localhost/test_secret_house

    python db/migrate_sqlite_to_postgres.py \\
        sqlite:///test_the_secret_house.db \\
        postgresql://admin:ganja1488@amvera-the-secret-house-cnpg-tsh-prod-db-rw/the_secret_house
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger

# Import models
from db.models.user import UserBase
from db.models.gift import GiftBase
from db.models.booking import BookingBase
from db.models.promocode import PromocodeBase


def migrate_data(source_url: str, target_url: str):
    """
    Migrate data from SQLite to PostgreSQL.

    Args:
        source_url: SQLite database URL (e.g., sqlite:///test_the_secret_house.db)
        target_url: PostgreSQL database URL (e.g., postgresql://user:pass@host/db)
    """

    logger.info("=" * 80)
    logger.info("Starting SQLite to PostgreSQL Migration")
    logger.info("=" * 80)

    # STEP 1: Create connections
    logger.info(f"Connecting to source: {source_url}")
    try:
        source_engine = create_engine(source_url)
        SourceSession = sessionmaker(bind=source_engine)
        logger.success("Source connection established")
    except Exception as e:
        logger.error(f"Failed to connect to source database: {e}")
        sys.exit(1)

    logger.info(f"Connecting to target: {target_url}")
    try:
        target_engine = create_engine(target_url)
        TargetSession = sessionmaker(bind=target_engine)
        logger.success("Target connection established")
    except Exception as e:
        logger.error(f"Failed to connect to target database: {e}")
        sys.exit(1)

    # STEP 2: Verify target database is ready (has tables from Alembic migrations)
    logger.info("Verifying target database has been initialized with Alembic...")
    with target_engine.connect() as conn:
        try:
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
            )
            table_count = result.scalar()
            if table_count == 0:
                logger.error(
                    "Target database has no tables. "
                    "Run 'alembic upgrade head' first to create schema!"
                )
                sys.exit(1)
            logger.success(f"Target database has {table_count} tables")

            # Check for required tables
            required_tables = ["user", "gift", "booking", "promocode"]
            for table_name in required_tables:
                result = conn.execute(
                    text(
                        f"SELECT COUNT(*) FROM information_schema.tables "
                        f"WHERE table_schema = 'public' AND table_name = '{table_name}'"
                    )
                )
                if result.scalar() == 0:
                    logger.error(
                        f"Required table '{table_name}' not found. "
                        f"Run Alembic migrations first!"
                    )
                    sys.exit(1)
            logger.success("All required tables exist")

        except Exception as e:
            logger.error(f"Failed to verify target database: {e}")
            sys.exit(1)

    # STEP 3: Migrate users (no foreign keys - must be first)
    logger.info("")
    logger.info("-" * 80)
    logger.info("Migrating users...")
    logger.info("-" * 80)
    migrate_table(
        source_session=SourceSession(),
        target_session=TargetSession(),
        model_class=UserBase,
        table_name="user",
    )

    # STEP 4: Migrate gifts (FK to user)
    logger.info("")
    logger.info("-" * 80)
    logger.info("Migrating gifts...")
    logger.info("-" * 80)
    migrate_table(
        source_session=SourceSession(),
        target_session=TargetSession(),
        model_class=GiftBase,
        table_name="gift",
    )

    # STEP 5: Migrate promocodes (no foreign keys)
    logger.info("")
    logger.info("-" * 80)
    logger.info("Migrating promocodes...")
    logger.info("-" * 80)
    migrate_table(
        source_session=SourceSession(),
        target_session=TargetSession(),
        model_class=PromocodeBase,
        table_name="promocode",
    )

    # STEP 6: Migrate bookings (FK to user, gift, promocode - must be last)
    logger.info("")
    logger.info("-" * 80)
    logger.info("Migrating bookings...")
    logger.info("-" * 80)
    migrate_table(
        source_session=SourceSession(),
        target_session=TargetSession(),
        model_class=BookingBase,
        table_name="booking",
    )

    logger.info("")
    logger.info("=" * 80)
    logger.success("Migration completed successfully!")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Verify data in PostgreSQL database")
    logger.info("2. Test bot with PostgreSQL (set DATABASE_URL)")
    logger.info("3. Create CRUD operations to ensure everything works")
    logger.info("4. Keep SQLite backup until PostgreSQL is proven stable")


def migrate_table(source_session, target_session, model_class, table_name: str):
    """
    Migrate a single table from source to target.

    CRITICAL: Preserves primary key IDs to maintain referential integrity.

    Args:
        source_session: SQLAlchemy session for source database
        target_session: SQLAlchemy session for target database
        model_class: SQLAlchemy model class
        table_name: Name of the table being migrated
    """

    try:
        # Read all records from source
        source_records = source_session.query(model_class).all()
        record_count = len(source_records)
        logger.info(f"Found {record_count} records in {table_name}")

        if record_count == 0:
            logger.warning(f"No records to migrate in {table_name}")
            source_session.close()
            target_session.close()
            return

        # Convert to dictionaries (to avoid session binding issues)
        logger.info(f"Converting {record_count} records to dictionaries...")
        records_data = []
        for record in source_records:
            # Get all column values as dict
            record_dict = {
                column.name: getattr(record, column.name)
                for column in record.__table__.columns
            }
            records_data.append(record_dict)

        logger.success(f"Converted {len(records_data)} records")

        # Insert into target database
        logger.info(f"Inserting {len(records_data)} records into target...")

        # CRITICAL: Use bulk_insert_mappings to preserve IDs
        # This bypasses autoincrement and uses explicit IDs from source
        target_session.bulk_insert_mappings(model_class, records_data)
        target_session.commit()
        logger.success(f"Inserted {len(records_data)} records")

        # Verify count
        target_count = target_session.query(model_class).count()
        if target_count != record_count:
            raise ValueError(
                f"Count mismatch! Source: {record_count}, Target: {target_count}"
            )

        logger.success(f"Verified: {target_count} records in target match source")

        # CRITICAL: Reset PostgreSQL sequence for autoincrement
        # This ensures future inserts use correct IDs
        logger.info("Resetting sequence for future inserts...")
        max_id_result = target_session.execute(text(f"SELECT MAX(id) FROM {table_name}"))
        max_id = max_id_result.scalar() or 0

        target_session.execute(
            text(f"ALTER SEQUENCE {table_name}_id_seq RESTART WITH {max_id + 1}")
        )
        target_session.commit()
        logger.success(f"Sequence reset to {max_id + 1}")

        logger.success(f"✓ Successfully migrated {record_count} records from {table_name}")

    except Exception as e:
        target_session.rollback()
        logger.error(f"✗ Error migrating {table_name}: {e}")
        logger.error("Transaction rolled back")
        raise

    finally:
        source_session.close()
        target_session.close()


def main():
    """Main entry point for the migration script."""

    # Parse command line arguments
    if len(sys.argv) < 2:
        logger.error("Usage: python db/migrate_sqlite_to_postgres.py <source_url> [target_url]")
        logger.error("")
        logger.error("Examples:")
        logger.error(
            "  python db/migrate_sqlite_to_postgres.py sqlite:///test_the_secret_house.db "
            "postgresql://postgres:password@localhost/test_secret_house"
        )
        logger.error(
            "  python db/migrate_sqlite_to_postgres.py sqlite:///test_the_secret_house.db "
            "postgresql://admin:ganja1488@amvera-the-secret-house-cnpg-tsh-prod-db-rw/the_secret_house"
        )
        logger.error("")
        logger.error("Note: You can also set target URL via POSTGRES_URL environment variable")
        sys.exit(1)

    source_url = sys.argv[1]

    # Get target URL from command line or environment variable
    if len(sys.argv) > 2:
        target_url = sys.argv[2]
    else:
        target_url = os.getenv("POSTGRES_URL")
        if not target_url:
            logger.error(
                "Target URL required. Provide as second argument or set POSTGRES_URL env var"
            )
            sys.exit(1)

    # Confirm migration
    logger.warning("")
    logger.warning("MIGRATION CONFIRMATION")
    logger.warning(f"Source: {source_url}")
    logger.warning(f"Target: {target_url}")
    logger.warning("")
    logger.warning("This will:")
    logger.warning("  1. Read all data from source SQLite database")
    logger.warning("  2. Insert data into target PostgreSQL database")
    logger.warning("  3. Preserve all IDs for referential integrity")
    logger.warning("")
    logger.warning("Make sure you have:")
    logger.warning("  - Backed up your SQLite database")
    logger.warning("  - Run 'alembic upgrade head' on target PostgreSQL")
    logger.warning("  - Verified target PostgreSQL connection")
    logger.warning("")

    response = input("Continue with migration? (yes/no): ")
    if response.lower() not in ["yes", "y"]:
        logger.info("Migration cancelled by user")
        sys.exit(0)

    # Run migration
    try:
        migrate_data(source_url, target_url)
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
