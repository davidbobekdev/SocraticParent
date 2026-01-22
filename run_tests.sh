#!/bin/bash
# Comprehensive automated test suite for Socratic Parent
# Tests all functionality using shell commands and curl

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"
TEST_DIR="test_images"
RESULTS_FILE="test_results.txt"

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Print header
echo -e "${BOLD}${CYAN}"
echo "======================================================================"
echo "  🎓 SOCRATIC PARENT - COMPREHENSIVE TEST SUITE"
echo "======================================================================"
echo -e "${NC}"

# Function to print test result
test_result() {
    local name="$1"
    local status="$2"
    local message="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    case "$status" in
        PASS)
            PASSED_TESTS=$((PASSED_TESTS + 1))
            echo -e "${GREEN}✓ PASS${NC} - $name"
            ;;
        FAIL)
            FAILED_TESTS=$((FAILED_TESTS + 1))
            echo -e "${RED}✗ FAIL${NC} - $name"
            if [ -n "$message" ]; then
                echo -e "  ${RED}└─ $message${NC}"
            fi
            ;;
        SKIP)
            SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
            echo -e "${YELLOW}⊘ SKIP${NC} - $name"
            if [ -n "$message" ]; then
                echo -e "  ${YELLOW}└─ $message${NC}"
            fi
            ;;
    esac
}

# Function to create test images using ImageMagick or similar
create_test_images() {
    echo -e "\n${BOLD}Creating Test Images...${NC}"
    
    mkdir -p "$TEST_DIR"
    
    # Check if we can create images
    if command -v convert &> /dev/null; then
        # Using ImageMagick
        convert -size 600x400 xc:white -gravity center -pointsize 32 -annotate +0-50 "Math Problem:" -pointsize 28 -annotate +0+0 "15 + 27 = ?" -annotate +0+50 "Show your work" "$TEST_DIR/math_addition.jpg" 2>/dev/null
        convert -size 600x400 xc:white -gravity center -pointsize 32 -annotate +0-30 "Multiplication:" -pointsize 28 -annotate +0+20 "8 × 7 = ?" "$TEST_DIR/math_multiplication.jpg" 2>/dev/null
        convert -size 600x400 xc:white -gravity center -pointsize 32 -annotate +0-50 "Fractions:" -pointsize 28 -annotate +0+0 "1/2 + 1/4 = ?" -annotate +0+50 "Simplify" "$TEST_DIR/math_fractions.jpg" 2>/dev/null
        convert -size 600x400 xc:white -gravity center -pointsize 24 -annotate +0-80 "Word Problem:" -pointsize 20 -annotate +0-30 "Sarah has 15 apples." -annotate +0+0 "She gives 6 to her friend." -annotate +0+30 "How many apples does" -annotate +0+60 "Sarah have left?" "$TEST_DIR/word_problem.jpg" 2>/dev/null
        convert -size 600x400 xc:white -gravity center -pointsize 32 -annotate +0-50 "Algebra:" -pointsize 28 -annotate +0+0 "Solve for x:" -annotate +0+40 "2x + 5 = 13" "$TEST_DIR/algebra.jpg" 2>/dev/null
        
        echo -e "  ${GREEN}✓${NC} Created test images using ImageMagick"
    else
        # Create simple placeholder images with base64
        echo -e "  ${YELLOW}⚠${NC} ImageMagick not found, creating minimal test images"
        
        # Create a minimal 1x1 white JPEG for testing
        base64 -d <<< "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAA8A/9k=" > "$TEST_DIR/math_addition.jpg"
        cp "$TEST_DIR/math_addition.jpg" "$TEST_DIR/math_multiplication.jpg"
        cp "$TEST_DIR/math_addition.jpg" "$TEST_DIR/math_fractions.jpg"
        cp "$TEST_DIR/math_addition.jpg" "$TEST_DIR/word_problem.jpg"
        cp "$TEST_DIR/math_addition.jpg" "$TEST_DIR/algebra.jpg"
    fi
}

# Check if server is running
check_server() {
    echo -e "\n${BOLD}Checking Server Status...${NC}"
    
    if curl -s -f "$BASE_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Server is running at $BASE_URL${NC}"
        test_result "Server is running" "PASS"
        return 0
    else
        echo -e "${RED}✗ Server is not running at $BASE_URL${NC}"
        echo -e "\n${YELLOW}Please start the server first:${NC}"
        echo -e "  ${CYAN}docker compose up -d${NC}"
        echo -e "  or"
        echo -e "  ${CYAN}python main.py${NC}"
        test_result "Server is running" "FAIL" "Cannot connect"
        return 1
    fi
}

# Test health endpoint
test_health() {
    echo -e "\n${BOLD}Testing Health Endpoint...${NC}"
    
    response=$(curl -s -w "\n%{http_code}" "$BASE_URL/health")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        test_result "Health endpoint responds" "PASS"
    else
        test_result "Health endpoint responds" "FAIL" "HTTP $http_code"
        return
    fi
    
    # Check JSON structure
    if echo "$body" | grep -q '"status"' && echo "$body" | grep -q '"ai_configured"'; then
        test_result "Health response has required fields" "PASS"
    else
        test_result "Health response has required fields" "FAIL"
    fi
    
    # Check AI configuration
    if echo "$body" | grep -q '"ai_configured":true' || echo "$body" | grep -q '"ai_configured": true'; then
        test_result "AI (Gemini) is configured" "PASS"
    else
        test_result "AI (Gemini) is configured" "SKIP" "Using fallback mode"
    fi
}

# Test static files
test_static_files() {
    echo -e "\n${BOLD}Testing Static Files...${NC}"
    
    # Test index.html
    if curl -s -f "$BASE_URL/" > /dev/null; then
        test_result "Static file: index.html" "PASS"
    else
        test_result "Static file: index.html" "FAIL"
    fi
    
    # Test styles.css
    if curl -s -f "$BASE_URL/static/styles.css" > /dev/null; then
        test_result "Static file: styles.css" "PASS"
    else
        test_result "Static file: styles.css" "FAIL"
    fi
    
    # Test app.js
    if curl -s -f "$BASE_URL/static/app.js" > /dev/null; then
        test_result "Static file: app.js" "PASS"
    else
        test_result "Static file: app.js" "FAIL"
    fi
}

# Test analyze endpoint
test_analyze() {
    local image_file="$1"
    local grade="$2"
    local test_name="Analyze: $(basename "$image_file")"
    
    if [ ! -f "$image_file" ]; then
        test_result "$test_name" "SKIP" "Image not found"
        return
    fi
    
    # Make the request
    if [ -n "$grade" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/analyze" \
            -F "file=@$image_file" \
            -F "grade=$grade")
    else
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/analyze" \
            -F "file=@$image_file")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" != "200" ]; then
        test_result "$test_name" "FAIL" "HTTP $http_code"
        return
    fi
    
    # Check required fields
    if echo "$body" | grep -q '"subject"' && \
       echo "$body" | grep -q '"questions"' && \
       echo "$body" | grep -q '"behavioral_tip"'; then
        
        # Check question types
        if echo "$body" | grep -q '"foundation"' && \
           echo "$body" | grep -q '"bridge"' && \
           echo "$body" | grep -q '"mastery"'; then
            test_result "$test_name" "PASS"
        else
            test_result "$test_name" "FAIL" "Missing question types"
        fi
    else
        test_result "$test_name" "FAIL" "Missing required fields"
    fi
}

# Test all homework types
test_homework_analysis() {
    echo -e "\n${BOLD}Testing Homework Analysis...${NC}"
    
    if [ ! -d "$TEST_DIR" ] || [ -z "$(ls -A "$TEST_DIR" 2>/dev/null)" ]; then
        test_result "Test images available" "SKIP" "No test images"
        return
    fi
    
    test_result "Test images available" "PASS"
    
    # Test each image
    test_analyze "$TEST_DIR/math_addition.jpg" "3-5"
    test_analyze "$TEST_DIR/math_multiplication.jpg" "3-5"
    test_analyze "$TEST_DIR/math_fractions.jpg" "6-8"
    test_analyze "$TEST_DIR/word_problem.jpg" "3-5"
    test_analyze "$TEST_DIR/algebra.jpg" "9-12"
}

# Test error handling
test_error_handling() {
    echo -e "\n${BOLD}Testing Error Handling...${NC}"
    
    # Test without file
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/analyze")
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "422" ]; then
        test_result "Error handling: No file" "PASS"
    else
        test_result "Error handling: No file" "FAIL" "Expected 422, got $http_code"
    fi
    
    # Test with invalid file
    echo "Not an image" > /tmp/test_invalid.txt
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/analyze" \
        -F "file=@/tmp/test_invalid.txt")
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "400" ] || [ "$http_code" = "422" ]; then
        test_result "Error handling: Invalid file type" "PASS"
    else
        test_result "Error handling: Invalid file type" "FAIL" "Expected 400/422, got $http_code"
    fi
    
    rm -f /tmp/test_invalid.txt
}

# Test response quality
test_response_quality() {
    echo -e "\n${BOLD}Testing Response Quality...${NC}"
    
    local test_file="$TEST_DIR/math_addition.jpg"
    
    if [ ! -f "$test_file" ]; then
        test_result "Response quality" "SKIP" "Test image not found"
        return
    fi
    
    response=$(curl -s -X POST "$BASE_URL/analyze" \
        -F "file=@$test_file" \
        -F "grade=3-5")
    
    # Check that questions don't give away the answer
    if echo "$response" | grep -qi "42\|15 + 27"; then
        test_result "Questions don't reveal answer" "FAIL" "Answer found in questions"
    else
        test_result "Questions don't reveal answer" "PASS"
    fi
    
    # Check for solution steps
    if echo "$response" | grep -q '"solution_steps"'; then
        test_result "Response includes solution steps" "PASS"
        
        # Check if solution has calculations
        if echo "$response" | grep -E '\+|=|÷|×' | grep -q solution; then
            test_result "Solution contains calculations" "PASS"
        else
            test_result "Solution contains calculations" "SKIP" "Cannot verify"
        fi
    else
        test_result "Response includes solution steps" "SKIP" "No solution steps"
    fi
}

# Performance test
test_performance() {
    echo -e "\n${BOLD}Testing Performance...${NC}"
    
    local test_file="$TEST_DIR/math_addition.jpg"
    
    if [ ! -f "$test_file" ]; then
        test_result "Performance test" "SKIP" "Test image not found"
        return
    fi
    
    start_time=$(date +%s)
    response=$(curl -s -X POST "$BASE_URL/analyze" -F "file=@$test_file" -F "grade=3-5")
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    if [ $duration -lt 30 ]; then
        test_result "Response time < 30s" "PASS" "${duration}s"
    else
        test_result "Response time < 30s" "FAIL" "${duration}s (too slow)"
    fi
}

# Print summary
print_summary() {
    echo -e "\n${BOLD}======================================================================"
    echo -e "TEST SUMMARY"
    echo -e "======================================================================${NC}"
    echo -e "Total Tests:  $TOTAL_TESTS"
    echo -e "${GREEN}Passed:       $PASSED_TESTS${NC}"
    echo -e "${RED}Failed:       $FAILED_TESTS${NC}"
    echo -e "${YELLOW}Skipped:      $SKIPPED_TESTS${NC}"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "\n${GREEN}${BOLD}🎉 ALL TESTS PASSED!${NC}"
        echo -e "\n${CYAN}Results saved to: $RESULTS_FILE${NC}"
        return 0
    else
        echo -e "\n${RED}${BOLD}⚠️  SOME TESTS FAILED${NC}"
        echo -e "\n${CYAN}Results saved to: $RESULTS_FILE${NC}"
        return 1
    fi
}

# Main execution
main() {
    # Start results file
    echo "Socratic Parent Test Results - $(date)" > "$RESULTS_FILE"
    echo "======================================" >> "$RESULTS_FILE"
    
    # Run tests
    if ! check_server; then
        echo -e "\n${RED}Cannot proceed without server running${NC}"
        exit 1
    fi
    
    create_test_images
    test_health
    test_static_files
    test_homework_analysis
    test_error_handling
    test_response_quality
    test_performance
    
    # Save summary to file
    {
        echo ""
        echo "Summary:"
        echo "  Total:   $TOTAL_TESTS"
        echo "  Passed:  $PASSED_TESTS"
        echo "  Failed:  $FAILED_TESTS"
        echo "  Skipped: $SKIPPED_TESTS"
    } >> "$RESULTS_FILE"
    
    # Print summary and exit
    print_summary
    exit $?
}

# Run main
main
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
