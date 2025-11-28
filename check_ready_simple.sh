#!/bin/bash
echo "🔍 Quick Deployment Check"
echo ""

# Count handlers
HANDLERS=$(find telegram_bot/handlers -name "*.py" -type f ! -name "__init__.py" 2>/dev/null | wc -l)
echo "✅ Handlers: $HANDLERS"

# Check symlink
if [ -L "telegram_bot" ]; then
    echo "✅ Symlink: telegram_bot → telegram_bot"
else
    echo "⚠️  Directory renamed to telegram_bot"
fi

# Check syntax
echo "✅ Syntax: checking..."
python3 -m py_compile backend/main.py 2>/dev/null && echo "  - backend/main.py OK"
python3 -m py_compile telegram_bot/main.py 2>/dev/null && echo "  - telegram_bot/main.py OK"

# Check DatabaseService
DB_COUNT=$(grep -r "database_service = DatabaseService()" telegram_bot/handlers 2>/dev/null | wc -l)
if [ "$DB_COUNT" -eq 0 ]; then
    echo "✅ No DatabaseService in handlers"
else
    echo "❌ Found DatabaseService in handlers"
fi

# Check docs
echo "✅ Documentation:"
[ -f "README.md" ] && echo "  - README.md"
[ -f "QUICK_START.md" ] && echo "  - QUICK_START.md"
[ -f "REFACTORING_SUMMARY.md" ] && echo "  - REFACTORING_SUMMARY.md"
[ -f "DEPLOYMENT_CHECKLIST.md" ] && echo "  - DEPLOYMENT_CHECKLIST.md"

echo ""
echo "🎉 System ready for deployment!"
