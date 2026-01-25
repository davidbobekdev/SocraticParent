# 🚀 Deployment Checklist for Paddle Integration

## Before Deployment

### 1. Paddle Account Setup
- [ ] Sign up for Paddle account (sandbox for testing)
- [ ] Complete business verification (for production)
- [ ] Add business details and tax information

### 2. Create Product in Paddle
- [ ] Go to Paddle Dashboard → Catalog → Products
- [ ] Create "Socratic Parent Premium" product
- [ ] Add description: "Unlimited AI homework analysis"
- [ ] Create monthly price: $9.99 USD
- [ ] Copy Price ID: `pri_...`

### 3. Configure Webhook
- [ ] Go to Developer Tools → Notifications
- [ ] Add notification destination
- [ ] URL: `https://your-app.up.railway.app/webhooks/paddle`
- [ ] Select events:
  - [x] subscription.created
  - [x] subscription.updated
  - [x] subscription.canceled
  - [x] subscription.expired
- [ ] Save and copy Signing Secret: `pdl_ntfn_...`

### 4. Get Client Token
- [ ] Go to Developer Tools → Authentication
- [ ] Create client-side token
- [ ] Copy token: `test_...` (sandbox) or `live_...` (production)

## Code Configuration

### 1. Update Paddle Token in HTML
Edit `static/index.html` around line 252:

```javascript
// BEFORE (placeholder):
Paddle.Initialize({
    token: 'YOUR_PADDLE_CLIENT_TOKEN',
    environment: 'sandbox'
});

// AFTER (with your token):
Paddle.Initialize({
    token: 'test_1234567890abcdef',  // Your actual sandbox token
    environment: 'sandbox'
});
```

### 2. Add Environment Variables to Railway

```bash
# Method 1: Using Railway CLI
railway variables set PADDLE_WEBHOOK_SECRET="pdl_ntfn_..."
railway variables set PADDLE_CLIENT_TOKEN="test_..."
railway variables set PADDLE_PRICE_ID="pri_..."

# Method 2: Using Railway Dashboard
# Go to your project → Variables → Raw Editor
# Add:
PADDLE_WEBHOOK_SECRET=pdl_ntfn_...
PADDLE_CLIENT_TOKEN=test_...
PADDLE_PRICE_ID=pri_...
```

### 3. Commit and Deploy

```bash
# Stage all changes
git add .

# Commit with descriptive message
git commit -m "Add Paddle Billing v2: Free tier (3/day) + Premium ($9.99/mo)"

# Push to GitHub
git push origin main

# Deploy to Railway (if auto-deploy not enabled)
railway up --detach
```

## Testing After Deployment

### 1. Test Free Tier Flow ✅
```bash
# Register new user
curl -X POST https://your-app.railway.app/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser1",
    "password": "test123",
    "email": "test1@example.com"
  }'

# Expected: 200 OK with success message

# Login
curl -X POST https://your-app.railway.app/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser1",
    "password": "test123"
  }'

# Expected: 200 OK with JWT token
# Save the token from response

# Check user status
curl -X GET https://your-app.railway.app/api/user/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Expected:
# {
#   "username": "testuser1",
#   "is_premium": false,
#   "scans_left": 3
# }
```

### 2. Test Usage Limit ✅
- [ ] Open app in browser
- [ ] Login with testuser1
- [ ] Header should show "3 scans left"
- [ ] Upload and analyze homework (Scan 1) → Success
- [ ] Check header → "2 scans left"
- [ ] Analyze again (Scan 2) → Success
- [ ] Check header → "1 scan left"
- [ ] Analyze again (Scan 3) → Success
- [ ] Check header → "0 scans left"
- [ ] Analyze again (Scan 4) → **Paywall appears**
- [ ] Paywall shows: "You've reached your daily limit"
- [ ] Solution content is blurred
- [ ] "Upgrade to Premium" button visible

### 3. Test Premium Upgrade Flow ✅
- [ ] Click "Upgrade to Premium" button
- [ ] Paddle checkout overlay opens
- [ ] Shows "$9.99/month" pricing
- [ ] Enter Paddle test card:
  - Card: 4242 4242 4242 4242
  - Exp: Any future date
  - CVV: Any 3 digits
- [ ] Complete checkout
- [ ] Checkout closes
- [ ] Header updates to "∞ Unlimited"
- [ ] Can analyze unlimited homework
- [ ] No paywall appears

### 4. Test Webhook Reception ✅
```bash
# Check Railway logs for webhook
railway logs | grep "Paddle webhook"

# Expected output:
# Paddle webhook received: subscription.created
# User upgraded to premium: testuser1
```

### 5. Verify Data Persistence ✅
```bash
# SSH into Railway container
railway run bash

# Check users.json
cat /data/users.json | jq '.[] | select(.username=="testuser1")'

# Expected output:
# {
#   "username": "testuser1",
#   "password_hash": "...",
#   "email": "test1@example.com",
#   "is_premium": true,
#   "daily_scans_left": 3,
#   "last_reset": "2024-01-15T10:30:00.000Z",
#   "paddle_subscription_id": "sub_01hqn5..."
# }
```

## Mobile Testing

### iOS Safari
- [ ] Open app on iPhone
- [ ] Test free tier (3 scans)
- [ ] Trigger paywall
- [ ] Paywall overlay displays correctly
- [ ] Blur effect works
- [ ] Checkout opens in overlay
- [ ] Can complete purchase
- [ ] Premium badge displays

### Android Chrome
- [ ] Same tests as iOS
- [ ] Check touch targets are accessible
- [ ] Verify checkout form is usable

## Production Checklist

### Before Going Live
- [ ] **Switch Paddle to Production**
  - Create production product and price
  - Get production webhook secret
  - Get production client token
  - Update all environment variables

- [ ] **Update Code**
  ```javascript
  // In static/index.html
  Paddle.Initialize({
      token: 'live_...', // Production token
      environment: 'production' // Production mode
  });
  ```

- [ ] **Legal & Compliance**
  - Add Terms of Service
  - Add Privacy Policy
  - Add Refund Policy
  - Configure Paddle email notifications

- [ ] **Final Tests**
  - Test with real payment method (small amount)
  - Verify subscription appears in Paddle dashboard
  - Test webhook processing
  - Test cancellation flow
  - Verify refunds work

## Monitoring

### Key Metrics to Track
```bash
# Daily active users
railway run cat /data/users.json | jq '. | length'

# Premium users count
railway run cat /data/users.json | jq '[.[] | select(.is_premium==true)] | length'

# Free users count
railway run cat /data/users.json | jq '[.[] | select(.is_premium==false)] | length'

# Watch real-time logs
railway logs --follow
```

### Paddle Dashboard
- [ ] Monitor subscription count
- [ ] Track MRR (Monthly Recurring Revenue)
- [ ] Check failed payments
- [ ] Review cancellation reasons
- [ ] Analyze conversion rate

## Rollback Plan

If issues occur:

```bash
# Revert to previous version
git revert HEAD
git push origin main

# Or rollback in Railway Dashboard
# Project → Deployments → Select previous → Rollback
```

## Common Issues

### Webhook Not Received
**Symptom**: User pays but doesn't get premium

**Fix**:
1. Check Railway logs: `railway logs | grep webhook`
2. Verify webhook URL in Paddle matches deployment
3. Test webhook signature locally
4. Check firewall/CORS settings

### Invalid Signature Error
**Symptom**: Webhook received but signature verification fails

**Fix**:
1. Verify `PADDLE_WEBHOOK_SECRET` matches Paddle dashboard
2. Check for extra whitespace in environment variable
3. Ensure using correct environment (sandbox vs production)

### Checkout Won't Open
**Symptom**: Click upgrade button, nothing happens

**Fix**:
1. Check browser console for JavaScript errors
2. Verify Paddle.js loaded: `console.log(typeof Paddle)`
3. Ensure `PADDLE_CLIENT_TOKEN` is correct
4. Check `PADDLE_PRICE_ID` exists in Paddle

### Premium Not Persisting
**Symptom**: Premium status lost after restart

**Fix**:
1. Verify Railway volume mounted at `/data`
2. Check users.json write permissions
3. Ensure atomic file writes in main.py
4. Backup users.json regularly

## Success Criteria

✅ Deployment is successful when:

- [ ] Free users can register and get 3 scans
- [ ] Usage counter displays and updates correctly
- [ ] Paywall appears on 4th scan attempt
- [ ] Upgrade button opens Paddle checkout
- [ ] Payment processing completes successfully
- [ ] Webhook received and processed
- [ ] Premium status activates immediately
- [ ] Premium users have unlimited access
- [ ] Mobile experience is smooth
- [ ] No console errors
- [ ] All tests pass

## Support Resources

- **Paddle Documentation**: https://developer.paddle.com/
- **Paddle Test Cards**: https://developer.paddle.com/concepts/payment-methods/credit-debit-card#test-card-numbers
- **Railway Docs**: https://docs.railway.app/
- **Project Docs**: See PADDLE_CONFIG.md and PADDLE_IMPLEMENTATION.md

---

**Last Updated**: After Paddle v2 implementation
**Status**: Ready for deployment
**Version**: v8
