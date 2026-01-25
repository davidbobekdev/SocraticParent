# Paddle Billing Configuration Guide

## Environment Variables Required

Add these environment variables to your Railway deployment:

### 1. PADDLE_WEBHOOK_SECRET
- **Description**: Used to verify webhook signatures from Paddle
- **Location**: Paddle Dashboard → Developer Tools → Notifications → Webhook endpoint → Signing secret
- **Example**: `pdl_ntfn_01hqn5...`
- **Required**: YES

### 2. PADDLE_CLIENT_TOKEN
- **Description**: Client-side token for Paddle.js initialization
- **Location**: Paddle Dashboard → Developer Tools → Authentication → Client-side tokens
- **Example**: `test_1234567890abcdef` (sandbox) or `live_1234567890abcdef` (production)
- **Required**: YES
- **Note**: Update in `static/index.html` in the Paddle.Initialize() call

### 3. PADDLE_PRICE_ID
- **Description**: The price ID for your monthly subscription
- **Location**: Paddle Dashboard → Catalog → Products → Select product → Prices → Copy ID
- **Example**: `pri_01hqn5...` (sandbox) or production price ID
- **Required**: YES

## Paddle Dashboard Setup

### 1. Create Product
1. Go to Paddle Dashboard → Catalog → Products
2. Click "Create Product"
3. Name: "Socratic Parent Premium"
4. Description: "Unlimited homework analyses"
5. Save

### 2. Create Price
1. In your product, click "Add Price"
2. Billing cycle: Monthly
3. Amount: $9.99 USD
4. Save and copy the Price ID

### 3. Configure Webhook
1. Go to Developer Tools → Notifications
2. Click "Add notification destination"
3. URL: `https://your-railway-app.up.railway.app/webhooks/paddle`
4. Select events:
   - `subscription.created`
   - `subscription.updated`
   - `subscription.canceled`
   - `subscription.expired`
5. Save and copy the Signing Secret

### 4. Get Client Token
1. Go to Developer Tools → Authentication
2. Create or copy existing Client-side token
3. For testing, use Sandbox token
4. For production, use Live token

## Railway Configuration

### Add Environment Variables

```bash
# In Railway project settings → Variables
PADDLE_WEBHOOK_SECRET=pdl_ntfn_01hqn5...
PADDLE_CLIENT_TOKEN=test_1234567890abcdef
PADDLE_PRICE_ID=pri_01hqn5...
```

### Update Paddle.js in HTML

Edit `static/index.html` and replace the token:

```javascript
Paddle.Initialize({
    token: 'YOUR_ACTUAL_CLIENT_TOKEN', // Replace this
    environment: 'sandbox' // Use 'production' for live
});
```

## Testing the Integration

### 1. Test Free Tier (No Payment Required)
```bash
# Register a new user
curl -X POST https://your-app.railway.app/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123","email":"test@example.com"}'

# Login
curl -X POST https://your-app.railway.app/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123"}'

# Make 3 analyses (should work)
# 4th analysis should return 402 with paywall

# Check user status
curl -X GET https://your-app.railway.app/api/user/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2. Test Webhook (Paddle Sandbox)
1. Use Paddle test cards: https://developer.paddle.com/concepts/payment-methods/credit-debit-card#test-card-numbers
2. Complete checkout in sandbox
3. Verify webhook received in Railway logs
4. Check user premium status updated

### 3. Test Premium Access
```bash
# After webhook processes subscription
# Try analysis - should have unlimited scans
curl -X POST https://your-app.railway.app/analyze \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@homework.jpg"
```

## Troubleshooting

### Webhook Not Received
- Check Railway logs: `railway logs`
- Verify webhook URL is correct in Paddle Dashboard
- Test webhook signature verification locally

### Invalid Signature
- Verify `PADDLE_WEBHOOK_SECRET` matches Paddle Dashboard
- Check webhook endpoint logs for signature details

### Premium Not Activating
- Check webhook event type is `subscription.created`
- Verify `paddle_subscription_id` is saved in users.json
- Look for webhook processing errors in logs

### Checkout Not Opening
- Verify `PADDLE_CLIENT_TOKEN` is correct
- Check browser console for Paddle.js errors
- Ensure environment (sandbox/production) matches token

## Production Checklist

Before going live:

- [ ] Switch from sandbox to production Paddle account
- [ ] Update `PADDLE_CLIENT_TOKEN` to production token
- [ ] Update `PADDLE_PRICE_ID` to production price
- [ ] Update `PADDLE_WEBHOOK_SECRET` to production webhook secret
- [ ] Update `environment: 'production'` in Paddle.Initialize()
- [ ] Test complete flow with real payment method
- [ ] Set up Paddle email notifications
- [ ] Configure tax settings in Paddle
- [ ] Add terms of service and privacy policy links

## Monitoring

### Check Daily Usage
```bash
# View users.json to see daily_scans_left
railway run cat /data/users.json | jq
```

### Monitor Webhooks
```bash
# Watch Railway logs for webhook events
railway logs --follow | grep "Paddle webhook"
```

### Track Subscriptions
- Paddle Dashboard → Subscriptions
- View active, canceled, and churned subscriptions
- Monitor revenue and metrics
