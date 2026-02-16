import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from alembic.config import Config
from alembic import command, script
from alembic.runtime.environment import EnvironmentContext
from src.config.config import DATABASE_URL
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os


def is_postgresql_database(database_url: str) -> bool:
    """Check if DATABASE_URL points to PostgreSQL."""
    return database_url.startswith("postgresql://") or database_url.startswith("postgres://")


def is_sqlite_database(database_url: str) -> bool:
    """Check if DATABASE_URL points to SQLite."""
    return database_url.startswith("sqlite:///")


def check_sqlite_file_exists() -> tuple[bool, str]:
    """
    Check if SQLite database file exists.

    Checks multiple locations:
    1. /data/the_secret_house.db (Amvera production)
    2. ./the_secret_house.db (local production)
    3. ./test_the_secret_house.db (local testing)

    Returns:
        (exists, filepath): Tuple of boolean and filepath
    """
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sqlite_paths = [
        "/data/the_secret_house.db",  # Amvera production path
        os.path.join(BASE_DIR, "the_secret_house.db"),
        os.path.join(BASE_DIR, "test_the_secret_house.db"),
        os.path.join(BASE_DIR, "test_the_secret_house.db.backup"),
    ]

    print("[AUTO-MIGRATION] Searching for SQLite database file...")
    for path in sqlite_paths:
        print(f"[AUTO-MIGRATION] Checking: {path}")
        if os.path.exists(path):
            file_size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"[AUTO-MIGRATION] OK Found SQLite database: {path}")
            print(f"[AUTO-MIGRATION] OK File size: {file_size_mb:.2f} MB")
            return True, path
        else:
            print(f"[AUTO-MIGRATION]   - Not found")

    print("[AUTO-MIGRATION] X No SQLite database file found in any location")
    return False, ""


def is_database_empty(engine) -> bool:
    """
    Check if PostgreSQL database needs migration (no records in booking table).

    We check booking table specifically because it's the main data table.
    If booking is empty but users exist, we still need to migrate bookings.

    Args:
        engine: SQLAlchemy engine

    Returns:
        True if database needs migration (booking table empty), False otherwise
    """
    try:
        with engine.connect() as conn:
            # Check if booking table exists
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = 'booking'"
                )
            )
            table_exists = result.scalar() > 0

            if not table_exists:
                return True

            # Check if booking table has records
            # If booking is empty, we need migration even if other tables have data
            result = conn.execute(text('SELECT COUNT(*) FROM "booking"'))
            count = result.scalar()

            if count == 0:
                print("[AUTO-MIGRATION] Booking table is empty - migration needed")
                return True

            print(f"[AUTO-MIGRATION] Booking table has {count} records - skipping migration")
            return False
    except Exception as e:
        print(f"[WARNING] Error checking if database is empty: {e}")
        return False


def auto_migrate_data_if_needed():
    """
    Automatically migrate data from SQLite to PostgreSQL if:
    1. Current database is PostgreSQL
    2. PostgreSQL database is empty
    3. SQLite file exists
    """

    print("[AUTO-MIGRATION] ===== Checking if auto-migration is needed =====")
    print(f"[AUTO-MIGRATION] DATABASE_URL: {DATABASE_URL[:60]}...")

    # Only auto-migrate if using PostgreSQL
    if not is_postgresql_database(DATABASE_URL):
        print("[AUTO-MIGRATION] Not using PostgreSQL - skipping auto-migration")
        return

    print("[AUTO-MIGRATION] OK Detected PostgreSQL database")

    # Check if database needs migration (booking table empty)
    print("[AUTO-MIGRATION] Checking if booking table is empty...")
    engine = create_engine(DATABASE_URL)
    if not is_database_empty(engine):
        print("[AUTO-MIGRATION] Booking table has data - skipping auto-migration")
        return

    print("[AUTO-MIGRATION] OK Booking table is empty - migration needed")
    print("[AUTO-MIGRATION] ===== Starting SQLite file search =====")

    # Check if SQLite file exists
    sqlite_exists, sqlite_path = check_sqlite_file_exists()
    if not sqlite_exists:
        print("[AUTO-MIGRATION] X No SQLite file found, skipping auto-migration")
        return

    print("[AUTO-MIGRATION] ===== All checks passed - starting migration =====")
    print(f"[AUTO-MIGRATION] Source: {sqlite_path}")
    print(f"[AUTO-MIGRATION] Target: {DATABASE_URL[:60]}...")
    print("=" * 80)

    # Import migration function
    try:
        from db.migrate_sqlite_to_postgres import migrate_data

        # Construct SQLite URL
        sqlite_url = f"sqlite:///{sqlite_path}"

        # Run migration
        print(f"[AUTO-MIGRATION] Source: {sqlite_url}")
        print(f"[AUTO-MIGRATION] Target: {DATABASE_URL}")
        print("")

        migrate_data(sqlite_url, DATABASE_URL)

        print("")
        print("=" * 80)
        print("[AUTO-MIGRATION] SUCCESS: Automatic data migration completed successfully!")
        print("=" * 80)

    except Exception as e:
        print("")
        print("=" * 80)
        print(f"[AUTO-MIGRATION] X Error during automatic migration: {e}")
        print("[AUTO-MIGRATION] You can manually run:")
        print(f"  python db/migrate_sqlite_to_postgres.py {sqlite_url} {DATABASE_URL}")
        print("=" * 80)
        raise


def run_migrations_if_needed():
    """
    Run Alembic schema migrations and automatically migrate data if needed.

    This function:
    1. Runs Alembic migrations to create/update schema
    2. Auto-migrates data from SQLite to PostgreSQL on first run
    """
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ALEMBIC_INI_PATH = os.path.join(BASE_DIR, "alembic.ini")
    alembic_cfg = Config(ALEMBIC_INI_PATH)
    engine = create_engine(DATABASE_URL)

    # Step 1: Run Alembic schema migrations
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        current_rev = context.get_current_revision()
        script_dir = script.ScriptDirectory.from_config(alembic_cfg)
        head_rev = script_dir.get_current_head()

        if current_rev != head_rev:
            print(f"[MIGRATION] Migrating DB schema: {current_rev} -> {head_rev}")
            command.upgrade(alembic_cfg, "head")
            print("[MIGRATION] Schema migration completed successfully")
        else:
            print("[INFO] DB schema already up to date.")

    # Step 2: Auto-migrate data from SQLite to PostgreSQL if needed
    try:
        auto_migrate_data_if_needed()
    except Exception as e:
        print(f"[ERROR] Auto-migration failed: {e}")
        print("[ERROR] Bot will continue with empty database.")
        print("[ERROR] Please manually run migration script if needed.")
