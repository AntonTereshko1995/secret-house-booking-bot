#!/usr/bin/env python3
"""Test script to verify chat_id handling for users with empty chat_id."""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.services.database_service import DatabaseService
from src.services.logger_service import LoggerService

def test_update_user_chat_id_existing_user():
    """Test update_user_chat_id with existing user without chat_id."""
    print("\n" + "="*70)
    print("TEST 1: update_user_chat_id with existing user (no chat_id)")
    print("="*70)

    db_service = DatabaseService()

    # Test data from database: user id=1
    user_name = "@1"
    test_chat_id = 999888777  # Test chat_id

    print(f"\n📋 Test scenario:")
    print(f"   - Existing user: {user_name}")
    print(f"   - Current chat_id: NULL")
    print(f"   - Assigning chat_id: {test_chat_id}")

    # Check user before update
    user_before = db_service.get_user_by_contact("@1")
    if user_before:
        print(f"\n✅ User found in database:")
        print(f"   - ID: {user_before.id}")
        print(f"   - Contact: {user_before.contact}")
        print(f"   - Username: {user_before.user_name}")
        print(f"   - Chat ID: {user_before.chat_id}")
        print(f"   - Has bookings: {user_before.has_bookings}")
    else:
        print("❌ User not found!")
        return

    # Update chat_id
    print(f"\n🔄 Calling update_user_chat_id('{user_name}', {test_chat_id})...")
    try:
        user_after = db_service.update_user_chat_id(user_name, test_chat_id)
        print(f"\n✅ Update successful!")
        print(f"   - ID: {user_after.id}")
        print(f"   - Contact: {user_after.contact}")
        print(f"   - Username: {user_after.user_name}")
        print(f"   - Chat ID: {user_after.chat_id}")

        # Verify in database
        user_verify = db_service.get_user_by_chat_id(test_chat_id)
        if user_verify and user_verify.chat_id == test_chat_id:
            print(f"\n✅ Verification: chat_id saved correctly in database!")
        else:
            print(f"\n❌ Verification FAILED: chat_id not found in database!")

    except Exception as e:
        print(f"\n❌ Error during update: {e}")
        import traceback
        traceback.print_exc()


def test_update_user_contact_existing_user():
    """Test update_user_contact with existing user."""
    print("\n" + "="*70)
    print("TEST 2: update_user_contact with existing user")
    print("="*70)

    db_service = DatabaseService()

    # Use the chat_id from previous test
    test_chat_id = 999888777
    new_contact = "+375291234567"  # New contact to add

    print(f"\n📋 Test scenario:")
    print(f"   - Chat ID: {test_chat_id}")
    print(f"   - New contact: {new_contact}")

    # Check user before update
    user_before = db_service.get_user_by_chat_id(test_chat_id)
    if user_before:
        print(f"\n✅ User found by chat_id:")
        print(f"   - ID: {user_before.id}")
        print(f"   - Contact: {user_before.contact}")
        print(f"   - Username: {user_before.user_name}")
        print(f"   - Chat ID: {user_before.chat_id}")
    else:
        print(f"❌ User with chat_id {test_chat_id} not found!")
        return

    # Update contact
    print(f"\n🔄 Calling update_user_contact({test_chat_id}, '{new_contact}')...")
    try:
        user_after = db_service.update_user_contact(test_chat_id, new_contact)
        print(f"\n✅ Update successful!")
        print(f"   - ID: {user_after.id}")
        print(f"   - Contact: {user_after.contact}")
        print(f"   - Username: {user_after.user_name}")
        print(f"   - Chat ID: {user_after.chat_id}")

        # Verify in database
        user_verify = db_service.get_user_by_contact(new_contact)
        if user_verify and user_verify.contact == new_contact:
            print(f"\n✅ Verification: contact updated correctly in database!")
            # Verify chat_id is still there
            if user_verify.chat_id == test_chat_id:
                print(f"✅ Verification: chat_id {test_chat_id} preserved!")
            else:
                print(f"❌ Verification FAILED: chat_id was lost! Current: {user_verify.chat_id}")
        else:
            print(f"\n❌ Verification FAILED: contact not updated in database!")

    except Exception as e:
        print(f"\n❌ Error during update: {e}")
        import traceback
        traceback.print_exc()


def cleanup_test_data():
    """Clean up test data."""
    print("\n" + "="*70)
    print("CLEANUP: Removing test data")
    print("="*70)

    db_service = DatabaseService()
    test_chat_id = 999888777

    # Get user
    user = db_service.get_user_by_chat_id(test_chat_id)
    if user:
        print(f"\n🧹 Resetting user {user.id} data:")
        print(f"   - Restoring contact to: @1")
        print(f"   - Clearing chat_id")

        # Reset using raw SQL to avoid our logic
        import sqlite3
        conn = sqlite3.connect('test_the_secret_house.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE user SET contact = '@1', chat_id = NULL WHERE id = ?", (user.id,))
        conn.commit()
        conn.close()

        print("✅ Test data cleaned up!")
    else:
        print("ℹ️ No test data to clean up")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 TESTING CHAT_ID HANDLING FOR EXISTING USERS")
    print("="*70)

    try:
        # Run tests
        test_update_user_chat_id_existing_user()
        test_update_user_contact_existing_user()

        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED")
        print("="*70)

        # Ask if user wants to cleanup
        print("\nDo you want to clean up test data? (y/n): ", end="")
        # For automated testing, skip input
        # response = input().strip().lower()
        # if response == 'y':
        #     cleanup_test_data()

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
