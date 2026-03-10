"""Add receipt_file_id to booking

Revision ID: ad18bd626107
Revises: c4d5e6f7a8b9
Create Date: 2026-03-10 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ad18bd626107"
down_revision: Union[str, None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("booking", schema=None) as batch_op:
        batch_op.add_column(sa.Column("receipt_file_id", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("booking", schema=None) as batch_op:
        batch_op.drop_column("receipt_file_id")
