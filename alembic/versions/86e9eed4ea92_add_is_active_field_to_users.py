"""Add is_active field to users

Revision ID: 86e9eed4ea92
Revises: efdab6cb698f
Create Date: 2025-11-07 09:26:31.095889

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "86e9eed4ea92"
down_revision: Union[str, None] = "efdab6cb698f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_active column with default value 1 (True) if it doesn't exist
    # This migration is idempotent - it won't fail if column already exists
    try:
        op.add_column(
            "user",
            sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        )
    except:
        # Column already exists, migration was already applied manually
        pass


def downgrade() -> None:
    # Remove is_active column
    op.drop_column("user", "is_active")
