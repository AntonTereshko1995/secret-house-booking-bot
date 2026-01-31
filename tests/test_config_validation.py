"""Test validation of prepayment rules configuration."""
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set UTF-8 encoding for Windows console
if os.name == "nt":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from src.models.holiday_prepayment_rule import HolidayPrepaymentRule


def test_load_rules():
    """Test loading rules from JSON."""
    with open("src/config/holiday_prepayment_rules.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    rules = [HolidayPrepaymentRule(**item) for item in data["prepayment_rules"]]

    print(f"[OK] Loaded {len(rules)} rules\n")

    for rule in rules:
        recurring_str = "recurring" if rule.is_recurring else "one-time"
        print(
            f"  - {rule.name}: {rule.date} ({recurring_str}, {rule.prepayment_percentage}%)"
        )

    return rules


if __name__ == "__main__":
    try:
        rules = test_load_rules()
        print(f"\n[OK] All rules loaded and validated successfully")
        print(f"[OK] Total holidays: {len(rules)}")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Validation failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
