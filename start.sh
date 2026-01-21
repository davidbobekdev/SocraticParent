#!/bin/bash
# Quick start script for Socratic Parent

set -e

echo "🎓 Socratic Parent - Setup"
echo "=========================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo ""
    echo "📝 Please edit .env and add your GEMINI_API_KEY"
    echo "   Get your API key from: https://makersuite.google.com/app/apikey"
    echo ""
    read -p "Press Enter once you've added your API key..."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "🐳 Starting Docker containers..."
docker compose up -d --build

echo ""
echo "✅ Socratic Parent is starting!"
echo ""
echo "📍 Access the application at: http://localhost:8000"
echo "🏥 Health check: http://localhost:8000/health"
echo ""
echo "📊 View logs with: docker compose logs -f"
echo "🛑 Stop with: docker compose down"
echo ""
