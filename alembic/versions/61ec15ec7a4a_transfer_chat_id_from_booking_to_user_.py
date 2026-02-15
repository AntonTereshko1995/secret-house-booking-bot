"""Transfer chat_id from booking to user and add booking counters

Revision ID: 61ec15ec7a4a
Revises: 0c1b9c465d4d
Create Date: 2025-11-01 10:18:01.363155

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "61ec15ec7a4a"
down_revision: Union[str, None] = "0c1b9c465d4d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add new columns to user table
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("has_bookings", sa.Boolean(), nullable=False, server_default="false")
        )
        batch_op.add_column(
            sa.Column(
                "total_bookings", sa.Integer(), nullable=False, server_default="0"
            )
        )

    # Step 2: Transfer chat_id from booking to user and calculate booking counts
    connection = op.get_bind()

    # Get all users with their booking counts
    result = connection.execute(
        sa.text("""
        SELECT user_id, COUNT(*) as booking_count
        FROM booking
        GROUP BY user_id
    """)
    )

    # Update users with booking counts
    for row in result:
        user_id, booking_count = row
        connection.execute(
            sa.text("""
            UPDATE "user"
            SET has_bookings = true,
                total_bookings = :booking_count
            WHERE id = :user_id
        """),
            {"booking_count": booking_count, "user_id": user_id},
        )

    # Step 3: Remove chat_id column from booking table
    with op.batch_alter_table("booking", schema=None) as batch_op:
        batch_op.drop_column("chat_id")


def downgrade() -> None:
    # Step 1: Add chat_id back to booking
    with op.batch_alter_table("booking", schema=None) as batch_op:
        batch_op.add_column(sa.Column("chat_id", sa.Integer(), nullable=True))

    # Step 2: Restore chat_id from user to booking
    connection = op.get_bind()

    # Copy chat_id from user to all their bookings
    connection.execute(
        sa.text("""
        UPDATE booking
        SET chat_id = (SELECT chat_id FROM "user" WHERE "user".id = booking.user_id)
        WHERE EXISTS (SELECT 1 FROM "user" WHERE "user".id = booking.user_id AND "user".chat_id IS NOT NULL)
    """)
    )

    # Make chat_id NOT NULL after data transfer
    with op.batch_alter_table("booking", schema=None) as batch_op:
        batch_op.alter_column("chat_id", nullable=False)

    # Step 3: Remove new columns from user
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("total_bookings")
        batch_op.drop_column("has_bookings")
