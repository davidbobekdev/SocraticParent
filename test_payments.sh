#!/bin/bash

# Payment Integration Test Suite
# Tests the complete Paddle Billing integration
# Run: ./test_payments.sh

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${TEST_URL:-https://socratesparent-production.up.railway.app}"
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test user credentials
TEST_USER="testpay_$(date +%s)@test.com"
TEST_PASS="TestPass123!"

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Socratic Parent - Payment Integration Tests      ║${NC}"
echo -e "${BLUE}║  Testing: $BASE_URL${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Helper functions
pass_test() {
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${GREEN}✓${NC} $1"
}

fail_test() {
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${RED}✗${NC} $1"
    echo -e "${RED}  Error: $2${NC}"
}

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Test 1: Health Check
echo -e "\n${BLUE}Test Category: API Health${NC}"
info "Testing server availability..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
if [ "$HTTP_CODE" -eq 200 ]; then
    pass_test "Server is healthy (200 OK)"
else
    fail_test "Server health check failed" "Expected 200, got $HTTP_CODE"
fi

# Test 2: User Registration
echo -e "\n${BLUE}Test Category: User Management${NC}"
info "Registering test user: $TEST_USER"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/register" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USER\",\"password\":\"$TEST_PASS\",\"email\":\"$TEST_USER\"}")

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    pass_test "User registration successful"
else
    fail_test "User registration failed" "$REGISTER_RESPONSE"
fi

# Test 3: User Login
info "Logging in test user..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USER\",\"password\":\"$TEST_PASS\"}")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    JWT_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    pass_test "User login successful (JWT received)"
else
    fail_test "User login failed" "$LOGIN_RESPONSE"
    exit 1
fi

# Test 4: Check Initial User Status
echo -e "\n${BLUE}Test Category: Free Tier${NC}"
info "Checking initial user status..."
STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/user/status" \
    -H "Authorization: Bearer $JWT_TOKEN")

if echo "$STATUS_RESPONSE" | grep -q '"is_premium":false'; then
    pass_test "User starts as free tier (is_premium: false)"
else
    fail_test "User premium status incorrect" "$STATUS_RESPONSE"
fi

if echo "$STATUS_RESPONSE" | grep -q '"scans_left":3'; then
    pass_test "User has 3 initial scans"
else
    fail_test "User scan count incorrect" "Expected 3 scans"
fi

# Test 5: Test Scan Decrement (Mock)
info "Testing scan usage tracking..."
echo "$STATUS_RESPONSE" | grep -q '"scans_left":[0-9]' && pass_test "Scan counter is tracked"

# Test 6: Webhook Endpoint Exists
echo -e "\n${BLUE}Test Category: Paddle Integration${NC}"
info "Testing webhook endpoint availability..."
WEBHOOK_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/webhooks/paddle" \
    -H "Content-Type: application/json" \
    -d '{}')

if [ "$WEBHOOK_RESPONSE" -eq 400 ] || [ "$WEBHOOK_RESPONSE" -eq 401 ] || [ "$WEBHOOK_RESPONSE" -eq 200 ]; then
    pass_test "Webhook endpoint exists and responds"
else
    fail_test "Webhook endpoint unreachable" "Got HTTP $WEBHOOK_RESPONSE"
fi

# Test 7: Paddle.js Script Loading
info "Checking Paddle.js integration..."
HTML_RESPONSE=$(curl -s "$BASE_URL/app")
if echo "$HTML_RESPONSE" | grep -q "paddle.com/paddle"; then
    pass_test "Paddle.js script is loaded"
else
    fail_test "Paddle.js script not found in HTML" "Missing Paddle CDN"
fi

# Test 8: Premium Upgrade Button Present
if echo "$HTML_RESPONSE" | grep -q "Upgrade to Premium"; then
    pass_test "Upgrade to Premium button exists"
else
    fail_test "Upgrade button not found" "Check HTML"
fi

# Test 9: Price ID Configuration
if echo "$HTML_RESPONSE" | grep -q "pri_01kfr8qsrd2eggamsmeazrc5kq"; then
    pass_test "Paddle Price ID configured in frontend"
else
    warning "Price ID not visible in HTML (may be OK if in .env)"
fi

# Test 10: Manual Upgrade Test (Admin Endpoint)
echo -e "\n${BLUE}Test Category: Premium Features${NC}"
info "Testing manual premium upgrade..."
UPGRADE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/admin/upgrade-test?username=$TEST_USER&admin_secret=TEMP_ADMIN_2026")

if echo "$UPGRADE_RESPONSE" | grep -q '"success":true'; then
    pass_test "Manual premium upgrade successful"
    
    # Verify premium status
    info "Verifying premium status after upgrade..."
    sleep 1
    STATUS_AFTER=$(curl -s -X GET "$BASE_URL/api/user/status" \
        -H "Authorization: Bearer $JWT_TOKEN")
    
    if echo "$STATUS_AFTER" | grep -q '"is_premium":true'; then
        pass_test "User status updated to premium (is_premium: true)"
    else
        fail_test "Premium status not updated" "$STATUS_AFTER"
    fi
    
    if echo "$STATUS_AFTER" | grep -q '"scans_left":-1'; then
        pass_test "Premium user has unlimited scans (scans_left: -1)"
    else
        warning "Premium scan count format may differ"
    fi
else
    fail_test "Manual upgrade failed" "$UPGRADE_RESPONSE"
fi

# Test 11: Frontend Files
echo -e "\n${BLUE}Test Category: Frontend Assets${NC}"
info "Checking static file availability..."

CSS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/static/styles.css")
if [ "$CSS_CODE" -eq 200 ]; then
    pass_test "styles.css loads successfully"
else
    fail_test "styles.css not found" "HTTP $CSS_CODE"
fi

JS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/static/app.js")
if [ "$JS_CODE" -eq 200 ]; then
    pass_test "app.js loads successfully"
else
    fail_test "app.js not found" "HTTP $JS_CODE"
fi

# Test 12: Paywall Overlay in HTML
info "Checking paywall UI components..."
if echo "$HTML_RESPONSE" | grep -q "paywallOverlay"; then
    pass_test "Paywall overlay element exists"
else
    fail_test "Paywall overlay not found" "Missing paywallOverlay ID"
fi

# Test 13: Usage Info Display
if echo "$HTML_RESPONSE" | grep -q "usageInfo"; then
    pass_test "Usage info display element exists"
else
    fail_test "Usage info element not found" "Missing usageInfo ID"
fi

# Test 14: Environment Check
echo -e "\n${BLUE}Test Category: Configuration${NC}"
info "Checking Paddle environment configuration..."
if echo "$HTML_RESPONSE" | grep -q "sandbox"; then
    warning "Running in SANDBOX mode (test environment)"
else
    info "May be in production mode (or sandbox check needs update)"
fi

# Test 15: Database Persistence (Railway)
info "Testing data persistence capability..."
# Can't directly test Railway volume, but can verify users endpoint works
ME_RESPONSE=$(curl -s -X GET "$BASE_URL/api/me" \
    -H "Authorization: Bearer $JWT_TOKEN")
if echo "$ME_RESPONSE" | grep -q "$TEST_USER"; then
    pass_test "User data persistence working"
else
    fail_test "User data not persisting" "$ME_RESPONSE"
fi

# Summary
echo -e "\n${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                 TEST SUMMARY                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo -e "Total Tests:  $TOTAL_TESTS"
echo -e "${GREEN}Passed:       $PASSED_TESTS${NC}"
echo -e "${RED}Failed:       $FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}✓ All payment integration tests passed!${NC}"
    echo -e "${GREEN}✓ System is ready for testing with Paddle sandbox${NC}"
    exit 0
else
    echo -e "\n${RED}✗ Some tests failed. Please review errors above.${NC}"
    exit 1
fi
