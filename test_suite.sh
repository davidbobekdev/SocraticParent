#!/bin/bash

# Socratic Parent - Comprehensive Test Suite
# Run this before every deployment to ensure everything works

# Don't use set -e because we want to run all tests even if some fail

# Test against production Railway deployment
BASE_URL="https://socratesparent-production.up.railway.app"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
    ((TESTS_TOTAL++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
    ((TESTS_TOTAL++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Check if server is running
check_server() {
    if curl -s --max-time 5 "$BASE_URL/health" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# No need to start server - we test against production
# Remove all the server start/stop logic

# ============================================
# TEST 1: File Structure & Dependencies
# ============================================
log_section "TEST 1: File Structure & Dependencies"

# Check critical files exist
REQUIRED_FILES=(
    "main.py"
    "requirements.txt"
    "static/index.html"
    "static/app.js"
    "static/styles.css"
    "Dockerfile"
    "railway.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_success "File exists: $file"
    else
        log_error "Missing file: $file"
    fi
done

# Check Python dependencies (skip to avoid hanging)
log_warning "Skipping pip dependency checks (can cause hangs)"

# ============================================
# TEST 2: Static File Integrity
# ============================================
log_section "TEST 2: Static File Integrity"

# Check HTML for critical elements
if grep -q 'id="fileInput"' static/index.html; then
    log_success "File input element exists in HTML"
else
    log_error "File input element missing from HTML"
fi

if grep -q 'accept="image/\*"' static/index.html; then
    log_success "File input accepts images"
else
    log_error "File input image accept attribute missing"
fi

if grep -q 'capture=' static/index.html; then
    log_error "File input has capture attribute (forces camera mode)"
else
    log_success "File input does NOT have capture attribute (allows gallery)"
fi

# Check JavaScript critical functions
REQUIRED_JS_FUNCTIONS=(
    "handleFileSelect"
    "analyzeHomework"
    "displayResults"
    "renderMath"
)

for func in "${REQUIRED_JS_FUNCTIONS[@]}"; do
    if grep -q "function $func\|const $func\|$func.*=.*function" static/app.js; then
        log_success "JavaScript function exists: $func"
    else
        log_error "JavaScript function missing: $func"
    fi
done

# Check CSS for critical classes
REQUIRED_CSS_CLASSES=(
    ".btn-outline"
    ".btn-solid"
    ".drop-zone"
    ".question-card"
)

for class in "${REQUIRED_CSS_CLASSES[@]}"; do
    if grep -q "$class" static/styles.css; then
        log_success "CSS class exists: $class"
    else
        log_error "CSS class missing: $class"
    fi
done

# ============================================
# TEST 3: Backend Server Tests (Production)
# ============================================
log_section "TEST 3: Production Server Tests"

log_info "Testing against: $BASE_URL"

# Check if server is accessible
if check_server; then
    log_success "Production server is accessible"
    SERVER_RUNNING=true
else
    log_error "Production server is not accessible"
    SERVER_RUNNING=false
fi

if [ "$SERVER_RUNNING" = true ]; then
    # Test health endpoint
    if curl -s "$BASE_URL/health" | grep -q "healthy"; then
        log_success "Health endpoint responds correctly"
    else
        log_error "Health endpoint failed"
    fi

    # Test login page
    if curl -s "$BASE_URL/" | grep -q "Socratic Parent"; then
        log_success "Login page loads"
    else
        log_error "Login page failed to load"
    fi

    # Test app page (should redirect to login without auth)
    if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/app" | grep -q "200\|302"; then
        log_success "App endpoint accessible"
    else
        log_error "App endpoint failed"
    fi
else
    log_warning "Skipping server tests - server not accessible"
fi

# ============================================
# TEST 4: Authentication Tests
# ============================================
log_section "TEST 4: Authentication Tests"

# Create test user
TEST_USER="test_$(date +%s)"
TEST_EMAIL="$TEST_USER@test.com"
TEST_PASS="TestPass123!"

# Register test user
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/register" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USER\",\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASS\"}")

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    log_success "User registration works"
    TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
else
    log_error "User registration failed"
    TOKEN=""
fi

# Test login
if [ ! -z "$TOKEN" ]; then
    LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"$TEST_USER\",\"password\":\"$TEST_PASS\"}")
    
    if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
        log_success "User login works"
    else
        log_error "User login failed"
    fi
    
    # Test /api/me endpoint
    ME_RESPONSE=$(curl -s "$BASE_URL/api/me" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo "$ME_RESPONSE" | grep -q "$TEST_USER"; then
        log_success "Authenticated /api/me endpoint works"
    else
        log_error "Authenticated /api/me endpoint failed"
    fi
fi

# ============================================
# TEST 5: File Upload Tests
# ============================================
log_section "TEST 5: File Upload Tests"

if [ ! -z "$TOKEN" ]; then
    # Create a test image (1x1 PNG)
    TEST_IMAGE="/tmp/test_homework.png"
    echo -n "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" | base64 -d > "$TEST_IMAGE"
    
    # Test analyze endpoint (will use fallback since no real Gemini key)
    ANALYZE_RESPONSE=$(curl -s -X POST "$BASE_URL/analyze" \
        -H "Authorization: Bearer $TOKEN" \
        -F "file=@$TEST_IMAGE" \
        -F "grade=9-12")
    
    if echo "$ANALYZE_RESPONSE" | grep -q "questions\|foundation"; then
        log_success "File upload and analysis endpoint works"
    else
        log_error "File upload and analysis endpoint failed"
    fi
    
    rm -f "$TEST_IMAGE"
else
    log_warning "Skipping file upload tests (no auth token)"
fi

# ============================================
# TEST 6: Static Files Serving
# ============================================
log_section "TEST 6: Static Files Serving"

# Test CSS file
if curl -s "$BASE_URL/static/styles.css" | grep -q ".btn"; then
    log_success "CSS file serves correctly"
else
    log_error "CSS file not serving"
fi

# Test JS file
if curl -s "$BASE_URL/static/app.js" | grep -q "function\|const"; then
    log_success "JavaScript file serves correctly"
else
    log_error "JavaScript file not serving"
fi

# Check for cache-busting version parameters
if grep -q 'styles.css?v=' static/index.html; then
    log_success "CSS has cache-busting version parameter"
else
    log_warning "CSS missing cache-busting version parameter"
fi

if grep -q 'app.js?v=' static/index.html; then
    log_success "JS has cache-busting version parameter"
else
    log_warning "JS missing cache-busting version parameter"
fi

# ============================================
# TEST 7: Python Code Quality
# ============================================
log_section "TEST 7: Python Code Quality"

# Test Python syntax
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    log_error "Python not found for syntax check"
    PYTHON_CMD=""
fi

if [ ! -z "$PYTHON_CMD" ] && $PYTHON_CMD -m py_compile main.py 2>/dev/null; then
    log_success "main.py has valid Python syntax"
else
    log_error "main.py has syntax errors or Python not available"
fi

# Check for hardcoded credentials
if grep -i "password.*=.*['\"]" main.py | grep -v "password_hash\|hashed_password\|check_password" > /dev/null; then
    log_warning "Possible hardcoded credentials in main.py"
else
    log_success "No obvious hardcoded credentials"
fi

# Check for TODO/FIXME comments
TODO_COUNT=$(grep -c "TODO\|FIXME" main.py 2>/dev/null || echo "0")
if [ "$TODO_COUNT" -gt 0 ]; then
    log_warning "Found $TODO_COUNT TODO/FIXME comments in main.py"
fi

# ============================================
# TEST 8: Mobile Compatibility
# ============================================
log_section "TEST 8: Mobile Compatibility"

# Check viewport meta tag
if grep -q 'name="viewport"' static/index.html; then
    log_success "Viewport meta tag present"
else
    log_error "Viewport meta tag missing"
fi

# Check for responsive CSS
if grep -q "@media" static/styles.css; then
    log_success "Responsive CSS media queries present"
else
    log_warning "No responsive CSS media queries found"
fi

# Check mobile-specific meta tags
if grep -q 'mobile-web-app-capable' static/index.html; then
    log_success "Mobile web app meta tags present"
else
    log_warning "Mobile web app meta tags missing"
fi

# ============================================
# TEST 9: KaTeX Integration
# ============================================
log_section "TEST 9: KaTeX Integration"

# Check KaTeX CDN links
if grep -q "katex.*css" static/index.html; then
    log_success "KaTeX CSS included"
else
    log_error "KaTeX CSS missing"
fi

if grep -q "katex.*js" static/index.html; then
    log_success "KaTeX JavaScript included"
else
    log_error "KaTeX JavaScript missing"
fi

# Check renderMath function
if grep -q "renderMathInElement" static/app.js; then
    log_success "KaTeX rendering function present"
else
    log_error "KaTeX rendering function missing"
fi

# ============================================
# TEST 10: Docker Configuration
# ============================================
log_section "TEST 10: Docker Configuration"

if [ -f "Dockerfile" ]; then
    # Check Dockerfile has required commands
    if grep -q "FROM python" Dockerfile; then
        log_success "Dockerfile uses Python base image"
    else
        log_error "Dockerfile missing Python base image"
    fi
    
    if grep -q "COPY requirements.txt" Dockerfile; then
        log_success "Dockerfile copies requirements.txt"
    else
        log_error "Dockerfile missing requirements.txt copy"
    fi
    
    if grep -q "pip install" Dockerfile; then
        log_success "Dockerfile installs dependencies"
    else
        log_error "Dockerfile missing pip install"
    fi
fi

if [ -f "railway.json" ]; then
    log_success "Railway configuration exists"
else
    log_warning "Railway configuration missing"
fi

# ============================================
# FINAL REPORT
# ============================================
log_section "TEST SUMMARY"

echo ""
echo -e "${BLUE}Total Tests:${NC} $TESTS_TOTAL"
echo -e "${GREEN}Passed:${NC} $TESTS_PASSED"
echo -e "${RED}Failed:${NC} $TESTS_FAILED"
echo ""

# Fetch recent Railway logs
log_section "RECENT RAILWAY LOGS"
log_info "Fetching last 20 lines from Railway..."
railway logs --tail 20 2>/dev/null || log_warning "Could not fetch Railway logs (railway CLI not available)"

echo ""
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED - SAFE TO DEPLOY${NC}"
    echo ""
    echo "To deploy to Railway, run:"
    echo "  railway up --detach"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED - FIX ISSUES BEFORE DEPLOYING${NC}"
    exit 1
fi
