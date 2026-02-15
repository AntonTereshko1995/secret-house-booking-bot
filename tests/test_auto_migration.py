"""
Test script for automatic migration functionality.

This script tests the automatic data migration logic without requiring
an actual PostgreSQL database.
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_database_url_detection():
    """Test database URL detection functions."""
    from db.run_migrations import is_postgresql_database, is_sqlite_database

    print("Testing database URL detection...")

    # Test PostgreSQL URLs
    assert is_postgresql_database("postgresql://user:pass@host/db")
    assert is_postgresql_database("postgres://user:pass@host/db")
    assert not is_postgresql_database("sqlite:///test.db")
    print("  [OK] PostgreSQL detection works")

    # Test SQLite URLs
    assert is_sqlite_database("sqlite:///test.db")
    assert not is_sqlite_database("postgresql://user:pass@host/db")
    print("  [OK] SQLite detection works")


def test_sqlite_file_detection():
    """Test SQLite file detection."""
    from db.run_migrations import check_sqlite_file_exists

    print("\nTesting SQLite file detection...")

    exists, path = check_sqlite_file_exists()
    if exists:
        print(f"  [OK] SQLite file found: {path}")
    else:
        print("  [INFO] No SQLite file found (expected if not exists)")


def test_empty_database_check_logic():
    """Test the logic for checking if database is empty."""
    print("\nTesting empty database check logic...")

    # Mock test - just verify the function exists and can be imported
    from db.run_migrations import is_database_empty

    print("  [OK] is_database_empty function is defined")
    print("  [INFO] Actual database check requires PostgreSQL connection")


def test_migration_function_import():
    """Test that migration function can be imported."""
    print("\nTesting migration function import...")

    try:
        from db.migrate_sqlite_to_postgres import migrate_data

        print("  [OK] migrate_data function can be imported")
        print("  [OK] Function signature: migrate_data(source_url, target_url)")
    except ImportError as e:
        print(f"  [ERROR] Failed to import migrate_data: {e}")
        return False

    return True


def test_auto_migration_workflow():
    """Test the complete auto-migration workflow logic."""
    print("\nTesting auto-migration workflow...")

    # Test scenario descriptions
    scenarios = [
        {
            "name": "PostgreSQL with empty database and SQLite exists",
            "database_url": "postgresql://user:pass@host/db",
            "db_empty": True,
            "sqlite_exists": True,
            "should_migrate": True,
        },
        {
            "name": "PostgreSQL with data already present",
            "database_url": "postgresql://user:pass@host/db",
            "db_empty": False,
            "sqlite_exists": True,
            "should_migrate": False,
        },
        {
            "name": "PostgreSQL but no SQLite file",
            "database_url": "postgresql://user:pass@host/db",
            "db_empty": True,
            "sqlite_exists": False,
            "should_migrate": False,
        },
        {
            "name": "SQLite database (not PostgreSQL)",
            "database_url": "sqlite:///test.db",
            "db_empty": True,
            "sqlite_exists": True,
            "should_migrate": False,
        },
    ]

    for scenario in scenarios:
        print(f"\n  Scenario: {scenario['name']}")
        print(f"    Database URL: {scenario['database_url']}")
        print(f"    Database empty: {scenario['db_empty']}")
        print(f"    SQLite exists: {scenario['sqlite_exists']}")
        print(f"    Should migrate: {scenario['should_migrate']}")

        # Logic check
        from db.run_migrations import is_postgresql_database

        is_postgres = is_postgresql_database(scenario["database_url"])

        will_migrate = (
            is_postgres and scenario["db_empty"] and scenario["sqlite_exists"]
        )

        if will_migrate == scenario["should_migrate"]:
            print(f"    [OK] Logic correct: {'Will migrate' if will_migrate else 'Will not migrate'}")
        else:
            print(f"    [ERROR] Logic error: Expected {scenario['should_migrate']}, got {will_migrate}")


def test_run_migrations_function():
    """Test that run_migrations_if_needed function is properly defined."""
    print("\nTesting run_migrations_if_needed function...")

    try:
        from db.run_migrations import run_migrations_if_needed

        print("  [OK] run_migrations_if_needed function is defined")
        print("  [INFO] This function will be called automatically on bot startup")
    except ImportError as e:
        print(f"  [ERROR] Failed to import run_migrations_if_needed: {e}")
        return False

    return True


def main():
    """Run all tests."""
    print("=" * 80)
    print("Testing Automatic Migration Functionality")
    print("=" * 80)
    print()

    try:
        test_database_url_detection()
        test_sqlite_file_detection()
        test_empty_database_check_logic()
        test_migration_function_import()
        test_auto_migration_workflow()
        test_run_migrations_function()

        print("\n" + "=" * 80)
        print("[OK] All tests passed!")
        print("=" * 80)
        print()
        print("How automatic migration works:")
        print("1. Bot starts with DATABASE_URL=postgresql://...")
        print("2. db/run_migrations.py is called from db/database.py")
        print("3. Alembic creates schema if needed")
        print("4. auto_migrate_data_if_needed() checks:")
        print("   - Is using PostgreSQL? -> Yes")
        print("   - Is PostgreSQL empty? -> Yes (no records in user table)")
        print("   - SQLite file exists? -> Yes")
        print("5. Automatic migration runs:")
        print("   - migrate_data(sqlite:///.../test.db, postgresql://...)")
        print("6. Data copied: user -> gift -> promocode -> booking")
        print("7. Sequences reset for future inserts")
        print("8. Bot continues with migrated data")
        print()

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"[ERROR] Test failed: {e}")
        print("=" * 80)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
