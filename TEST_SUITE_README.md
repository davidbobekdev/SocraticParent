# Test Suite Documentation

## Overview
`test_suite.sh` is a comprehensive testing script that validates the Socratic Parent application before deployment. It tests against the **production Railway deployment** at `https://socratesparent-production.up.railway.app`.

## Cache-Busting Strategy

The app uses **version parameters** (`?v=7`) on static files to force browser cache updates:
- `styles.css?v=7` and `app.js?v=7`
- **IMPORTANT**: Increment version number in `static/index.html` before each deployment
- Current version: **v7**

### How to Update Version Number

Before deploying changes to static files (CSS/JS), increment the version:

```html
<!-- In static/index.html, change: -->
<link rel="stylesheet" href="/static/styles.css?v=7">
<script src="/static/app.js?v=7"></script>

<!-- To: -->
<link rel="stylesheet" href="/static/styles.css?v=8">
<script src="/static/app.js?v=8"></script>
```

**When to increment:**
- Any change to `static/app.js`
- Any change to `static/styles.css`
- Any change to `static/index.html` that affects UI

**When NOT to increment:**
- Backend-only changes (`main.py`)
- Documentation updates
- Test suite changes

## Testing After Deployment

### Desktop Browser
1. **Normal changes**: Just refresh (F5 or Cmd+R)
2. **Stubborn cache**: Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

### Mobile Browser
1. **First try**: Normal refresh/reload
2. **If old behavior persists**: Close browser app completely → Reopen → Navigate to site
3. **Last resort**: Clear site data (Settings → Browser → Site settings → socratesparent-production.up.railway.app → Clear data)

### Testing Authentication Changes
- Clear cookies/site data before testing
- For UI/upload changes, cookies don't affect behavior

### Why This Works
The version parameter (`?v=7`) makes the browser treat each version as a completely new file. When you increment to `?v=8`, the browser must fetch the new file regardless of cache settings.

## Usage

### Run all tests before deploying:
```bash
./test_suite.sh
```

### Deploy only if tests pass:
```bash
./test_suite.sh && railway up --detach
```

### Complete Deployment Workflow:
```bash
# 1. Make changes to code
# 2. If static files changed, increment version in index.html
# 3. Run tests
./test_suite.sh

# 4. If tests pass, deploy
railway up --detach

# 5. On mobile device:
#    - Close browser app completely
#    - Reopen and navigate to site
#    - Test functionality
```

## What It Tests

### 1. **File Structure & Dependencies** ✓
- Verifies all critical files exist (main.py, static files, Dockerfile, etc.)
- Checks that required Python packages are installed

### 2. **Static File Integrity** ✓
- HTML has file input element without `capture` attribute (allows gallery selection)
- JavaScript contains required functions (handleFileSelect, analyzeHomework, etc.)
- CSS contains required classes (btn-outline, btn-solid, drop-zone, etc.)

### 3. **Production Server Tests** ✓
- Tests against live Railway deployment
- Verifies health endpoint
- Checks session creation
- Tests login and app pages load

### 4. **Authentication Tests** ✓
- Creates temporary test user
- Tests registration endpoint
- Tests login endpoint
- Verifies authenticated endpoints work

### 5. **File Upload Tests** ✓
- Tests file upload with a test image
- Verifies analyze endpoint works
- Checks response format

### 6. **Static Files Serving** ✓
- Verifies CSS and JS files are accessible
- Checks cache-busting version parameters are present

### 7. **Python Code Quality** ✓
- Validates Python syntax
- Checks for hardcoded credentials
- Counts TODO/FIXME comments

### 8. **Mobile Compatibility** ✓
- Verifies viewport meta tag
- Checks for responsive CSS media queries
- Validates mobile web app meta tags

### 9. **KaTeX Integration** ✓
- Checks KaTeX CDN links are present
- Verifies renderMath function exists

### 10. **Docker Configuration** ✓
- Validates Dockerfile structure
- Checks Railway configuration

## Test Results

The script provides colored output:
- 🟢 **[PASS]** - Test passed
- 🔴 **[FAIL]** - Test failed
- 🟡 **[WARN]** - Warning (non-critical)
- 🔵 **[INFO]** - Information

## Exit Codes

- `0` - All tests passed, safe to deploy
- `1` - Some tests failed, review before deploying

## Railway Logs

At the end, the script fetches the last 20 lines from Railway logs for debugging.

## Known Expected Failures

Some failures are expected in development:
- **Google GenAI not installed locally** - Only needed in production with API key
- **Health endpoint format** - May differ slightly between environments

## Workflow

1. Make changes to code
2. Run `./test_suite.sh`
3. Review any failures
4. Fix issues
5. Re-run tests
6. Once passing, deploy: `railway up --detach`

## Customization

To test a different Railway URL, edit the `BASE_URL` variable at the top of `test_suite.sh`:

```bash
BASE_URL="https://your-app.up.railway.app"
```

## Benefits

- **Catches issues before deployment** - Mobile file upload bugs, missing files, broken endpoints
- **Tests real production** - Not just local environment
- **Fast feedback** - Runs in ~30 seconds
- **Comprehensive** - Covers frontend, backend, auth, uploads, and mobile compatibility
- **Automated** - Run before every deploy to catch regressions

## Example Output

```
========================================
TEST SUMMARY
========================================

Total Tests: 41
Passed: 38
Failed: 3

✓ ALL TESTS PASSED - SAFE TO DEPLOY

To deploy to Railway, run:
  railway up --detach
```
