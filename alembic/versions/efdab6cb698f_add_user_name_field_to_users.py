"""Add user_name field to users

Revision ID: efdab6cb698f
Revises: ab9a47c0f211
Create Date: 2025-11-05 17:30:07.503797

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "efdab6cb698f"
down_revision: Union[str, None] = "ab9a47c0f211"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_name column as nullable
    op.add_column("user", sa.Column("user_name", sa.String(), nullable=True))

    # Populate user_name from contact for existing users
    op.execute('UPDATE "user" SET user_name = contact')


def downgrade() -> None:
    op.drop_column("user", "user_name")
