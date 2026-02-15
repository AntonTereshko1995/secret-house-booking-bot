"""Remove unique constraint from promocode name

Revision ID: f8a2b3c4d5e6
Revises: aede36e59394
Create Date: 2025-11-28 17:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f8a2b3c4d5e6"
down_revision: Union[str, None] = "aede36e59394"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the unique constraint on name column
    # SQLite doesn't support dropping constraints directly, so we need to recreate the table
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        # SQLite doesn't support DROP CONSTRAINT, so we need to recreate the table
        # Create a new table without the unique constraint, copy data, drop old, rename new
        op.execute("""
            CREATE TABLE promocode_new (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) NOT NULL,
                promocode_type INTEGER NOT NULL DEFAULT 1,
                date_from DATE NOT NULL,
                date_to DATE NOT NULL,
                discount_percentage FLOAT NOT NULL,
                applicable_tariffs JSON,
                is_active BOOLEAN NOT NULL,
                created_at DATETIME NOT NULL
            )
        """)
        op.execute("""
            INSERT INTO promocode_new
            SELECT id, name, promocode_type, date_from, date_to,
                   discount_percentage, applicable_tariffs, is_active, created_at
            FROM promocode
        """)
        op.execute("DROP TABLE promocode")
        op.execute("ALTER TABLE promocode_new RENAME TO promocode")
    else:
        # For PostgreSQL and other databases, use direct SQL to safely drop constraint
        conn = op.get_bind()

        # Check if constraint exists using PostgreSQL system catalogs
        result = conn.execute(sa.text("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = 'promocode'
            AND constraint_type = 'UNIQUE'
            AND constraint_name LIKE '%name%'
        """))

        constraint_name = None
        row = result.fetchone()
        if row:
            constraint_name = row[0]

        if constraint_name:
            print(f"[MIGRATION] Dropping unique constraint: {constraint_name}")
            conn.execute(sa.text(f'ALTER TABLE promocode DROP CONSTRAINT "{constraint_name}"'))
            conn.commit()
        else:
            print("[MIGRATION] No unique constraint on 'name' column found, skipping")


def downgrade() -> None:
    # Restore the unique constraint
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        # Recreate table with unique constraint
        op.execute("""
            CREATE TABLE promocode_new (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) NOT NULL UNIQUE,
                promocode_type INTEGER NOT NULL DEFAULT 1,
                date_from DATE NOT NULL,
                date_to DATE NOT NULL,
                discount_percentage FLOAT NOT NULL,
                applicable_tariffs JSON,
                is_active BOOLEAN NOT NULL,
                created_at DATETIME NOT NULL
            )
        """)
        op.execute("""
            INSERT INTO promocode_new 
            SELECT id, name, promocode_type, date_from, date_to, 
                   discount_percentage, applicable_tariffs, is_active, created_at
            FROM promocode
        """)
        op.execute("DROP TABLE promocode")
        op.execute("ALTER TABLE promocode_new RENAME TO promocode")
    else:
        # For other databases, restore the unique constraint
        with op.batch_alter_table("promocode", schema=None) as batch_op:
            batch_op.create_unique_constraint("uq_promocode_name", ["name"])

