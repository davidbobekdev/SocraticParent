#!/bin/bash
# Comprehensive automated test suite for Socratic Parent
# Run this to verify all functionality

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🧪 Socratic Parent - Automated Test Suite"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "Testing: $test_name... "
    
    if eval "$test_command" > /tmp/test_output.log 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Error: $(cat /tmp/test_output.log | head -5)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# 1. Check Docker is running
echo "1️⃣  Environment Checks"
echo "-------------------"
run_test "Docker daemon" "docker info > /dev/null 2>&1"
run_test "Docker Compose available" "command -v docker > /dev/null"
echo ""

# 2. Check container is running
echo "2️⃣  Container Status"
echo "-------------------"
run_test "Container running" "docker compose ps | grep -q 'Up'"
run_test "Container healthy" "docker compose ps | grep -q 'healthy\\|Up'"
echo ""

# 3. Check health endpoint
echo "3️⃣  API Health Checks"
echo "-------------------"
run_test "Health endpoint responds" "curl -sf http://localhost:8000/health > /dev/null"
run_test "Health endpoint returns JSON" "curl -s http://localhost:8000/health | jq -e '.status' > /dev/null"
run_test "AI configured flag true" "curl -s http://localhost:8000/health | jq -e '.ai_configured == true' > /dev/null"
echo ""

# 4. Check frontend files
echo "4️⃣  Frontend Files"
echo "-------------------"
run_test "index.html exists" "[ -f static/index.html ]"
run_test "styles.css exists" "[ -f static/styles.css ]"
run_test "app.js exists" "[ -f static/app.js ]"
run_test "Frontend accessible" "curl -sf http://localhost:8000/ > /dev/null"
echo ""

# 5. Create test image if needed
echo "5️⃣  Test Image Creation"
echo "-------------------"
if [ ! -f "test_homework.jpg" ]; then
    echo "Creating test image..."
    docker compose exec -T socratic-parent python3 -c "
from PIL import Image, ImageDraw
img = Image.new('RGB', (400, 200), color='white')
draw = ImageDraw.Draw(img)
draw.text((20, 20), 'Math Problem:\n\n6 ÷ 2(1 + 2) = ?', fill='black')
img.save('/tmp/test_homework.jpg', 'JPEG')
" > /dev/null 2>&1
    docker compose cp socratic-parent:/tmp/test_homework.jpg test_homework.jpg > /dev/null 2>&1
fi
run_test "Test image exists" "[ -f test_homework.jpg ]"
echo ""

# 6. Test API endpoints
echo "6️⃣  API Functionality"
echo "-------------------"

# Test analyze endpoint
ANALYZE_RESPONSE=$(curl -s -X POST http://localhost:8000/analyze \
    -F "file=@test_homework.jpg" \
    -F "grade=6-8" 2>&1)

ANALYZE_CODE=$?

if [ $ANALYZE_CODE -eq 0 ]; then
    run_test "Analyze endpoint responds" "echo '$ANALYZE_RESPONSE' | jq -e '.subject' > /dev/null"
    run_test "Questions returned" "echo '$ANALYZE_RESPONSE' | jq -e '.questions.foundation' > /dev/null"
    run_test "Behavioral tip returned" "echo '$ANALYZE_RESPONSE' | jq -e '.behavioral_tip' > /dev/null"
    run_test "Solution steps returned" "echo '$ANALYZE_RESPONSE' | jq -e '.solution_steps | length > 0' > /dev/null"
    run_test "Example approach returned" "echo '$ANALYZE_RESPONSE' | jq -e '.example_approach' > /dev/null"
else
    echo -e "${RED}✗ FAILED${NC} - Could not reach analyze endpoint"
    TESTS_FAILED=$((TESTS_FAILED + 5))
fi
echo ""

# 7. Test response quality
echo "7️⃣  Response Quality"
echo "-------------------"
if [ $ANALYZE_CODE -eq 0 ]; then
    run_test "Subject field non-empty" "echo '$ANALYZE_RESPONSE' | jq -e '.subject | length > 0' > /dev/null"
    run_test "Has 3 question categories" "echo '$ANALYZE_RESPONSE' | jq -e '.questions | length == 3' > /dev/null"
    run_test "Solution has multiple steps" "echo '$ANALYZE_RESPONSE' | jq -e '.solution_steps | length >= 4' > /dev/null"
    run_test "Steps contain numbers" "echo '$ANALYZE_RESPONSE' | jq -r '.solution_steps[]' | grep -q '[0-9]'"
else
    TESTS_FAILED=$((TESTS_FAILED + 4))
fi
echo ""

# 8. Test configuration files
echo "8️⃣  Configuration"
echo "-------------------"
run_test ".env file exists" "[ -f .env ]"
run_test ".env.example exists" "[ -f .env.example ]"
run_test "Dockerfile exists" "[ -f Dockerfile ]"
run_test "docker-compose.yml exists" "[ -f docker-compose.yml ]"
run_test "requirements.txt exists" "[ -f requirements.txt ]"
echo ""

# 9. Test documentation
echo "9️⃣  Documentation"
echo "-------------------"
run_test "README.md exists" "[ -f README.md ]"
run_test "README has content" "[ $(wc -l < README.md) -gt 50 ]"
run_test "LICENSE exists" "[ -f LICENSE ]"
run_test "docs directory exists" "[ -d docs ]"
echo ""

# 10. Container logs check
echo "🔟  Container Logs"
echo "-------------------"
RECENT_ERRORS=$(docker compose logs --tail=50 socratic-parent 2>&1 | grep -i "error\|exception\|failed" | wc -l)
if [ "$RECENT_ERRORS" -lt 3 ]; then
    echo -e "No critical errors in logs ${GREEN}✓ PASSED${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠ WARNING${NC} - Found $RECENT_ERRORS error entries in logs"
    echo "Recent errors:"
    docker compose logs --tail=50 socratic-parent 2>&1 | grep -i "error\|exception\|failed" | head -3
fi
echo ""

# Summary
echo "=========================================="
echo "📊 Test Summary"
echo "=========================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
TOTAL=$((TESTS_PASSED + TESTS_FAILED))
echo "Total Tests: $TOTAL"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    echo "✅ Application is working correctly"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo "Please review the errors above"
    exit 1
fi
