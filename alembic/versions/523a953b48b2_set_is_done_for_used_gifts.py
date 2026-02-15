"""Set is_done for used gifts

Revision ID: 523a953b48b2
Revises: 5765b8f265b8
Create Date: 2025-11-07 22:15:39.556797

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "523a953b48b2"
down_revision: Union[str, None] = "5765b8f265b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Set is_done=True for all gifts that have been used in bookings
    # Find gifts by checking if they are referenced in booking table
    op.execute("""
        UPDATE gift
        SET is_done = true
        WHERE id IN (
            SELECT DISTINCT gift_id
            FROM booking
            WHERE gift_id IS NOT NULL
        )
        AND is_done = false
    """)


def downgrade() -> None:
    # Revert is_done for gifts that were updated
    op.execute("""
        UPDATE gift
        SET is_done = false
        WHERE id IN (
            SELECT DISTINCT gift_id
            FROM booking
            WHERE gift_id IS NOT NULL
        )
        AND is_done = true
    """)
