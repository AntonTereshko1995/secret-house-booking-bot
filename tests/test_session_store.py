"""
Unit tests for SessionStore class.
Tests in-memory storage, TTL expiration, persistence, and cleanup.
"""
import asyncio
import json
import time
import sys
import os
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.session.session_store import SessionStore


class TestSessionStore:
    """Test suite for SessionStore"""

    def setup_method(self):
        """Setup before each test"""
        self.test_file = Path("test_storage.json")
        if self.test_file.exists():
            self.test_file.unlink()

    def teardown_method(self):
        """Cleanup after each test"""
        if self.test_file.exists():
            self.test_file.unlink()

    async def test_set_and_get(self):
        """Test basic set and get operations"""
        store = SessionStore(str(self.test_file), cleanup_interval_days=1)
        await store.start()

        # Set a value
        await store.set("test_key", "test_value", ttl_seconds=3600)

        # Get the value
        result = await store.get("test_key")
        assert result == "test_value", f"Expected 'test_value', got '{result}'"

        await store.stop()
        print("[OK] test_set_and_get passed")

    async def test_get_nonexistent_key(self):
        """Test getting a non-existent key returns None"""
        store = SessionStore(str(self.test_file), cleanup_interval_days=1)
        await store.start()

        result = await store.get("nonexistent_key")
        assert result is None, f"Expected None, got '{result}'"

        await store.stop()
        print("[OK] test_get_nonexistent_key passed")

    async def test_ttl_expiration(self):
        """Test that expired entries return None"""
        store = SessionStore(str(self.test_file), cleanup_interval_days=1)
        await store.start()

        # Set with 1 second TTL
        await store.set("expiring_key", "expiring_value", ttl_seconds=1)

        # Immediately get - should work
        result = await store.get("expiring_key")
        assert result == "expiring_value", "Value should exist immediately"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Get after expiration - should be None
        result = await store.get("expiring_key")
        assert result is None, f"Expected None after expiration, got '{result}'"

        await store.stop()
        print("[OK] test_ttl_expiration passed")

    async def test_delete(self):
        """Test delete operation"""
        store = SessionStore(str(self.test_file), cleanup_interval_days=1)
        await store.start()

        # Set and verify
        await store.set("delete_key", "delete_value", ttl_seconds=3600)
        assert await store.get("delete_key") == "delete_value"

        # Delete and verify
        await store.delete("delete_key")
        result = await store.get("delete_key")
        assert result is None, f"Expected None after delete, got '{result}'"

        await store.stop()
        print("[OK] test_delete passed")

    async def test_persistence_to_disk(self):
        """Test that data persists to JSON file"""
        store = SessionStore(str(self.test_file), cleanup_interval_days=1)
        await store.start()

        # Set some values
        await store.set("key1", "value1", ttl_seconds=3600)
        await store.set("key2", "value2", ttl_seconds=7200)

        await store.stop()

        # Verify file exists and contains correct data
        assert self.test_file.exists(), "Storage file should exist"

        with open(self.test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert "key1" in data, "key1 should be in storage"
        assert "key2" in data, "key2 should be in storage"
        assert data["key1"]["value"] == "value1"
        assert data["key2"]["value"] == "value2"

        print("[OK] test_persistence_to_disk passed")

    async def test_load_from_disk(self):
        """Test that data loads from JSON file on startup"""
        # Create storage file manually
        test_data = {
            "loaded_key": {
                "value": "loaded_value",
                "created_at": time.time(),
                "ttl_seconds": 3600
            }
        }

        with open(self.test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        # Start store and verify data loaded
        store = SessionStore(str(self.test_file), cleanup_interval_days=1)
        await store.start()

        result = await store.get("loaded_key")
        assert result == "loaded_value", f"Expected 'loaded_value', got '{result}'"

        await store.stop()
        print("[OK] test_load_from_disk passed")

    async def test_cleanup_expired_entries(self):
        """Test that cleanup removes expired entries"""
        store = SessionStore(str(self.test_file), cleanup_interval_days=1)
        await store.start()

        # Add some entries with very short TTL
        await store.set("expired1", "value1", ttl_seconds=1)
        await store.set("expired2", "value2", ttl_seconds=1)
        await store.set("active", "active_value", ttl_seconds=3600)

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Run cleanup
        await store._cleanup_expired()

        # Verify expired entries are gone
        assert await store.get("expired1") is None
        assert await store.get("expired2") is None
        # But active entry remains
        assert await store.get("active") == "active_value"

        await store.stop()
        print("[OK] test_cleanup_expired_entries passed")

    async def test_concurrent_access(self):
        """Test concurrent read/write operations"""
        store = SessionStore(str(self.test_file), cleanup_interval_days=1)
        await store.start()

        async def write_task(key, value):
            await store.set(key, value, ttl_seconds=3600)

        async def read_task(key):
            return await store.get(key)

        # Run multiple concurrent operations
        await asyncio.gather(
            write_task("key1", "value1"),
            write_task("key2", "value2"),
            write_task("key3", "value3"),
        )

        # Verify all written
        results = await asyncio.gather(
            read_task("key1"),
            read_task("key2"),
            read_task("key3"),
        )

        assert results[0] == "value1"
        assert results[1] == "value2"
        assert results[2] == "value3"

        await store.stop()
        print("[OK] test_concurrent_access passed")

    async def test_corrupt_json_handling(self):
        """Test graceful handling of corrupt JSON file"""
        # Create corrupt JSON file
        with open(self.test_file, 'w') as f:
            f.write("{corrupt json content")

        # Should start successfully with empty storage
        store = SessionStore(str(self.test_file), cleanup_interval_days=1)
        await store.start()

        # Should be empty
        result = await store.get("any_key")
        assert result is None

        # Should be able to write
        await store.set("new_key", "new_value", ttl_seconds=3600)
        assert await store.get("new_key") == "new_value"

        await store.stop()
        print("[OK] test_corrupt_json_handling passed")


def run_async_test(coro):
    """Helper to run async test"""
    return asyncio.run(coro)


if __name__ == "__main__":
    print("Running SessionStore tests...\n")
    test_suite = TestSessionStore()

    tests = [
        test_suite.test_set_and_get(),
        test_suite.test_get_nonexistent_key(),
        test_suite.test_ttl_expiration(),
        test_suite.test_delete(),
        test_suite.test_persistence_to_disk(),
        test_suite.test_load_from_disk(),
        test_suite.test_cleanup_expired_entries(),
        test_suite.test_concurrent_access(),
        test_suite.test_corrupt_json_handling(),
    ]

    try:
        for test in tests:
            test_suite.setup_method()
            run_async_test(test)
            test_suite.teardown_method()

        print("\n[SUCCESS] All SessionStore tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n[FAILED] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
