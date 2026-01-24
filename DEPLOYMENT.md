# Deployment Guide for AI Agents

## Critical Information

### Current Version
- **Static files version**: `v7`
- **Production URL**: `https://socratesparent-production.up.railway.app`

### Before Every Deployment

1. **Check what files changed**
2. **If any static files changed (HTML/CSS/JS), increment version number**
3. **Run test suite**
4. **Deploy only if tests pass**

## Version Number Management

### Location
The version number is in `static/index.html`:

```html
<link rel="stylesheet" href="/static/styles.css?v=7">
<script src="/static/app.js?v=7"></script>
```

### When to Increment

**YES - Increment version when changing:**
- ✅ `static/app.js` - Any JavaScript changes
- ✅ `static/styles.css` - Any CSS changes  
- ✅ `static/index.html` - Any HTML/UI changes
- ✅ Mobile compatibility fixes
- ✅ Button behavior changes
- ✅ File upload logic changes

**NO - Do NOT increment for:**
- ❌ `main.py` - Backend-only changes
- ❌ Test suite updates
- ❌ Documentation changes
- ❌ Configuration files (Dockerfile, railway.json)

### How to Increment

**Find and replace BOTH occurrences in `static/index.html`:**

```html
<!-- FROM: -->
<link rel="stylesheet" href="/static/styles.css?v=7">
<!-- ... -->
<script src="/static/app.js?v=7"></script>

<!-- TO: -->
<link rel="stylesheet" href="/static/styles.css?v=8">
<!-- ... -->
<script src="/static/app.js?v=8"></script>
```

**Always increment to the next number**: v7 → v8 → v9 → v10, etc.

## Deployment Workflow

### Step 1: Make Changes
```bash
# Edit files as needed
vim static/app.js
vim static/styles.css
```

### Step 2: Increment Version (if needed)
```bash
# If you changed static files, update version in static/index.html
# Change ?v=7 to ?v=8 in BOTH places (CSS and JS)
```

### Step 3: Run Test Suite
```bash
cd /path/to/SocraticParent
./test_suite.sh
```

**Expected output:**
```
========================================
TEST SUMMARY
========================================

Total Tests: 38
Passed: 38
Failed: 0

✓ ALL TESTS PASSED - SAFE TO DEPLOY
```

### Step 4: Deploy
```bash
railway up --detach
```

### Step 5: Verify on Mobile
After deployment:
1. Close browser app completely on mobile device
2. Reopen browser
3. Navigate to `https://socratesparent-production.up.railway.app`
4. Test the specific functionality that changed

## Common Issues

### Issue: "Changes not showing on mobile"
**Solution:**
1. Verify version number was incremented
2. Close browser app completely (not just tab)
3. Clear site data if still not working
4. Check Railway logs: `railway logs --tail 50`

### Issue: "File upload not working on mobile"
**Solution:**
1. Check that file input doesn't have `capture` attribute
2. Verify file input overlay is working (opacity: 0, absolute positioning)
3. Check console logs on mobile (if debug mode enabled)

### Issue: "Buttons turning purple on click"
**Solution:**
1. Verify using `btn-outline` or `btn-solid` classes
2. Check that `:focus` styles use `!important`
3. Ensure `e.target.blur()` is called after button actions

### Issue: "Math not rendering"
**Solution:**
1. Verify KaTeX CDN links in HTML
2. Check that `renderMath()` is called after content loads
3. Ensure AI prompt includes $ symbols for math expressions

## Test Suite Details

### What Gets Tested
- ✅ File structure and dependencies
- ✅ Static file integrity (no `capture` attribute, required functions)
- ✅ Production server endpoints (health, login, app)
- ✅ Authentication (register, login, /api/me)
- ✅ File upload and analysis
- ✅ Static file serving (CSS, JS)
- ✅ Python code quality
- ✅ Mobile compatibility (viewport, responsive CSS)
- ✅ KaTeX integration
- ✅ Docker configuration

### Test Results Location
- Console output shows pass/fail for each test
- Railway logs fetched at end of test run
- Exit code: 0 = pass, 1 = fail

## Quick Reference Commands

```bash
# Run tests only
./test_suite.sh

# Run tests and deploy if passing
./test_suite.sh && railway up --detach

# Check Railway logs
railway logs --tail 50

# Check production health
curl https://socratesparent-production.up.railway.app/health

# Get current version from production
curl -s https://socratesparent-production.up.railway.app/static/app.js | head -5
```

## File Change Checklist

Before committing/deploying, verify:

- [ ] Static file version incremented (if static files changed)
- [ ] Test suite passes (`./test_suite.sh`)
- [ ] No debug code left in production (console.log, debug panels)
- [ ] Mobile compatibility tested
- [ ] Cache-busting parameters present
- [ ] Railway deployment successful

## For AI Agents

When modifying this codebase:

1. **Always run test suite before deploying**
2. **Increment version if you touch HTML/CSS/JS**
3. **Test on mobile after deployment (close browser, reopen)**
4. **Check Railway logs if issues occur**
5. **Don't deploy if tests fail**

The version parameter system (`?v=7`) ensures browsers fetch fresh code. Without incrementing, mobile users see cached old code even after deployment.

## Rollback Procedure

If deployment causes issues:

```bash
# Check recent logs
railway logs --tail 100

# Revert version in index.html
# Re-deploy previous working version
./test_suite.sh && railway up --detach
```

## Environment Variables

Required in Railway:
- `GEMINI_API_KEY` - Google Gemini API key (for AI analysis)
- `JWT_SECRET_KEY` - Secret key for JWT tokens (auto-generated if missing)
- `PORT` - Railway sets automatically to 8080

## Monitoring

Check production health:
```bash
# Should return: {"status":"healthy"}
curl https://socratesparent-production.up.railway.app/health
```

Check static files serving:
```bash
# Should return CSS content
curl https://socratesparent-production.up.railway.app/static/styles.css

# Should return JS content
curl https://socratesparent-production.up.railway.app/static/app.js
```
