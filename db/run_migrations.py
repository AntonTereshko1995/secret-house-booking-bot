import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from alembic.config import Config
from alembic import command, script
from src.config.config import DATABASE_URL
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine


def run_migrations_if_needed():
    """
    Run Alembic schema migrations if needed.

    This function checks if the database schema is up to date and runs
    migrations if necessary.
    """
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ALEMBIC_INI_PATH = os.path.join(BASE_DIR, "alembic.ini")
    alembic_cfg = Config(ALEMBIC_INI_PATH)
    engine = create_engine(DATABASE_URL)

    # Run Alembic schema migrations
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
