from alembic.config import Config
from alembic import command, script
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine
import os

def run_migrations_if_needed():
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ALEMBIC_INI_PATH = os.path.join(BASE_DIR, "alembic.ini")
    alembic_cfg = Config(ALEMBIC_INI_PATH)
    db_url = alembic_cfg.get_main_option("sqlalchemy.url")
    engine = create_engine(db_url)

    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        current_rev = context.get_current_revision()
        script_dir = script.ScriptDirectory.from_config(alembic_cfg)
        head_rev = script_dir.get_current_head()

        if current_rev != head_rev:
            print(f"🟡 Migrating DB: {current_rev} → {head_rev}")
            command.upgrade(alembic_cfg, "head")
        else:
            print("✅ DB already up to date.")