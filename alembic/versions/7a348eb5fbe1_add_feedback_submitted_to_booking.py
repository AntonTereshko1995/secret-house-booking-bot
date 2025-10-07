"""add_feedback_submitted_to_booking

Revision ID: 7a348eb5fbe1
Revises: c28d5944418c
Create Date: 2025-10-07 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7a348eb5fbe1"
down_revision: Union[str, None] = "c28d5944418c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("booking", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "feedback_submitted", sa.Boolean(), nullable=False, server_default="0"
            )
        )


def downgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("booking", schema=None) as batch_op:
        batch_op.drop_column("feedback_submitted")
