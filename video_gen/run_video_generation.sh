#!/bin/bash
#
# Guided Homework - Video Generation Pipeline
# Orchestration script for generating promotional videos using Vertex AI Veo
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="/home/davidbobek/SocraticParent/media/videos"

echo "=============================================="
echo "  GUIDED HOMEWORK - VIDEO GENERATION"
echo "=============================================="
echo ""
echo "Project: $PROJECT_DIR"
echo "Script:  $SCRIPT_DIR"
echo "Output:  $OUTPUT_DIR"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"
echo "✓ Output directory ready"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed"
    exit 1
fi
echo "✓ Python3 found"

# Install dependencies if needed
echo ""
echo "Installing/checking dependencies..."
pip3 install requests --quiet 2>/dev/null || pip install requests --quiet
echo "✓ Dependencies ready"

# Run video generation
echo ""
echo "Starting video generation..."
echo "This may take several minutes per video..."
echo ""

cd "$SCRIPT_DIR"
python3 generate_videos.py

# Check results
echo ""
echo "=============================================="
echo "  CHECKING RESULTS"
echo "=============================================="

if [ -d "$OUTPUT_DIR" ]; then
    VIDEO_COUNT=$(find "$OUTPUT_DIR" -name "*.mp4" 2>/dev/null | wc -l)
    echo "Videos generated: $VIDEO_COUNT"
    
    if [ "$VIDEO_COUNT" -gt 0 ]; then
        echo ""
        echo "Generated videos:"
        ls -lh "$OUTPUT_DIR"/*.mp4 2>/dev/null || echo "No MP4 files found"
    fi
    
    if [ -f "$OUTPUT_DIR/generation_log.json" ]; then
        echo ""
        echo "Generation log saved to: $OUTPUT_DIR/generation_log.json"
    fi
fi

echo ""
echo "=============================================="
echo "  DONE"
echo "=============================================="
