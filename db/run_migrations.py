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

    Returns:
        (exists, filepath): Tuple of boolean and filepath
    """
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sqlite_paths = [
        os.path.join(BASE_DIR, "test_the_secret_house.db"),
        os.path.join(BASE_DIR, "test_the_secret_house.db.backup"),
    ]

    for path in sqlite_paths:
        if os.path.exists(path):
            return True, path

    return False, ""


def is_database_empty(engine) -> bool:
    """
    Check if PostgreSQL database is empty (no records in user table).

    Args:
        engine: SQLAlchemy engine

    Returns:
        True if database is empty or user table doesn't exist, False otherwise
    """
    try:
        with engine.connect() as conn:
            # Check if user table exists
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = 'user'"
                )
            )
            table_exists = result.scalar() > 0

            if not table_exists:
                return True

            # Check if user table has records
            result = conn.execute(text('SELECT COUNT(*) FROM "user"'))
            count = result.scalar()
            return count == 0
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

    # Only auto-migrate if using PostgreSQL
    if not is_postgresql_database(DATABASE_URL):
        return

    print("[AUTO-MIGRATION] Detected PostgreSQL database")

    # Check if database is empty
    engine = create_engine(DATABASE_URL)
    if not is_database_empty(engine):
        print("[AUTO-MIGRATION] PostgreSQL database has data, skipping auto-migration")
        return

    print("[AUTO-MIGRATION] PostgreSQL database is empty")

    # Check if SQLite file exists
    sqlite_exists, sqlite_path = check_sqlite_file_exists()
    if not sqlite_exists:
        print("[AUTO-MIGRATION] No SQLite file found, skipping auto-migration")
        return

    print(f"[AUTO-MIGRATION] Found SQLite file: {sqlite_path}")
    print("[AUTO-MIGRATION] Starting automatic data migration...")
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
        print("[AUTO-MIGRATION] ✓ Automatic data migration completed successfully!")
        print("=" * 80)

    except Exception as e:
        print("")
        print("=" * 80)
        print(f"[AUTO-MIGRATION] ✗ Error during automatic migration: {e}")
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
            print("[MIGRATION] ✓ Schema migration completed")
        else:
            print("[INFO] DB schema already up to date.")

    # Step 2: Auto-migrate data from SQLite to PostgreSQL if needed
    try:
        auto_migrate_data_if_needed()
    except Exception as e:
        print(f"[ERROR] Auto-migration failed: {e}")
        print("[ERROR] Bot will continue with empty database.")
        print("[ERROR] Please manually run migration script if needed.")
