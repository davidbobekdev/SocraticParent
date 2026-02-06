#!/bin/bash
# Video Generation with Gemini API Key

# Check if API key provided
if [ -z "$1" ]; then
    echo "Usage: $0 <GEMINI_API_KEY>"
    echo ""
    echo "Get a free API key from: https://aistudio.google.com/"
    echo ""
    echo "Example:"
    echo "  ./run_with_api_key.sh your_api_key_here"
    exit 1
fi

API_KEY="$1"

echo "Starting video storyboard generation..."
echo "API Key: ${API_KEY:0:15}..."
echo ""

cd /home/davidbobek/SocraticParent

python3 video_gen/generate_videos.py --api-key "$API_KEY"

echo ""
echo "Check /home/davidbobek/SocraticParent/media/videos/ for storyboard files"
