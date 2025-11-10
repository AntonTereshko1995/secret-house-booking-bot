"""Merge multiple heads

Revision ID: d7cf40ae784b
Revises: 61ec15ec7a4a, 691bc97d7a18
Create Date: 2025-11-05 13:06:46.003634

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d7cf40ae784b"
down_revision: Union[str, None] = ("61ec15ec7a4a", "691bc97d7a18")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
