# API Key Rotation Setup Guide

## Overview
The system now supports multiple Gemini API keys to handle the 20 requests/day limit on free tier accounts.

## How It Works
- Each free Gemini API key gets **20 requests per day**
- System automatically rotates between keys when one reaches its limit (set at 18 for safety)
- Usage tracking resets daily at midnight
- With 10 keys, you get **~180 requests/day** total

## Setup Instructions

### Option 1: Numbered Keys (Recommended)
Set environment variables with numbered suffixes:

```bash
GEMINI_API_KEY_1=your_first_key_here
GEMINI_API_KEY_2=your_second_key_here
GEMINI_API_KEY_3=your_third_key_here
# ... up to however many you want
GEMINI_API_KEY_10=your_tenth_key_here
```

### Option 2: Single Key Fallback
If you only have one key initially:
```bash
GEMINI_API_KEY=your_single_key_here
```

## Getting Multiple API Keys

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create a new project for each API key
3. Generate API key for each project
4. Each project gets its own 20/day limit

**Note:** Google allows multiple projects per account. You can also use different Google accounts if needed.

## For Production Deployment

### Railway
```bash
railway variables set GEMINI_API_KEY_1="key1"
railway variables set GEMINI_API_KEY_2="key2"
# etc...
```

### Docker / Docker Compose
Add to your `docker-compose.yml`:
```yaml
environment:
  - GEMINI_API_KEY_1=your_key_1
  - GEMINI_API_KEY_2=your_key_2
  - GEMINI_API_KEY_3=your_key_3
  # ... add more as needed
```

### .env File (Local Development)
```bash
# Add to .env file
GEMINI_API_KEY_1=AIza...
GEMINI_API_KEY_2=AIza...
GEMINI_API_KEY_3=AIza...
GEMINI_API_KEY_4=AIza...
GEMINI_API_KEY_5=AIza...
GEMINI_API_KEY_6=AIza...
GEMINI_API_KEY_7=AIza...
GEMINI_API_KEY_8=AIza...
GEMINI_API_KEY_9=AIza...
GEMINI_API_KEY_10=AIza...
```

## Monitoring Usage

### Check Status via API
```bash
curl https://your-app.railway.app/api/test
```

Response includes:
```json
{
  "status": "success",
  "api_keys_loaded": 10,
  "api_key_available": true,
  "total_requests_remaining": 152
}
```

### Usage Tracking
- Usage data is stored in `api_key_usage.json` in your DATA_DIR
- Automatically resets at midnight
- Each key tracks usage independently

## How the Rotation Works

1. **Request comes in** → System checks which keys have capacity
2. **Selects first available key** → Uses it for the API call
3. **Records usage** → Increments counter for that key
4. **Key hits limit (18/20)** → Automatically moves to next key
5. **All keys exhausted** → Returns error message to user
6. **Next day** → All counters reset to 0

## Upgrading to Paid Tier

When you're ready to scale:
1. Upgrade one project to pay-as-you-go in Google Cloud Console
2. That key gets much higher limits (1500+ RPD)
3. System will automatically use it first
4. Cost: ~$0.075 per 1M input tokens (very affordable)

## Recommended Strategy

### MVP Phase (Now)
- Start with 5-10 free API keys
- Monitor usage daily
- ~100-180 requests/day capacity

### Growth Phase
- Add more free keys as needed
- Or upgrade 1-2 keys to paid tier
- Mix of free + paid keys works great

### Production Phase
- Upgrade to full paid tier
- Much simpler management
- ~$10-20/month for moderate traffic

## Troubleshooting

### "All API keys have reached their daily limit"
- Wait until midnight UTC for reset
- Or add more API keys to rotation
- Or upgrade one key to paid tier

### Keys not loading
- Check environment variable names (must be `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, etc.)
- Verify no spaces in variable names
- Check application logs for "Loaded X API key(s)" message

### Usage not resetting
- Usage file: `api_key_usage.json` in DATA_DIR
- Resets automatically at midnight
- Can manually delete file to force reset (not recommended)

## Cost Comparison

### Free Tier (Current)
- 10 keys × 20 requests = 200 requests/day
- Cost: $0
- Good for: MVP, testing, low traffic

### Paid Tier (Upgrade)
- 1 key = 1500+ requests/day (or more based on tier)
- Cost: ~$7-15/month for typical usage
- Good for: Production, scaling, reliability

## Questions?

Check the logs for rotation status:
```bash
railway logs
# or
docker-compose logs -f app
```

You'll see messages like:
- "🔑 Loaded 10 API key(s) for rotation"
- "📊 API Key 3 usage: 15/18"
- "📅 New day detected, resetting API key usage counters"
