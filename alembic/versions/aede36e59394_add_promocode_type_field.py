"""add promocode_type field

Revision ID: aede36e59394
Revises: e351ee0a0cb0
Create Date: 2025-11-26 13:49:12.763771

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aede36e59394'
down_revision: Union[str, None] = 'e351ee0a0cb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add promocode_type column with default value 1 (BOOKING_DATES)
    op.add_column('promocode', sa.Column('promocode_type', sa.Integer(), nullable=False, server_default='1'))


def downgrade() -> None:
    # Remove promocode_type column
    op.drop_column('promocode', 'promocode_type')
