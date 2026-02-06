# Guided Homework - Video Generation Guide

## Current Status
✅ Video generation pipeline is ready  
❌ Billing not enabled on GCP project (needed for Vertex AI Veo 2)  
✅ OAuth authentication working

## What You Can Do Now

### Generate Storyboards (Free - Requires Gemini API Key)
```bash
# Get your free API key from: https://aistudio.google.com/
python3 video_gen/generate_videos.py --api-key YOUR_GEMINI_API_KEY
```

This will generate:
- Detailed visual storyboards for all 5 scenes
- Frame-by-frame descriptions
- Color palettes and mood suggestions
- Markdown files in `/media/videos/`

### Generate Full Videos (Paid - Requires GCP Billing)
```bash
# 1. Enable billing: https://console.cloud.google.com/billing/enable?project=socratesparent
# 2. Run the script (you already logged in with gcloud auth)
python3 video_gen/generate_videos.py
```

This will generate:
- 8-second Pixar-style 3D animated videos
- One MP4 file per scene
- Saved in `/media/videos/`

## Scene Details

The pipeline includes 5 promotional video scenes:

1. **Tornado of Chaos** - Chaotic papers → Phone vacuums → Clean homework
2. **Math Arrow Attack** - Attacking equations → Phone shield → Solutions
3. **Fog of Confusion** - Lost in fog → Phone spotlight → Clear path
4. **Magnetic Order** - Scattered mess → Phone magnetizes → Perfect order
5. **Monster Under the Desk** - Paper monster → Phone laser → Victory

## Technical Setup

### Project ID
- GCP Project: `socratesparent`
- Already configured in gcloud

### API Keys Location
- Gemini API: https://aistudio.google.com/
- Vertex AI: Enabled (requires billing)

### Output Directory
```
/home/davidbobek/SocraticParent/media/videos/
```

## Script Features

- **Multi-Auth Support**: Gemini API key or gcloud OAuth
- **Fallback Methods**: Tries Veo 2 → Imagen → Gemini storyboards
- **Logging**: Saves results to `generation_log.json`
- **Selective Generation**: `python3 generate_videos.py --scene scene_1`

## Troubleshooting

### Error: "Billing not enabled"
→ Enable billing: https://console.cloud.google.com/billing/enable?project=socratesparent

### Error: "No authentication"
→ Get Gemini API key from https://aistudio.google.com/
→ Or run: `/opt/google-cloud-sdk/bin/gcloud auth login`

### Error: "Scene not found"
→ Check available scenes: `python3 video_gen/generate_videos.py --help`

## Cost Estimates

- **Gemini API (Storyboards)**: Free tier available
- **Veo 2 (Videos)**: ~$10 per video (with free trial credits)
- **Imagen 3 (Keyframes)**: Included in Vertex AI pricing

## Next Steps

1. Get a free Gemini API key
2. Generate storyboards to review concepts
3. Enable billing when ready for full video generation
4. Review videos and integrate into app

---
**Last Updated:** February 4, 2026
