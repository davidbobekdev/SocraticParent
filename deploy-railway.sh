#!/bin/bash
# Automated Railway deployment script

set -e

echo "🚀 Starting Railway deployment..."

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    bash -c "$(curl -fsSL https://railway.app/install.sh)"
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "⚠️  Not logged in to Railway. Please login:"
    railway login
fi

# Deploy
echo "📦 Deploying to Railway..."
railway up --detach

echo "✅ Deployment complete!"
echo "🌐 Your app: https://socratesparent-production.up.railway.app/"
