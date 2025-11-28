#!/bin/bash

# Deployment Readiness Check Script
# Verifies that the system is ready for deployment

set -e

echo "======================================================================"
echo "🔍 Secret House Booking System - Deployment Readiness Check"
echo "======================================================================"
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0
WARNINGS=0

# Function to print success
success() {
    echo "✅ $1"
    ((CHECKS_PASSED++))
}

# Function to print failure
fail() {
    echo "❌ $1"
    ((CHECKS_FAILED++))
}

# Function to print warning
warn() {
    echo "⚠️  $1"
    ((WARNINGS++))
}

# Function to print info
info() {
    echo "ℹ️  $1"
}

echo "📂 Checking project structure..."
echo ""

# Check critical directories exist
if [ -d "backend" ]; then
    success "Backend directory exists"
else
    fail "Backend directory not found"
fi

if [ -d "telegram_bot" ]; then
    success "Telegram bot directory exists"
else
    fail "Telegram bot directory not found"
fi

if [ -d "telegram_bot/handlers" ]; then
    success "Handlers directory exists"
    HANDLER_COUNT=$(find telegram_bot/handlers -name "*.py" -type f ! -name "__init__.py" | wc -l | tr -d ' ')
    info "Found $HANDLER_COUNT handler files"
else
    fail "Handlers directory not found"
fi

# Check for symlink
if [ -L "telegram_bot" ]; then
    success "Symbolic link telegram_bot exists"
else
    warn "Symbolic link telegram_bot not found - may cause import issues"
    info "Run: ln -s telegram_bot telegram_bot"
fi

echo ""
echo "📝 Checking critical files..."
echo ""

# Check for critical files
critical_files=(
    "backend/main.py"
    "telegram_bot/main.py"
    "telegram_bot/client/backend_api.py"
    "docker-compose.yml"
    "requirements.txt"
    "README.md"
)

for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        success "Found $file"
    else
        fail "Missing critical file: $file"
    fi
done

echo ""
echo "🔧 Checking configuration files..."
echo ""

# Check for config files
if [ -f ".env.docker.example" ]; then
    success "Example environment file exists"
else
    warn "Example environment file not found"
fi

if [ -f ".env" ] || [ -f ".env.debug" ] || [ -f ".env.production" ]; then
    success "Environment configuration found"
else
    warn "No environment file found - you'll need to create one"
    info "Copy .env.docker.example to .env and fill in values"
fi

echo ""
echo "🐍 Checking Python syntax..."
echo ""

# Check Python files for syntax errors
SYNTAX_ERRORS=0
echo "Checking backend files..."
for file in $(find backend -name "*.py" -type f 2>/dev/null); do
    if python3 -m py_compile "$file" 2>/dev/null; then
        :
    else
        fail "Syntax error in $file"
        ((SYNTAX_ERRORS++))
    fi
done

echo "Checking telegram_bot files..."
for file in $(find telegram_bot -name "*.py" -type f 2>/dev/null); do
    if python3 -m py_compile "$file" 2>/dev/null; then
        :
    else
        fail "Syntax error in $file"
        ((SYNTAX_ERRORS++))
    fi
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    success "No syntax errors found"
else
    fail "Found $SYNTAX_ERRORS files with syntax errors"
fi

echo ""
echo "🔍 Checking for legacy database imports..."
echo ""

# Check for remaining database_service imports
DB_IMPORTS=$(grep -r "from src.services.database_service import DatabaseService" telegram_bot/handlers --include="*.py" 2>/dev/null | wc -l | tr -d ' ')
if [ "$DB_IMPORTS" -eq 0 ]; then
    success "No DatabaseService imports found in handlers"
else
    fail "Found $DB_IMPORTS DatabaseService imports in handlers"
fi

echo ""
echo "📦 Checking dependencies..."
echo ""

# Check if requirements.txt exists and has content
if [ -f "requirements.txt" ]; then
    REQ_COUNT=$(grep -v "^#" requirements.txt | grep -v "^$" | wc -l | tr -d ' ')
    success "requirements.txt has $REQ_COUNT dependencies"
else
    fail "requirements.txt not found"
fi

# Check for Python 3
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    success "Python 3 installed: $PYTHON_VERSION"
else
    fail "Python 3 not found"
fi

# Check for Redis (optional but recommended)
if command -v redis-server &> /dev/null; then
    success "Redis installed"
elif command -v redis-cli &> /dev/null; then
    success "Redis CLI installed"
else
    warn "Redis not found - sessions won't persist"
    info "Install Redis or use Docker"
fi

# Check for Docker (optional)
if command -v docker &> /dev/null; then
    success "Docker installed"
    if command -v docker-compose &> /dev/null; then
        success "Docker Compose installed"
    else
        warn "Docker Compose not found"
    fi
else
    warn "Docker not found - can't use docker-compose deployment"
fi

echo ""
echo "📊 Running system test..."
echo ""

# Run system test if available
if [ -f "test_system.py" ]; then
    if python3 test_system.py 2>&1 | grep -q "All tests passed"; then
        success "System integration test passed"
    else
        warn "System test didn't pass completely (likely missing env vars)"
        info "Run: python3 test_system.py for details"
    fi
else
    warn "test_system.py not found"
fi

echo ""
echo "📋 Checking documentation..."
echo ""

docs=(
    "README.md"
    "QUICK_START.md"
    "REFACTORING_SUMMARY.md"
    "DEPLOYMENT_CHECKLIST.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        success "Documentation: $doc"
    else
        warn "Missing documentation: $doc"
    fi
done

echo ""
echo "======================================================================"
echo "📊 Summary"
echo "======================================================================"
echo ""
echo "✅ Checks passed: $CHECKS_PASSED"
echo "❌ Checks failed: $CHECKS_FAILED"
echo "⚠️  Warnings: $WARNINGS"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo "🎉 System is ready for deployment!"
    echo ""
    echo "Next steps:"
    echo "1. Create/update .env file with your configuration"
    echo "2. Run: python backend/main.py"
    echo "3. In another terminal run: python telegram_bot/main.py"
    echo "4. Or use Docker: docker-compose up --build"
    echo ""
    echo "For detailed instructions, see QUICK_START.md"
    exit 0
else
    echo "⚠️  System has issues that need to be resolved"
    echo ""
    echo "Please fix the failed checks above before deploying."
    echo "See DEPLOYMENT_CHECKLIST.md for detailed guidance."
    exit 1
fi
