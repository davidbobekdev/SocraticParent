# Payment Integration Testing Guide

## Overview

This document contains comprehensive test cases for the Paddle Billing integration. Run these tests before any major deployment or after making payment-related changes.

---

## Automated Test Suite

### Quick Test
```bash
chmod +x test_payments.sh
./test_payments.sh
```

### What It Tests
- ✅ Server health and API availability
- ✅ User registration and authentication
- ✅ Initial free tier status (3 scans)
- ✅ Paddle webhook endpoint
- ✅ Frontend Paddle.js integration
- ✅ Manual premium upgrade
- ✅ Premium status verification
- ✅ Frontend assets loading
- ✅ Paywall UI components
- ✅ Data persistence

**Expected Output**: 15/15 tests passing

---

## Manual Test Scenarios

### Test 1: Free Tier Flow (New User)

**Objective**: Verify free tier works correctly

**Steps**:
1. Register new user: `testuser1@example.com` / `TestPass123!`
2. Login successfully
3. **Expected**: Header shows "3 scans left"
4. Upload homework image #1 → Analyze
5. **Expected**: Analysis completes, header shows "2 scans left"
6. Analyze homework #2
7. **Expected**: Header shows "1 scan left"
8. Analyze homework #3
9. **Expected**: Header shows "0 scans left"
10. Attempt homework #4
11. **Expected**: 
    - Paywall overlay appears
    - Content is blurred
    - Message: "You've used all 3 free scans today!"
    - "Upgrade to Premium" button visible

**Pass Criteria**: All scan counts accurate, paywall triggers on 4th scan

---

### Test 2: Daily Reset (24 Hour Limit)

**Objective**: Verify scans reset after 24 hours

**Steps**:
1. Use all 3 scans with test user
2. Wait 24+ hours (or manually update `last_reset` in database)
3. Login again
4. **Expected**: Header shows "3 scans left" (reset)
5. Able to analyze homework again

**Pass Criteria**: Counter resets to 3 after 24 hours

**Manual Reset (for testing)**:
```bash
railway run bash
# In container:
python3 << 'EOF'
import json
from datetime import datetime, timedelta
with open('/data/users.json', 'r') as f:
    users = json.load(f)
for user in users.values():
    if 'last_reset' in user:
        # Set to 25 hours ago
        user['last_reset'] = (datetime.now() - timedelta(hours=25)).isoformat()
        user['daily_scans_left'] = 0
with open('/data/users.json', 'w') as f:
    json.dump(users, f, indent=2)
print("Reset times updated!")
EOF
exit
```

---

### Test 3: Paddle Checkout Flow (Sandbox)

**Objective**: Complete payment with test card

**Steps**:
1. Register new user: `testpay2@example.com`
2. Use all 3 scans to trigger paywall
3. Click "⭐ Upgrade to Premium"
4. **Expected**: Paddle checkout overlay opens
5. Enter payment details:
   - **Email**: testpay2@example.com
   - **Country**: Any
   - Click "Continue/Fortfahren"
6. Enter card details:
   - **Card**: `4242 4242 4242 4242`
   - **Exp**: `12/27`
   - **CVV**: `123`
   - **Name**: Test User
7. Complete payment
8. **Expected**: 
   - Payment processes
   - Success message
   - Redirected back to app
9. Refresh page
10. **Expected**: Header shows "∞ Unlimited"

**Pass Criteria**: Payment completes, user becomes premium automatically

---

### Test 4: Webhook Processing

**Objective**: Verify webhook upgrades user

**Steps**:
1. Complete Test 3 (make a payment)
2. Check Railway logs:
   ```bash
   railway logs | grep -i webhook | tail -20
   ```
3. **Expected Log Output**:
   ```
   [WEBHOOK] Received Paddle webhook
   [WEBHOOK] Event type: subscription.created
   [WEBHOOK] Looking for user: user_id=testpay2@example.com
   [WEBHOOK] User testpay2@example.com upgraded to premium!
   POST /webhooks/paddle HTTP/1.1" 200 OK
   ```
4. Verify user in database:
   ```bash
   railway run cat /data/users.json | grep -A5 "testpay2"
   ```
5. **Expected**:
   ```json
   {
     "username": "testpay2@example.com",
     "is_premium": true,
     "paddle_subscription_id": "sub_01xxxxx"
   }
   ```

**Pass Criteria**: Webhook returns 200, user is_premium=true

---

### Test 5: Premium User Experience

**Objective**: Verify premium users have unlimited access

**Steps**:
1. Login as premium user (from Test 3)
2. **Expected**: Header shows "∞ Unlimited"
3. Analyze homework #1 → Success
4. Analyze homework #2 → Success  
5. Analyze homework #3 → Success
6. Analyze homework #4 → Success
7. Analyze homework #5 → Success
8. **Expected**: No paywall ever appears
9. All analyses complete successfully

**Pass Criteria**: Unlimited analyses work, no paywall

---

### Test 6: Upgrade Button Visibility

**Objective**: Check upgrade button shows/hides correctly

**Steps**:
1. **As FREE user**: 
   - Login
   - **Expected**: Header shows "⭐ Upgrade to Premium" button
2. **As PREMIUM user**:
   - Login
   - **Expected**: Upgrade button is HIDDEN
   - Only shows "∞ Unlimited" badge

**Pass Criteria**: Button visibility matches user status

---

### Test 7: Subscription Cancellation

**Objective**: Verify cancellation downgrades user

**Steps**:
1. Go to Paddle Dashboard → Subscriptions
2. Find test subscription (testpay2@example.com)
3. Click "Cancel subscription"
4. Confirm cancellation
5. **Expected**: Paddle sends `subscription.canceled` webhook
6. Check logs:
   ```bash
   railway logs | grep -i "canceled"
   ```
7. Verify user downgraded:
   ```bash
   railway run cat /data/users.json | grep -A5 "testpay2"
   ```
8. **Expected**:
   ```json
   {
     "is_premium": false,
     "daily_scans_left": 3,
     "paddle_subscription_id": null
   }
   ```
9. Login as that user
10. **Expected**: Back to "3 scans left"

**Pass Criteria**: Cancellation webhook processed, user downgraded

---

### Test 8: Failed Payment (Decline Card)

**Objective**: Handle payment failures gracefully

**Steps**:
1. Trigger paywall with new user
2. Click "Upgrade to Premium"
3. Enter DECLINE test card:
   - **Card**: `4000 0000 0000 0002`
   - **Exp**: `12/27`
   - **CVV**: `123`
4. **Expected**: 
   - Payment declined
   - Error message shown
   - User remains on free tier
5. Close checkout
6. **Expected**: Header still shows "0 scans left"
7. User is NOT upgraded

**Pass Criteria**: Failed payment doesn't create premium access

---

### Test 9: Mobile Responsiveness

**Objective**: Ensure payment works on mobile

**Steps**:
1. Open app on mobile device (or Chrome DevTools mobile view)
2. Register new user
3. Trigger paywall
4. Click "Upgrade to Premium"
5. **Expected**: 
   - Checkout overlay is mobile-friendly
   - All fields are tappable
   - Payment form is readable
   - No horizontal scroll
6. Complete payment with test card
7. **Expected**: Success on mobile

**Pass Criteria**: Full payment flow works on mobile

---

### Test 10: Webhook Signature (Production)

**Objective**: Verify webhook security works

⚠️ **Only test after enabling signature verification!**

**Steps**:
1. Enable signature verification in `main.py` (uncomment lines 1489-1496)
2. Set proper `PADDLE_WEBHOOK_SECRET` in Railway
3. Deploy changes
4. Make test payment
5. Check logs:
   ```bash
   railway logs | grep webhook
   ```
6. **Expected**: `POST /webhooks/paddle HTTP/1.1" 200 OK`
7. **If 401**: Signature mismatch, check webhook secret

**With Invalid Secret:**
1. Set wrong webhook secret: `railway variables set PADDLE_WEBHOOK_SECRET="wrong"`
2. Make payment
3. **Expected**: `POST /webhooks/paddle HTTP/1.1" 401 Unauthorized`
4. User NOT upgraded (security working!)

**Pass Criteria**: Valid signature = 200, Invalid = 401

---

## Edge Cases to Test

### Test 11: Concurrent Requests
- Multiple users upgrade simultaneously
- **Expected**: All webhooks process correctly

### Test 12: Duplicate Webhooks
- Paddle may send same webhook twice
- **Expected**: Idempotent (no double-upgrade issues)

### Test 13: Partial Payment
- User closes checkout mid-payment
- **Expected**: No charge, user stays free tier

### Test 14: Expired Session
- JWT token expires during checkout
- **Expected**: Still upgrades after payment (webhook uses email)

### Test 15: Network Failure
- Simulate webhook failure (turn off Railway)
- **Expected**: Paddle retries webhook later

---

## Performance Tests

### Load Test - Usage Checking
```bash
# Simulate 100 concurrent scan requests
for i in {1..100}; do
  curl -X POST "$BASE_URL/analyze" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@test_homework.jpg" &
done
wait
```

**Expected**: All requests complete, counter decrements correctly

---

## Monitoring & Alerts

### Key Metrics to Track

**Daily Monitoring:**
```bash
# Total users
railway run cat /data/users.json | grep -c username

# Premium users
railway run cat /data/users.json | grep -c '"is_premium": true'

# Failed webhooks (should be 0)
railway logs --since 24h | grep -c '"401.*webhook"'
```

**Paddle Dashboard:**
- Active subscriptions count
- Monthly Recurring Revenue (MRR)
- Churn rate
- Failed payments

### Set Up Alerts

**Railway (if available):**
- Alert on webhook 401 errors
- Alert on 5xx server errors
- Alert on high CPU usage

**Paddle Dashboard:**
- Email on failed payment
- Email on subscription canceled
- Weekly revenue summary

---

## Troubleshooting Guide

### Issue: Webhook Returns 401
**Cause**: Signature verification failing
**Fix**: 
1. Get correct webhook secret from Paddle
2. Update Railway: `railway variables set PADDLE_WEBHOOK_SECRET="pdl_ntfn_..."`
3. Redeploy

### Issue: User Not Upgraded After Payment
**Cause**: Webhook not finding user
**Check Logs**:
```bash
railway logs | grep -i "looking for user"
```
**Fix**: Ensure `custom_data.user_id` matches username exactly

### Issue: Checkout Won't Open
**Cause**: Invalid client token or price ID
**Fix**:
1. Verify token in `static/app.js`
2. Check price ID matches Paddle Dashboard
3. Ensure sandbox/production mode matches

### Issue: Scans Not Decrementing
**Cause**: Frontend not calling API correctly
**Check**: Browser console for errors
**Fix**: Verify `fetchUserStatus()` called after each analysis

---

## Before Going Live Checklist

Production Pre-Flight:
- [ ] Switch Paddle to live mode
- [ ] Update PADDLE_CLIENT_TOKEN (live token)
- [ ] Update PADDLE_PRICE_ID (live price)
- [ ] Enable webhook signature verification
- [ ] Set PADDLE_WEBHOOK_SECRET (live secret)
- [ ] Remove `Paddle.Environment.set('sandbox')`
- [ ] Test with real $0.01 payment
- [ ] Run `./test_payments.sh`
- [ ] Verify webhook 200 OK
- [ ] Test cancellation flow
- [ ] Set up monitoring alerts
- [ ] Document support process
- [ ] Test on mobile devices
- [ ] Have rollback plan ready

---

## Test Schedule

**Before Each Deployment:**
- Run `./test_payments.sh`
- Manual Test 1 (Free Tier)
- Manual Test 3 (Payment Flow)

**Weekly:**
- All Manual Tests 1-9
- Check Paddle Dashboard metrics
- Review failed payments

**Monthly:**
- Full regression (all tests)
- Load testing
- Security audit
- Review customer feedback

---

Last Updated: January 24, 2026
Test Suite Version: 1.0
