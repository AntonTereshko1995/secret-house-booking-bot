"""add_incognito_questionnaire_fields

Revision ID: 16c4e4787de0
Revises: 7a348eb5fbe1
Create Date: 2025-10-15 19:47:56.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "16c4e4787de0"
down_revision: Union[str, None] = "7a348eb5fbe1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add wine_preference and transfer_address columns to booking table."""
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("booking", schema=None) as batch_op:
        batch_op.add_column(sa.Column("wine_preference", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("transfer_address", sa.String(), nullable=True))


def downgrade() -> None:
    """Remove wine_preference and transfer_address columns from booking table."""
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("booking", schema=None) as batch_op:
        batch_op.drop_column("transfer_address")
        batch_op.drop_column("wine_preference")
