"""test_postgresql_compatibility

This is a TEST migration to verify PostgreSQL compatibility.
It tests all problematic cases found during migration:
1. Boolean fields (true/false vs 1/0)
2. Reserved table name "user" (must be quoted)
3. Various SQL operations with proper syntax

This migration should be REMOVED after successful testing!

Revision ID: 205f819391de
Revises: f8a2b3c4d5e6
Create Date: 2026-02-15 21:46:48.802189

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '205f819391de'
down_revision: Union[str, None] = 'f8a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Test all PostgreSQL compatibility cases.
    This migration only performs READ operations and temporary table creation.
    It does NOT modify existing data.
    """
    conn = op.get_bind()

    print("\n" + "="*70)
    print("STARTING POSTGRESQL COMPATIBILITY TESTS")
    print("="*70)

    # TEST 1: Reserved word "user" table access
    print("\n[TEST 1] Testing reserved word 'user' table access...")
    try:
        result = conn.execute(sa.text('SELECT COUNT(*) as count FROM "user"'))
        user_count = result.fetchone()[0]
        print(f"✓ SUCCESS: Found {user_count} users in 'user' table")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    # TEST 2: Boolean field queries with true/false
    print("\n[TEST 2] Testing boolean queries with true/false...")
    try:
        result = conn.execute(sa.text('''
            SELECT COUNT(*) as count
            FROM booking
            WHERE is_done = true AND is_canceled = false
        '''))
        booking_count = result.fetchone()[0]
        print(f"✓ SUCCESS: Found {booking_count} completed bookings")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    # TEST 3: Boolean field queries with NOT
    print("\n[TEST 3] Testing boolean NOT queries...")
    try:
        result = conn.execute(sa.text('''
            SELECT COUNT(*) as count
            FROM booking
            WHERE NOT is_canceled
        '''))
        active_bookings = result.fetchone()[0]
        print(f"✓ SUCCESS: Found {active_bookings} non-canceled bookings")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    # TEST 4: JOIN with reserved word table
    print("\n[TEST 4] Testing JOIN with 'user' table...")
    try:
        result = conn.execute(sa.text('''
            SELECT COUNT(*) as count
            FROM booking b
            INNER JOIN "user" u ON b.user_id = u.id
            WHERE u.is_active = true
        '''))
        active_user_bookings = result.fetchone()[0]
        print(f"✓ SUCCESS: Found {active_user_bookings} bookings for active users")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    # TEST 5: Boolean aggregation
    print("\n[TEST 5] Testing boolean field aggregation...")
    try:
        result = conn.execute(sa.text('''
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_done = true) as completed,
                COUNT(*) FILTER (WHERE is_canceled = true) as canceled
            FROM booking
        '''))
        row = result.fetchone()
        print(f"✓ SUCCESS: Total: {row[0]}, Completed: {row[1]}, Canceled: {row[2]}")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    # TEST 6: Subquery with user table
    print("\n[TEST 6] Testing subquery with 'user' table...")
    try:
        result = conn.execute(sa.text('''
            SELECT COUNT(*) as count
            FROM booking
            WHERE user_id IN (
                SELECT id FROM "user" WHERE has_bookings = true
            )
        '''))
        count = result.fetchone()[0]
        print(f"✓ SUCCESS: Found {count} bookings for users with has_bookings=true")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    # TEST 7: CASE statement with boolean
    print("\n[TEST 7] Testing CASE with boolean fields...")
    try:
        result = conn.execute(sa.text('''
            SELECT
                CASE
                    WHEN is_done = true THEN 'completed'
                    WHEN is_canceled = true THEN 'canceled'
                    ELSE 'pending'
                END as status,
                COUNT(*) as count
            FROM booking
            GROUP BY status
        '''))
        for row in result:
            print(f"  - {row[0]}: {row[1]} bookings")
        print("✓ SUCCESS: CASE statement works correctly")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    # TEST 8: Create temporary test table with boolean and user reference
    print("\n[TEST 8] Testing CREATE temporary table with boolean...")
    try:
        conn.execute(sa.text('''
            CREATE TEMPORARY TABLE test_compatibility (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES "user"(id),
                is_test BOOLEAN DEFAULT true,
                test_value INTEGER
            )
        '''))
        print("✓ SUCCESS: Temporary table created")

        # Test INSERT with boolean
        conn.execute(sa.text('''
            INSERT INTO test_compatibility (user_id, is_test, test_value)
            SELECT id, true, 1
            FROM "user"
            LIMIT 1
        '''))
        print("✓ SUCCESS: INSERT with boolean=true works")

        # Test SELECT from temp table
        result = conn.execute(sa.text('''
            SELECT COUNT(*) FROM test_compatibility WHERE is_test = true
        '''))
        count = result.fetchone()[0]
        print(f"✓ SUCCESS: SELECT from temp table found {count} rows")

        # Test UPDATE with boolean
        conn.execute(sa.text('''
            UPDATE test_compatibility SET is_test = false WHERE test_value = 1
        '''))
        print("✓ SUCCESS: UPDATE with boolean=false works")

        # Cleanup temp table
        conn.execute(sa.text('DROP TABLE test_compatibility'))
        print("✓ SUCCESS: Temporary table dropped")

    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    # TEST 9: Gift table boolean checks
    print("\n[TEST 9] Testing gift table boolean fields...")
    try:
        result = conn.execute(sa.text('''
            SELECT COUNT(*) as count
            FROM gift
            WHERE is_done = false AND is_paymented = true
        '''))
        count = result.fetchone()[0]
        print(f"✓ SUCCESS: Found {count} paid but unused gifts")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    # TEST 10: Promocode table boolean check
    print("\n[TEST 10] Testing promocode table boolean fields...")
    try:
        result = conn.execute(sa.text('''
            SELECT COUNT(*) as count
            FROM promocode
            WHERE is_active = true
        '''))
        count = result.fetchone()[0]
        print(f"✓ SUCCESS: Found {count} active promocodes")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    print("\n" + "="*70)
    print("ALL POSTGRESQL COMPATIBILITY TESTS PASSED!")
    print("="*70 + "\n")


def downgrade() -> None:
    """
    No downgrade needed - this migration only performs read operations.
    """
    print("\n[TEST MIGRATION] No downgrade needed - read-only operations")
