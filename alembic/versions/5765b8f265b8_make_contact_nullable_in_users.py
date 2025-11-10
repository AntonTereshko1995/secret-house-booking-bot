"""make_contact_nullable_in_users

Revision ID: 5765b8f265b8
Revises: 86e9eed4ea92
Create Date: 2025-11-07 09:51:31.508585

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5765b8f265b8"
down_revision: Union[str, None] = "86e9eed4ea92"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make contact field nullable
    # SQLite doesn't support ALTER COLUMN directly, so we need to recreate the table
    # However, for SQLite, we can use a workaround by creating a new table and copying data
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("contact", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    # Make contact field NOT NULL again
    # Note: This will fail if there are any NULL values in contact
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("contact", existing_type=sa.String(), nullable=False)
