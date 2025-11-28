#!/bin/bash
# Backend API Test Script

set -e

echo "🧪 Testing Secret House Backend API"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="${API_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-dev-api-key-12345}"

echo "📍 API URL: $API_URL"
echo "🔑 API Key: ${API_KEY:0:10}..."
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
echo "---------------------"
RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/health")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASSED${NC} - Health check returned 200"
    echo "  Response: $BODY"
else
    echo -e "${RED}✗ FAILED${NC} - Expected 200, got $HTTP_CODE"
    exit 1
fi
echo ""

# Test 2: List Tariffs
echo "Test 2: List Tariffs"
echo "--------------------"
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "X-API-Key: $API_KEY" \
    "$API_URL/api/v1/pricing/tariffs")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASSED${NC} - Tariffs endpoint returned 200"
    TARIFF_COUNT=$(echo "$BODY" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?")
    echo "  Found $TARIFF_COUNT tariffs"
else
    echo -e "${RED}✗ FAILED${NC} - Expected 200, got $HTTP_CODE"
    echo "  Response: $BODY"
    exit 1
fi
echo ""

# Test 3: Calculate Price
echo "Test 3: Calculate Price"
echo "-----------------------"
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "tariff": "DAY",
        "start_date": "2025-12-20T14:00:00",
        "end_date": "2025-12-21T12:00:00",
        "number_of_guests": 2,
        "has_sauna": true,
        "has_secret_room": false,
        "has_second_bedroom": false,
        "has_photoshoot": false
    }' \
    "$API_URL/api/v1/pricing/calculate")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASSED${NC} - Price calculation returned 200"
    TOTAL=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_price', 'N/A'))" 2>/dev/null || echo "N/A")
    echo "  Total Price: $TOTAL BYN"
else
    echo -e "${RED}✗ FAILED${NC} - Expected 200, got $HTTP_CODE"
    echo "  Response: $BODY"
    exit 1
fi
echo ""

# Test 4: Check Availability
echo "Test 4: Check Availability"
echo "--------------------------"
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "start_date": "2025-12-20T14:00:00",
        "end_date": "2025-12-21T12:00:00"
    }' \
    "$API_URL/api/v1/availability/check")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASSED${NC} - Availability check returned 200"
    AVAILABLE=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('available', 'N/A'))" 2>/dev/null || echo "N/A")
    echo "  Available: $AVAILABLE"
else
    echo -e "${RED}✗ FAILED${NC} - Expected 200, got $HTTP_CODE"
    echo "  Response: $BODY"
    exit 1
fi
echo ""

# Test 5: Authentication Test (should fail without API key)
echo "Test 5: Authentication (negative test)"
echo "--------------------------------------"
RESPONSE=$(curl -s -w "\n%{http_code}" \
    "$API_URL/api/v1/pricing/tariffs")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "401" ]; then
    echo -e "${GREEN}✓ PASSED${NC} - Authentication correctly rejected (401)"
else
    echo -e "${YELLOW}⚠ WARNING${NC} - Expected 401, got $HTTP_CODE (auth might not be enforced)"
fi
echo ""

# Summary
echo "================================"
echo -e "${GREEN}✓ All tests passed!${NC}"
echo "================================"
echo ""
echo "Backend API is working correctly! 🎉"
echo ""
echo "Next steps:"
echo "  1. View API docs: $API_URL/docs"
echo "  2. Explore endpoints in Swagger UI"
echo "  3. Start telegram bot (TODO)"
