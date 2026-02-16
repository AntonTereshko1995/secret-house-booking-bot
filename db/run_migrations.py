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


def auto_migrate_bookings_if_needed(engine):
    """
    Automatically migrate missing bookings from SQLite to PostgreSQL if needed.

    This handles bookings that may have been skipped or added after initial migration.
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
        # Check booking count in PostgreSQL
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM booking"))
            pg_booking_count = result.scalar()

        # Check booking count in SQLite
        sqlite_url = f"sqlite:///{sqlite_path}"
        sqlite_engine = create_engine(sqlite_url)
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM booking"))
            sqlite_booking_count = result.scalar()

        # If PostgreSQL has fewer bookings, migrate missing ones
        if pg_booking_count < sqlite_booking_count:
            print(f"[AUTO-MIGRATION] Found {sqlite_booking_count} bookings in SQLite, {pg_booking_count} in PostgreSQL")
            print(f"[AUTO-MIGRATION] Migrating {sqlite_booking_count - pg_booking_count} missing bookings...")

            # Import models
            from db.models.booking import BookingBase
            from db.models.user import UserBase
            from db.models.gift import GiftBase
            from db.models.promocode import PromocodeBase

            # Get existing booking IDs in PostgreSQL
            with engine.connect() as conn:
                result = conn.execute(text("SELECT id FROM booking"))
                existing_ids = {row[0] for row in result}

            # Get valid IDs for foreign keys
            SourceSession = sessionmaker(bind=sqlite_engine)
            source_session = SourceSession()

            # Get valid user IDs (must exist in both SQLite and will be in PostgreSQL)
            valid_user_ids = [user.id for user in source_session.query(UserBase.id).all()]

            # Get valid gift IDs (only those with valid user_id)
            valid_gift_ids = [
                gift.id for gift in source_session.query(GiftBase.id)
                .filter(GiftBase.user_id.in_(valid_user_ids) | GiftBase.user_id.is_(None)).all()
            ]

            # Get all valid promocode IDs
            valid_promocode_ids = [promo.id for promo in source_session.query(PromocodeBase.id).all()]

            # Get ALL bookings from SQLite (including those with invalid user_id)
            all_bookings = source_session.query(BookingBase).all()

            # Filter to only missing bookings (not yet in PostgreSQL)
            missing_all = [b for b in all_bookings if b.id not in existing_ids]

            # Separate valid and invalid bookings
            invalid_user_bookings = []
            valid_bookings = []

            for booking in missing_all:
                if booking.user_id is None or booking.user_id not in valid_user_ids:
                    invalid_user_bookings.append(booking)
                else:
                    valid_bookings.append(booking)

            # Log invalid bookings
            if invalid_user_bookings:
                print(f"[AUTO-MIGRATION] ⚠️  Skipping {len(invalid_user_bookings)} bookings with invalid/NULL user_id:")
                for b in invalid_user_bookings[:5]:  # Show first 5
                    user_status = "NULL" if b.user_id is None else f"invalid user_id={b.user_id}"
                    print(f"  - Booking ID={b.id}, {user_status}, date={b.start_date.date()}")
                if len(invalid_user_bookings) > 5:
                    print(f"  ... and {len(invalid_user_bookings) - 5} more")

            missing_bookings = valid_bookings

            if missing_bookings:
                print(f"[AUTO-MIGRATION] Migrating {len(missing_bookings)} bookings...")

                # Convert to dictionaries and clean invalid FKs
                bookings_data = []
                cleaned_gift_ids = 0
                cleaned_promocode_ids = 0

                for booking in missing_bookings:
                    booking_dict = {
                        column.name: getattr(booking, column.name)
                        for column in booking.__table__.columns
                    }

                    # Clean invalid gift_id
                    if booking_dict.get('gift_id') is not None:
                        if booking_dict['gift_id'] not in valid_gift_ids:
                            booking_dict['gift_id'] = None
                            cleaned_gift_ids += 1

                    # Clean invalid promocode_id
                    if booking_dict.get('promocode_id') is not None:
                        if booking_dict['promocode_id'] not in valid_promocode_ids:
                            booking_dict['promocode_id'] = None
                            cleaned_promocode_ids += 1

                    bookings_data.append(booking_dict)

                if cleaned_gift_ids > 0 or cleaned_promocode_ids > 0:
                    print(f"[AUTO-MIGRATION] Cleaned {cleaned_gift_ids} invalid gift_id, {cleaned_promocode_ids} invalid promocode_id")

                # Insert into PostgreSQL
                TargetSession = sessionmaker(bind=engine)
                target_session = TargetSession()

                try:
                    target_session.bulk_insert_mappings(BookingBase, bookings_data)
                    target_session.commit()

                    # Reset sequence
                    max_id_result = target_session.execute(text('SELECT MAX(id) FROM "booking"'))
                    max_id = max_id_result.scalar() or 0
                    target_session.execute(
                        text(f'ALTER SEQUENCE "booking_id_seq" RESTART WITH {max_id + 1}')
                    )
                    target_session.commit()

                    print(f"[AUTO-MIGRATION] ✓ Successfully migrated {len(missing_bookings)} bookings!")

                except Exception as e:
                    target_session.rollback()
                    print(f"[AUTO-MIGRATION] ✗ Error migrating bookings: {e}")
                finally:
                    target_session.close()

            source_session.close()
        else:
            print(f"[AUTO-MIGRATION] Booking table is up to date ({pg_booking_count} bookings)")

    except Exception as e:
        print(f"[AUTO-MIGRATION] Error checking bookings: {e}")


def run_migrations_if_needed():
    """
    Run Alembic schema migrations and auto-migrate data if needed.

    This function:
    1. Runs Alembic schema migrations
    2. Auto-migrates missing gift certificates from SQLite (if needed)
    3. Auto-migrates missing bookings from SQLite (if needed)
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

    # Step 3: Auto-migrate bookings if needed
    try:
        auto_migrate_bookings_if_needed(engine)
    except Exception as e:
        print(f"[AUTO-MIGRATION] Error during booking auto-migration: {e}")
