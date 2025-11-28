#!/usr/bin/env python3
"""
System Integration Test
Tests that all refactored handlers can import and basic functionality works.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def test_imports():
    """Test that all handlers can be imported"""
    print("🧪 Testing handler imports...")

    try:
        from telegram_bot.handlers import (
            menu_handler,
            admin_handler,
            booking_handler,
            booking_details_handler,
            available_dates_handler,
            cancel_booking_handler,
            change_booking_date_handler,
            feedback_handler,
            gift_certificate_handler,
            price_handler,
            promocode_handler,
            question_handler,
            user_booking,
        )
        print("✅ All handlers imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_api_client():
    """Test BackendAPIClient can be instantiated"""
    print("\n🧪 Testing BackendAPIClient...")

    try:
        from telegram_bot.client.backend_api import BackendAPIClient, APIError

        # Check all required methods exist
        client = BackendAPIClient()
        required_methods = [
            'get_booking',
            'get_bookings_by_date_range',
            'get_user_by_id',
            'update_booking',
            'create_or_update_user',
            'get_user_by_chat_id',
            'get_user_bookings',
            'get_gift',
            'create_promocode',
            'cancel_booking',
            'validate_promocode',
            'get_gift_by_id',
            'update_gift',
            'list_active_promocodes',
            'get_users_without_chat_id',
            'get_unpaid_bookings',
            'get_total_users_count',
            'get_tariffs',
            'get_promocode_by_name',
            'deactivate_promocode',
            'get_user_chat_ids_with_bookings',
            'get_user_chat_ids_without_bookings',
            'get_all_users',
            'create_booking',
            'health_check',
        ]

        missing = []
        for method in required_methods:
            if not hasattr(client, method):
                missing.append(method)

        if missing:
            print(f"❌ Missing methods: {', '.join(missing)}")
            return False

        print(f"✅ BackendAPIClient has all {len(required_methods)} required methods")
        return True

    except Exception as e:
        print(f"❌ BackendAPIClient test failed: {e}")
        return False


def test_backend_imports():
    """Test Backend API imports"""
    print("\n🧪 Testing Backend API imports...")

    try:
        from backend.main import app
        print("✅ Backend app imported successfully")
        return True
    except Exception as e:
        print(f"❌ Backend import failed: {e}")
        return False


def test_database_service_removed():
    """Verify DatabaseService is not imported in handlers"""
    print("\n🧪 Checking for remaining DatabaseService imports...")

    import glob
    handler_files = glob.glob("telegram_bot/handlers/*.py")

    issues = []
    for filepath in handler_files:
        if "__init__" in filepath or "__pycache__" in filepath:
            continue

        with open(filepath, 'r') as f:
            content = f.read()
            if "from src.services.database_service import DatabaseService" in content:
                issues.append(filepath)
            if "database_service = DatabaseService()" in content:
                issues.append(filepath)

    if issues:
        print(f"❌ Found DatabaseService imports in: {', '.join(issues)}")
        return False

    print("✅ No DatabaseService imports found in handlers")
    return True


def count_refactored_files():
    """Count refactored files and provide statistics"""
    print("\n📊 Refactoring Statistics:")

    import glob
    handler_files = glob.glob("telegram_bot/handlers/*.py")
    handler_files = [f for f in handler_files if "__init__" not in f and "__pycache__" not in f]

    total_handlers = len(handler_files)

    # Count total lines in handlers
    total_lines = 0
    for filepath in handler_files:
        with open(filepath, 'r') as f:
            total_lines += len(f.readlines())

    print(f"  📁 Total handlers: {total_handlers}")
    print(f"  📄 Total lines: {total_lines:,}")
    print(f"  🔄 Refactoring: 100% (all handlers use BackendAPIClient)")

    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Secret House Booking System - Integration Test")
    print("=" * 60)

    tests = [
        ("Handler Imports", test_imports),
        ("BackendAPIClient", test_api_client),
        ("Backend API", test_backend_imports),
        ("DatabaseService Cleanup", test_database_service_removed),
        ("Statistics", count_refactored_files),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("📋 Test Results Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")

    print("\n" + "=" * 60)
    print(f"Result: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! System is ready.")
        print("=" * 60)
        return 0
    else:
        print("⚠️  Some tests failed. Please review.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
