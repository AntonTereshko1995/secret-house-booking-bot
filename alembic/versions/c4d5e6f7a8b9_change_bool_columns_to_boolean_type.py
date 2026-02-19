"""Change has_bookings and is_active columns to Boolean type

Revision ID: c4d5e6f7a8b9
Revises: 86e9eed4ea92, a1b2c3d4e5f6
Create Date: 2026-02-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = ("86e9eed4ea92", "a1b2c3d4e5f6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            sa.text(
                'ALTER TABLE "user" '
                "ALTER COLUMN has_bookings TYPE BOOLEAN USING has_bookings::boolean, "
                "ALTER COLUMN is_active TYPE BOOLEAN USING is_active::boolean"
            )
        )
    else:
        with op.batch_alter_table("user", schema=None) as batch_op:
            batch_op.alter_column(
                "has_bookings",
                type_=sa.Boolean(),
                existing_type=sa.Integer(),
                existing_nullable=False,
                existing_server_default="0",
            )
            batch_op.alter_column(
                "is_active",
                type_=sa.Boolean(),
                existing_type=sa.Integer(),
                existing_nullable=False,
                existing_server_default="1",
            )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            sa.text(
                'ALTER TABLE "user" '
                "ALTER COLUMN has_bookings TYPE INTEGER USING has_bookings::integer, "
                "ALTER COLUMN is_active TYPE INTEGER USING is_active::integer"
            )
        )
    else:
        with op.batch_alter_table("user", schema=None) as batch_op:
            batch_op.alter_column(
                "has_bookings",
                type_=sa.Integer(),
                existing_type=sa.Boolean(),
                existing_nullable=False,
                existing_server_default="0",
            )
            batch_op.alter_column(
                "is_active",
                type_=sa.Integer(),
                existing_type=sa.Boolean(),
                existing_nullable=False,
                existing_server_default="1",
            )
