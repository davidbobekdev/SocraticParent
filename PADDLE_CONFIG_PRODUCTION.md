# Paddle Billing Configuration - Production Guide

## Current Configuration (Sandbox - Testing)

### Account Details
- **Vendor ID**: 46459
- **Environment**: Sandbox (Test Mode)
- **Dashboard**: https://sandbox-vendors.paddle.com

### Credentials
```bash
# Client-side token (for Paddle.js in browser)
PADDLE_CLIENT_TOKEN=test_bbb6d3dd75d2dad295bd6027fad

# Product and pricing
PADDLE_PRICE_ID=pri_01kfr8qsrd2eggamsmeazrc5kq  # $9.99/month
PRODUCT_ID=pro_01kfr8mjffqg3bt6r59hrb9wdn

# Webhook (signature verification currently DISABLED)
PADDLE_WEBHOOK_SECRET=not_configured_yet
WEBHOOK_NOTIFICATION_ID=ntfset_01kfr8x1s7sgwaqx37atzpp1mk
```

### Webhook Configuration
- **URL**: `https://socratesparent-production.up.railway.app/webhooks/paddle`
- **Events**: subscription.created, subscription.updated, subscription.canceled, subscription.expired
- **Signature Verification**: ⚠️ **DISABLED FOR TESTING** - Must enable before production!

### Test Cards (Sandbox)
```
Success:  4242 4242 4242 4242
Decline:  4000 0000 0000 0002
Exp:      Any future date (e.g., 12/27)
CVV:      Any 3 digits (e.g., 123)
Name:     Any name
```

---

## Going Live - Production Checklist

### 1. Paddle Account Setup

**Switch to Live Mode:**
1. Go to Paddle Dashboard
2. Toggle from "Test mode" to "Live mode" (top right)
3. Complete business verification if required
4. Add banking/payout details

**Create Production Product:**
1. Catalog → Products → Create Product
2. Name: "Socratic Parent Premium"
3. Description: "Unlimited AI-powered homework analysis"
4. Save product (note the product ID: `pro_xxxxx`)

**Create Production Price:**
1. In product → Add Price
2. Billing: Monthly
3. Amount: $9.99 USD
4. Save and **copy the Price ID**: `pri_xxxxx` ← YOU NEED THIS

### 2. Get Production Tokens

**Client-Side Token:**
1. Developer Tools → Authentication
2. Click "Client-side tokens" tab
3. Generate new token
4. Name: "Socratic Parent Production"
5. **Copy token**: `live_xxxxx` ← YOU NEED THIS

**API Key (optional, for backend):**
1. Developer Tools → Authentication
2. "API keys" tab
3. Generate key with "All read, All write" permissions
4. **Copy key**: `pdl_live_apikey_xxxxx`

**Webhook Secret:**
1. Developer Tools → Notifications
2. Click your webhook destination
3. **Copy "Secret key"**: `pdl_ntfn_xxxxx` ← YOU NEED THIS

### 3. Configure Production Webhook

**Update Webhook URL:**
1. Developer Tools → Notifications
2. Edit your webhook destination
3. URL: `https://socratesparent-production.up.railway.app/webhooks/paddle`
4. Ensure events selected:
   - ✅ subscription.created
   - ✅ subscription.updated
   - ✅ subscription.canceled
   - ✅ subscription.expired
5. Save and copy new webhook secret

**Set Default Checkout URLs:**
1. Checkout → Checkout settings
2. Success URL: `https://socratesparent-production.up.railway.app/app?upgraded=true`
3. Cancel URL: `https://socratesparent-production.up.railway.app/app`
4. Save

### 4. Update Code for Production

**File: `static/app.js` (line ~153)**
```javascript
// REMOVE THIS LINE:
// Paddle.Environment.set('sandbox');

// Keep only:
Paddle.Initialize({
    token: 'live_xxxxx',  // ← Update with production token
    eventCallback: function(data) {
        // ... rest of code
    }
});
```

**File: `main.py` (lines 1487-1494)**
```python
# UNCOMMENT signature verification:
webhook_secret = os.getenv("PADDLE_WEBHOOK_SECRET", "")
if webhook_secret:
    computed_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(computed_signature, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
```

### 5. Update Railway Environment Variables

```bash
railway variables set PADDLE_CLIENT_TOKEN="live_xxxxx"
railway variables set PADDLE_PRICE_ID="pri_xxxxx"
railway variables set PADDLE_WEBHOOK_SECRET="pdl_ntfn_xxxxx"
```

### 6. Deploy to Production

```bash
# Commit code changes
git add static/app.js main.py
git commit -m "Switch to Paddle production mode"
git push origin main

# Deploy to Railway
railway up --detach

# Verify deployment
railway logs --tail 50
```

### 7. Production Testing

**Test Flow:**
1. Register new test user (use real email)
2. Use 3 free scans
3. Trigger paywall on 4th scan
4. Click "Upgrade to Premium"
5. **Use REAL payment method** (will charge $9.99)
6. Complete payment
7. Verify webhook received: `railway logs | grep -i webhook`
8. Refresh page → Should show "∞ Unlimited"
9. Test unlimited scans work
10. Verify you can cancel in Paddle Dashboard

**What to Check:**
- ✅ Checkout opens without errors
- ✅ Payment processes successfully
- ✅ Webhook returns 200 OK (not 401)
- ✅ User status updates to premium
- ✅ Header shows "∞ Unlimited"
- ✅ No paywall appears
- ✅ Unlimited analyses work
- ✅ Subscription appears in Paddle Dashboard

### 8. Monitor Production

**Check Active Subscriptions:**
```bash
railway run cat /data/users.json | grep '"is_premium": true' -c
```

**Monitor Webhooks:**
```bash
railway logs --follow | grep -i webhook
```

**Paddle Dashboard Monitoring:**
- Transactions → View all payments
- Subscriptions → Active subscriptions
- Revenue → MRR, churn rate
- Customers → Total customers

---

## Security Notes

### ⚠️ CRITICAL - Before Going Live:

1. **Enable Webhook Signature Verification**
   - Currently disabled for testing (line 1487 in main.py)
   - MUST uncomment before production
   - Validates webhooks actually come from Paddle

2. **Use HTTPS Only**
   - Railway provides HTTPS automatically
   - Never use HTTP for webhooks

3. **Secure Environment Variables**
   - Never commit tokens to git
   - Use Railway's secure variable storage
   - Rotate tokens if exposed

4. **Rate Limiting** (optional but recommended)
   - Add rate limiting to webhook endpoint
   - Prevents abuse/DoS attacks

---

## Rollback Plan

If issues occur in production:

```bash
# Quick rollback to sandbox
railway variables set PADDLE_CLIENT_TOKEN="test_bbb6d3dd75d2dad295bd6027fad"
railway variables set PADDLE_PRICE_ID="pri_01kfr8qsrd2eggamsmeazrc5kq"

# Restore code (if committed)
git revert HEAD
railway up --detach
```

---

## Support & Documentation

- **Paddle Docs**: https://developer.paddle.com/
- **Test Cards**: https://developer.paddle.com/concepts/payment-methods/credit-debit-card#test-card-numbers
- **Paddle Support**: Via dashboard → Help
- **Railway Docs**: https://docs.railway.app/

---

## Cost Estimates

**Paddle Fees (Standard Plan):**
- 5% + $0.50 per transaction
- On $9.99 subscription: $0.50 + 5% = $1.00 fee
- You receive: $8.99 per subscription

**Railway Costs:**
- Hobby Plan: $5/month
- Pro Plan: $20/month + usage
- Estimate: ~$10-30/month depending on traffic

**Total Monthly Costs:**
- Fixed: ~$5-30 (Railway)
- Variable: ~10% of revenue (Paddle fees)

---

Last Updated: January 24, 2026
