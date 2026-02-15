"""Populate completed_bookings from existing data

Revision ID: ab9a47c0f211
Revises: 8be7e628f1ca
Create Date: 2025-11-05 17:24:39.134954

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column, select, func


# revision identifiers, used by Alembic.
revision: str = "ab9a47c0f211"
down_revision: Union[str, None] = "8be7e628f1ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Populate completed_bookings field for all users based on existing bookings.
    completed_bookings = COUNT of bookings where is_done=True AND is_canceled=False
    """
    # Create table references
    user = table(
        "user", column("id", sa.Integer), column("completed_bookings", sa.Integer)
    )

    booking = table(
        "booking",
        column("user_id", sa.Integer),
        column("is_done", sa.Boolean),
        column("is_canceled", sa.Boolean),
    )

    # Get connection
    conn = op.get_bind()

    # Calculate completed bookings per user
    # Use raw SQL to avoid SQLAlchemy converting True/False to 1/0
    completed_counts = conn.execute(
        sa.text("""
            SELECT user_id, COUNT(*) as completed_count
            FROM booking
            WHERE is_done = true AND is_canceled = false
            GROUP BY user_id
        """)
    ).fetchall()

    # Update each user's completed_bookings count
    for user_id, count in completed_counts:
        conn.execute(
            sa.text("UPDATE \"user\" SET completed_bookings = :count WHERE id = :user_id"),
            {"count": count, "user_id": user_id}
        )

    conn.commit()


def downgrade() -> None:
    """Reset completed_bookings to 0 for all users."""
    conn = op.get_bind()
    conn.execute(sa.text('UPDATE "user" SET completed_bookings = 0'))
    conn.commit()
