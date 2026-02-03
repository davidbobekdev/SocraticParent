# Google OAuth Setup Guide

## Quick Setup Steps

### 1. Go to Google Cloud Console
Visit: https://console.cloud.google.com/

### 2. Create or Select a Project
- Click the project dropdown at the top
- Click "New Project" or select existing
- Name it something like "Socratic Parent"

### 3. Enable the Google+ API (optional, but recommended)
- Go to "APIs & Services" > "Library"
- Search for "Google+ API" and enable it

### 4. Create OAuth Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen first:
   - User Type: **External**
   - App name: **Socratic Parent**
   - User support email: your email
   - Developer contact: your email
   - Click "Save and Continue" through the scopes (no changes needed)
   - Add your email as a test user
   - Click "Save and Continue"

### 5. Create OAuth Client ID
1. Application type: **Web application**
2. Name: **Socratic Parent Web**
3. Authorized JavaScript origins:
   - `https://socratesparent-production.up.railway.app`
   - `http://localhost:8000` (for local testing)
4. Authorized redirect URIs:
   - `https://socratesparent-production.up.railway.app`
   - `http://localhost:8000` (for local testing)
5. Click "Create"

### 6. Copy the Client ID
You'll get something like: `1234567890-abcdefg.apps.googleusercontent.com`

### 7. Add to Railway Environment Variables
1. Go to your Railway project dashboard
2. Click on your service
3. Go to "Variables" tab
4. Add: `GOOGLE_CLIENT_ID` = `your-client-id-here`
5. Redeploy

## Testing
1. Visit your login page
2. Click "Continue with Google"
3. Sign in with a Google account
4. You should be redirected to the app

## Troubleshooting

### "Access blocked" error
- Make sure your domain is in the authorized JavaScript origins
- Make sure your Google Cloud project is in production mode (not testing)

### Button doesn't appear
- Check browser console for errors
- Verify the GOOGLE_CLIENT_ID environment variable is set

### "Invalid client" error
- Double-check the client ID is correct
- Make sure there are no extra spaces
