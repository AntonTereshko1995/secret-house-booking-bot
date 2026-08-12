"""Add has_bath_tub to booking and gift tables

Revision ID: f1e2d3c4b5a6
Revises: b1c2d3e4f5a6
Create Date: 2026-08-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f1e2d3c4b5a6"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(sa.text(
            "ALTER TABLE booking ADD COLUMN IF NOT EXISTS "
            "has_bath_tub BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        op.execute(sa.text(
            "ALTER TABLE gift ADD COLUMN IF NOT EXISTS "
            "has_bath_tub BOOLEAN NOT NULL DEFAULT FALSE"
        ))
    else:
        with op.batch_alter_table("booking", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column("has_bath_tub", sa.Boolean(), nullable=False, server_default="0")
            )
        with op.batch_alter_table("gift", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column("has_bath_tub", sa.Boolean(), nullable=False, server_default="0")
            )


def downgrade() -> None:
    with op.batch_alter_table("booking", schema=None) as batch_op:
        batch_op.drop_column("has_bath_tub")
    with op.batch_alter_table("gift", schema=None) as batch_op:
        batch_op.drop_column("has_bath_tub")
