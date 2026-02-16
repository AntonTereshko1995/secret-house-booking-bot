import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from alembic.config import Config
from alembic import command, script
from src.config.config import DATABASE_URL
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def auto_migrate_gifts_if_needed(engine):
    """
    Automatically migrate gift certificates from SQLite to PostgreSQL if needed.

    This handles gifts with NULL user_id (unactivated certificates) that were
    skipped during initial migration.
    """
    # Check if using PostgreSQL
    if not DATABASE_URL.startswith("postgresql"):
        return

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
            break

    if not sqlite_path:
        return  # No SQLite database found

    try:
        # Check gift count in PostgreSQL
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM gift"))
            pg_gift_count = result.scalar()

        # Check gift count in SQLite
        sqlite_url = f"sqlite:///{sqlite_path}"
        sqlite_engine = create_engine(sqlite_url)
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM gift"))
            sqlite_gift_count = result.scalar()

        # If PostgreSQL has fewer gifts, migrate missing ones
        if pg_gift_count < sqlite_gift_count:
            print(f"[AUTO-MIGRATION] Found {sqlite_gift_count} gifts in SQLite, {pg_gift_count} in PostgreSQL")
            print(f"[AUTO-MIGRATION] Migrating {sqlite_gift_count - pg_gift_count} missing gifts...")

            # Import models
            from db.models.gift import GiftBase

            # Get existing gift codes in PostgreSQL
            with engine.connect() as conn:
                result = conn.execute(text("SELECT code FROM gift"))
                existing_codes = {row[0] for row in result}

            # Get all gifts from SQLite
            SourceSession = sessionmaker(bind=sqlite_engine)
            source_session = SourceSession()

            all_sqlite_gifts = source_session.query(GiftBase).all()
            missing_gifts = [g for g in all_sqlite_gifts if g.code not in existing_codes]

            if missing_gifts:
                print(f"[AUTO-MIGRATION] Migrating {len(missing_gifts)} gifts...")

                # Convert to dictionaries
                gifts_data = []
                for gift in missing_gifts:
                    gift_dict = {
                        column.name: getattr(gift, column.name)
                        for column in gift.__table__.columns
                    }
                    gifts_data.append(gift_dict)

                # Insert into PostgreSQL
                TargetSession = sessionmaker(bind=engine)
                target_session = TargetSession()

                try:
                    target_session.bulk_insert_mappings(GiftBase, gifts_data)
                    target_session.commit()

                    # Reset sequence
                    max_id_result = target_session.execute(text('SELECT MAX(id) FROM "gift"'))
                    max_id = max_id_result.scalar() or 0
                    target_session.execute(
                        text(f'ALTER SEQUENCE "gift_id_seq" RESTART WITH {max_id + 1}')
                    )
                    target_session.commit()

                    print(f"[AUTO-MIGRATION] ✓ Successfully migrated {len(missing_gifts)} gifts!")

                except Exception as e:
                    target_session.rollback()
                    print(f"[AUTO-MIGRATION] ✗ Error migrating gifts: {e}")
                finally:
                    target_session.close()

            source_session.close()
        else:
            print(f"[AUTO-MIGRATION] Gift table is up to date ({pg_gift_count} gifts)")

    except Exception as e:
        print(f"[AUTO-MIGRATION] Error checking gifts: {e}")


def run_migrations_if_needed():
    """
    Run Alembic schema migrations and auto-migrate data if needed.

    This function:
    1. Runs Alembic schema migrations
    2. Auto-migrates missing gift certificates from SQLite (if needed)
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

    # Step 2: Auto-migrate gifts if needed
    try:
        auto_migrate_gifts_if_needed(engine)
    except Exception as e:
        print(f"[AUTO-MIGRATION] Error during gift auto-migration: {e}")
