#!/bin/bash

# Authentication Test Suite for Socratic Parent
# Tests registration, login, and protected endpoints

BASE_URL="http://localhost:8000"
PASSED=0
FAILED=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================="
echo "  Socratic Parent - Authentication Tests"
echo "========================================="
echo ""

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        ((FAILED++))
    fi
}

RANDOM_ID=$RANDOM
TEST_USER="testuser${RANDOM_ID}"
TEST_EMAIL="test${RANDOM_ID}@example.com"
TEST_PASS="testpass123"

echo "Test user: ${TEST_USER}"
echo ""

# Test 1: Health check
echo "Test 1: Health check..."
RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/health")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
[ "$HTTP_CODE" = "200" ] && test_result 0 "Health check" || test_result 1 "Health check"
echo ""

# Test 2: Login page
echo "Test 2: Login page..."
RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
[ "$HTTP_CODE" = "200" ] && test_result 0 "Login page accessible" || test_result 1 "Login page"
echo ""

# Test 3: Register
echo "Test 3: User registration..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/register" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${TEST_USER}\",\"email\":\"${TEST_EMAIL}\",\"password\":\"${TEST_PASS}\"}")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)
if [ "$HTTP_CODE" = "200" ] && echo "$BODY" | grep -q "access_token"; then
    TOKEN=$(echo "$BODY" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    test_result 0 "User registration"
else
    test_result 1 "User registration"
fi
echo ""

# Test 4: Duplicate registration
echo "Test 4: Duplicate registration..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/register" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${TEST_USER}\",\"email\":\"${TEST_EMAIL}\",\"password\":\"${TEST_PASS}\"}")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
[ "$HTTP_CODE" = "400" ] && test_result 0 "Duplicate blocked" || test_result 1 "Duplicate blocking"
echo ""

# Test 5: Login
echo "Test 5: Login..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${TEST_USER}\",\"password\":\"${TEST_PASS}\"}")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)
if [ "$HTTP_CODE" = "200" ] && echo "$BODY" | grep -q "access_token"; then
    TOKEN=$(echo "$BODY" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    test_result 0 "Login successful"
else
    test_result 1 "Login"
fi
echo ""

# Test 6: Wrong password
echo "Test 6: Wrong password..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${TEST_USER}\",\"password\":\"wrongpass\"}")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
[ "$HTTP_CODE" = "401" ] && test_result 0 "Wrong password rejected" || test_result 1 "Wrong password"
echo ""

# Test 7: Access /api/me without token
echo "Test 7: Unauthenticated /api/me..."
RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/api/me")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
[ "$HTTP_CODE" = "403" ] || [ "$HTTP_CODE" = "401" ] && test_result 0 "Access blocked" || test_result 1 "Access blocking"
echo ""

# Test 8: Access /api/me with token
echo "Test 8: Authenticated /api/me..."
if [ -n "$TOKEN" ]; then
    RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/api/me" \
        -H "Authorization: Bearer ${TOKEN}")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    [ "$HTTP_CODE" = "200" ] && echo "$BODY" | grep -q "username" && test_result 0 "Authenticated access" || test_result 1 "Authenticated access"
else
    test_result 1 "Authenticated access (no token)"
fi
echo ""

# Test 9: Invalid token
echo "Test 9: Invalid token..."
RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/api/me" \
    -H "Authorization: Bearer invalid_token")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
[ "$HTTP_CODE" = "401" ] && test_result 0 "Invalid token rejected" || test_result 1 "Invalid token"
echo ""

# Test 10: Short username
echo "Test 10: Short username..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/register" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"ab\",\"email\":\"short@test.com\",\"password\":\"testpass123\"}")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
[ "$HTTP_CODE" = "400" ] && test_result 0 "Short username rejected" || test_result 1 "Short username validation"
echo ""

# Test 11: Short password
echo "Test 11: Short password..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/register" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"validuser\",\"email\":\"valid@test.com\",\"password\":\"12345\"}")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
[ "$HTTP_CODE" = "400" ] && test_result 0 "Short password rejected" || test_result 1 "Short password validation"
echo ""

# Test 12: Session endpoint
echo "Test 12: Session endpoint..."
if [ -n "$TOKEN" ]; then
    RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/session" \
        -H "Authorization: Bearer ${TOKEN}")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    [ "$HTTP_CODE" = "200" ] && echo "$BODY" | grep -q "session_id" && test_result 0 "Session created" || test_result 1 "Session creation"
else
    test_result 1 "Session creation (no token)"
fi
echo ""

echo "========================================="
echo "  Test Summary"
echo "========================================="
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"
echo "Total:  $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed!${NC}"
    exit 1
fi
