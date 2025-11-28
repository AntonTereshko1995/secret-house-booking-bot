import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.db.database import engine
from db import database
from sqlalchemy.orm import sessionmaker


class BaseDatabaseService:
    """Base database service with session management."""

    def __init__(self):
        self.engine = engine
        self.Session = sessionmaker(bind=self.engine)
        database.create_db_and_tables()

    def get_session(self):
        """Get a new database session."""
        return self.Session()
