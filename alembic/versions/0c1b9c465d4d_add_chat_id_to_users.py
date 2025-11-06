"""Add chat_id to users

Revision ID: 0c1b9c465d4d
Revises: 16c4e4787de0
Create Date: 2025-10-31 13:08:23.546985

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c1b9c465d4d'
down_revision: Union[str, None] = '16c4e4787de0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('chat_id', sa.BigInteger(), nullable=True))
        batch_op.create_unique_constraint('uq_user_chat_id', ['chat_id'])


def downgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('uq_user_chat_id', type_='unique')
        batch_op.drop_column('chat_id')
