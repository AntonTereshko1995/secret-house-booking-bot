"""Reset PostgreSQL sequences for all tables

Revision ID: a1b2c3d4e5f6
Revises: f8a2b3c4d5e6
Create Date: 2026-02-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f8a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables and their quoted names for pg_get_serial_sequence.
# Reserved words (like "user") must be double-quoted inside the SQL string.
_TABLES = [
    ('"user"', "user"),
    ("booking", "booking"),
    ("gift", "gift"),
    ("promocode", "promocode"),
]


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for pg_name, py_name in _TABLES:
        bind.execute(
            sa.text(
                f"SELECT setval("
                f"  pg_get_serial_sequence('{pg_name}', 'id'),"
                f"  COALESCE((SELECT MAX(id) FROM \"{py_name}\"), 1)"
                f");"
            )
        )


def downgrade() -> None:
    # Sequences cannot be meaningfully rolled back.
    pass
