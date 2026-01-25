# Railway Persistent Storage Setup

## What This Fixes
- Users and data now persist across deployments
- No need to re-register after each update

## Setup Steps

### 1. Add Volume in Railway Dashboard
1. Go to your Railway project: https://railway.app/project/6c308298-0486-410d-b2ca-a7548eb55519
2. Click on your "SocratesParent" service
3. Go to the **"Variables"** tab
4. Click **"+ New Variable"**
5. Add: `DATA_DIR=/data`
6. Go to the **"Settings"** tab
7. Scroll down to **"Volumes"**
8. Click **"+ New Volume"**
9. Mount Path: `/data`
10. Click "Add"

### 2. Redeploy
After adding the volume, the next deployment will use persistent storage.

## How It Works
- `users.json` is now stored in `/data/users.json`
- Railway volumes persist across deployments
- Your user accounts survive updates!

## Alternative: Using Railway CLI
```bash
# In your Railway dashboard, you can also add volume via CLI:
railway volume add /data
railway variables set DATA_DIR=/data
```
