"""Add source to booking

Revision ID: b1c2d3e4f5a6
Revises: ad18bd626107
Create Date: 2026-04-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "ad18bd626107"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("booking", schema=None) as batch_op:
        batch_op.add_column(sa.Column("source", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("booking", schema=None) as batch_op:
        batch_op.drop_column("source")
