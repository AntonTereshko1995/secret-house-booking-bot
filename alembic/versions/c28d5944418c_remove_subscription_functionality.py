"""remove_subscription_functionality

Revision ID: c28d5944418c
Revises: 8e261b9824f5
Create Date: 2025-10-01 11:13:26.443063

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c28d5944418c'
down_revision: Union[str, None] = '8e261b9824f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('booking', schema=None) as batch_op:
        batch_op.drop_column('subscription_id')
    
    # Drop the subscription table
    op.drop_table('subscription')


def downgrade() -> None:
    # Recreate subscription table
    op.create_table('subscription',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.INTEGER(), nullable=False),
        sa.Column('date_expired', sa.DATETIME(), nullable=False),
        sa.Column('subscription_type', sa.INTEGER(), nullable=False),
        sa.Column('is_paymented', sa.BOOLEAN(), nullable=False),
        sa.Column('price', sa.FLOAT(), nullable=False),
        sa.Column('code', sa.VARCHAR(length=15), nullable=False),
        sa.Column('is_done', sa.BOOLEAN(), nullable=False),
        sa.Column('number_of_visits', sa.INTEGER(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    
    # Add subscription_id column back to booking table using batch mode
    with op.batch_alter_table('booking', schema=None) as batch_op:
        batch_op.add_column(sa.Column('subscription_id', sa.INTEGER(), nullable=True))
        batch_op.create_foreign_key('booking_subscription_id_fkey', 'subscription', ['subscription_id'], ['id'])
