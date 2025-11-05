"""base migration

Revision ID: 16c4e4787de0
Revises:
Create Date: 2025-03-28 11:12:25.693384

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from db.models.decorator.type_decorator import IntEnumType
from src.models.enum.tariff import Tariff


# revision identifiers, used by Alembic.
revision: str = '16c4e4787de0'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This is a base migration for existing databases
    # All tables already exist, so we do nothing here
    pass


def downgrade() -> None:
    # Cannot downgrade from base migration
    pass
