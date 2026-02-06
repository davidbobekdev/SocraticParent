#!/usr/bin/env python3
"""
Guided Homework - Video Generation Pipeline
Uses Google Vertex AI Veo 2 / Imagen to generate promotional videos

Usage:
  python3 generate_videos.py --api-key YOUR_GEMINI_API_KEY
  python3 generate_videos.py
  python3 generate_videos.py --scene scene_1
"""

import json
import os
import sys
import time
import base64
import argparse
import subprocess
import requests
from pathlib import Path
from datetime import datetime

# Load environment from parent .env file
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except:
    pass

# Parse CLI args
parser = argparse.ArgumentParser(description='Generate promotional videos for Guided Homework')
parser.add_argument('--api-key', '-k', help='Gemini API key')
parser.add_argument('--scene', '-s', help='Generate only specific scene (e.g., scene_1)')
args, _ = parser.parse_known_args()

# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "socratesparent")
LOCATION = "us-central1"

# Paths
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
SCENES_FILE = BASE_DIR / "scenes.json"
BASE_PROMPT_FILE = SCRIPT_DIR / "base_prompt.txt"
OUTPUT_DIR = Path("/home/davidbobek/SocraticParent/media/videos")
GCLOUD_PATH = "/opt/google-cloud-sdk/bin/gcloud"

# Get Gemini API key
def get_gemini_api_key():
    if args.api_key:
        return args.api_key
    for i in range(1, 10):
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if key and not key.startswith("your_"):
            return key
    key = os.getenv("GEMINI_API_KEY")
    if key and not key.startswith("your_"):
        return key
    return None

GEMINI_API_KEY = get_gemini_api_key()


def get_access_token():
    """Get OAuth2 access token from gcloud"""
    try:
        result = subprocess.run(
            [GCLOUD_PATH, 'auth', 'print-access-token'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            token = result.stdout.strip()
            if token and len(token) > 50:
                return token
    except:
        pass
    return None


def load_scenes():
    with open(SCENES_FILE, 'r') as f:
        return json.load(f)


def load_base_prompt():
    with open(BASE_PROMPT_FILE, 'r') as f:
        return f.read()


def format_scene_content(scene_data):
    lines = [f"SCENE: {scene_data['setting']} - {scene_data['description']}", "", "SEQUENCE:"]
    lines.extend(scene_data['sequence'])
    lines.extend(["", f"PHONE ACTION: {scene_data['phone_action']}", f"CORE MESSAGE: {scene_data['core_message']}"])
    return "\n".join(lines)


def build_full_prompt(base_prompt, scene_data):
    scene_content = format_scene_content(scene_data)
    return base_prompt.replace("{SCENE_CONTENT}", scene_content)


def generate_video(prompt, scene_name, output_path):
    """Main video generation function"""
    print(f"\n{'='*60}")
    print(f"Generating: {scene_name}")
    print(f"{'='*60}")
    
    simplified_prompt = f"""
8-second Pixar-style 3D animated video for "Guided Homework" app:

{scene_name}: A parent helps their child with homework using a magical glowing smartphone.
The phone emits magical blue and gold energy, transforming chaos into organized solutions.

Style: Pixar/Disney quality, vibrant colors, cinematic lighting, family-friendly.
Emotion: Child goes from stressed to happy. Parent is confident and heroic.

{prompt[:600]}
"""
    
    # Try Gemini API Veo 3.1 first (generates real videos!)
    if GEMINI_API_KEY:
        print("Trying Gemini API Veo 3.1 (real video generation)...")
        result = try_gemini_veo(simplified_prompt, scene_name, output_path)
        if result:
            return result
    
    # Try Vertex AI with OAuth token (backup)
    access_token = get_access_token()
    if access_token:
        print("Trying Vertex AI Veo 2...")
        result = try_vertex_ai_veo(simplified_prompt, scene_name, output_path, access_token)
        if result:
            return result
        # Try Imagen if Veo fails
        result = try_vertex_ai_imagen(simplified_prompt, scene_name, output_path, access_token)
        if result:
            return result
    
    print(f"✗ Failed - need API access for video generation")
    return None


def try_vertex_ai_veo(prompt, scene_name, output_path, access_token):
    """Try Veo 2 on Vertex AI"""
    endpoint = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/veo-2.0-generate-001:predictLongRunning"
    
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    body = {
        "instances": [{"prompt": prompt}],
        "parameters": {"aspectRatio": "9:16", "durationSeconds": 8, "sampleCount": 1}
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=body, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            if "name" in result:
                print(f"  ✓ Operation started: {result['name'][:50]}...")
                return poll_vertex_operation(result["name"], access_token, output_path)
            else:
                print(f"  Got 200 but no operation name in response")
                return None
        else:
            print(f"  Veo 2 error {response.status_code}")
            if response.status_code == 403:
                print(f"  (Permission/Billing issue)")
            return None
    except Exception as e:
        print(f"  Veo 2 exception: {type(e).__name__}")
        return None


def try_vertex_ai_imagen(prompt, scene_name, output_path, access_token):
    """Try Imagen 3 for keyframes"""
    print("  Trying Imagen 3 for keyframes...")
    endpoint = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/imagen-3.0-generate-001:predict"
    
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    frames = []
    
    frame_prompts = [
        f"Keyframe 1: Child overwhelmed by homework chaos. {prompt[:200]}. Pixar style.",
        f"Keyframe 2: Parent arrives with glowing smartphone. Superhero pose.",
        f"Keyframe 3: Happy child and parent, solved homework. Victory celebration."
    ]
    
    for i, fp in enumerate(frame_prompts):
        body = {"instances": [{"prompt": fp}], "parameters": {"sampleCount": 1, "aspectRatio": "16:9"}}
        try:
            response = requests.post(endpoint, headers=headers, json=body, timeout=120)
            if response.status_code == 200:
                result = response.json()
                predictions = result.get("predictions", [])
                if predictions and "bytesBase64Encoded" in predictions[0]:
                    frame_path = output_path.parent / f"{output_path.stem}_frame{i+1}.png"
                    with open(frame_path, 'wb') as f:
                        f.write(base64.b64decode(predictions[0]["bytesBase64Encoded"]))
                    frames.append(frame_path)
                    print(f"    ✓ Frame {i+1}")
        except:
            pass
    
    if frames:
        return create_video_from_frames(frames, output_path)
    return None


def try_gemini_veo(prompt, scene_name, output_path):
    """Generate actual video with Veo 3.1 via Gemini API"""
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Simplified prompt optimized for Veo 3.1
        video_prompt = f"""8-second Pixar-style 3D animated video for "Guided Homework" app:

{scene_name}: A parent helps their child with homework using a magical glowing smartphone.
The phone emits magical blue and gold energy, transforming chaos into organized solutions.

Style: Pixar/Disney quality CGI, vibrant colors, cinematic lighting, family-friendly.
Camera: Dynamic camera movement, close-ups of faces, wide shots showing transformation.
Audio: Uplifting orchestral music, magical sound effects.
Emotion: Child goes from stressed to happy. Parent is confident and heroic.

Action: {prompt[:400]}"""
        
        print(f"  🎬 Generating video with Veo 3.1...")
        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=video_prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio="9:16",
                resolution="720p",
                duration_seconds=8
            )
        )
        
        # Poll for completion (max 10 minutes)
        print(f"  ⏳ Waiting for video generation (this takes 1-6 minutes)...")
        max_wait = 600
        start = time.time()
        
        while not operation.done and (time.time() - start) < max_wait:
            elapsed = int(time.time() - start)
            print(f"    • Still generating... ({elapsed}s)")
            time.sleep(15)
            operation = client.operations.get(operation)
        
        if operation.done:
            # Download and save video
            output_path.parent.mkdir(parents=True, exist_ok=True)
            video = operation.response.generated_videos[0]
            
            # Save as MP4
            mp4_path = output_path.with_suffix('.mp4')
            client.files.download(file=video.video)
            video.video.save(str(mp4_path))
            
            print(f"✅ Video generated: {mp4_path.name}")
            return mp4_path
        else:
            print(f"  ⏱️  Timeout - video generation taking longer than expected")
            return None
            
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
            print(f"  Veo quota exhausted - falling back to storyboard...")
            return try_gemini_storyboard(prompt, scene_name, output_path)
        else:
            print(f"  Veo error: {type(e).__name__}: {error_str[:200]}")
            return try_gemini_storyboard(prompt, scene_name, output_path)


def try_gemini_storyboard(prompt, scene_name, output_path):
    """Generate storyboard with Gemini API (fallback)"""
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        storyboard_prompt = f"""Create a HIGHLY DETAILED 8-second animated video storyboard for a Pixar-style promotional video.

SCENE: {scene_name}

VIDEO CONCEPT:
{prompt}

Provide:
1. 2-3 sentence compelling visual summary
2. Frame-by-frame breakdown (8 frames):
   - FRAME 1 (0-1s): [Detailed visual description]
   - FRAME 2 (1-2s): [Detailed visual description]
   - ... etc to FRAME 8
3. Key visual elements to include
4. Color palette and mood
5. Recommended music style

Make it cinematic, emotional, and family-friendly."""
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=storyboard_prompt
        )
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        storyboard_path = output_path.parent / f"{output_path.stem}_storyboard.md"
        with open(storyboard_path, 'w') as f:
            f.write(f"# {scene_name} - Video Storyboard\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write(response.text)
        
        print(f"✅ Storyboard: {storyboard_path.name}")
        return storyboard_path
        
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
            print(f"  Gemini quota exhausted - generating text fallback...")
            return create_fallback_storyboard(prompt, scene_name, output_path)
        else:
            print(f"  Gemini error: {type(e).__name__}: {error_str[:200]}")
            return None


def create_fallback_storyboard(prompt, scene_name, output_path):
    """Create a basic storyboard without API call (for quota exhaustion)"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        storyboard_path = output_path.parent / f"{output_path.stem}_storyboard.md"
        
        # Extract frames from the base prompt
        lines = prompt.split('\n')
        frames_text = ""
        for i, line in enumerate(lines):
            if 'FRAME' in line or '(0-' in line or '(1-' in line:
                frames_text += line + "\n"
        
        with open(storyboard_path, 'w') as f:
            f.write(f"# {scene_name} - Video Storyboard\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n")
            f.write(f"**Status:** Fallback (API quota exhausted)\n\n")
            f.write("## Visual Summary\n")
            f.write(f"A Pixar-style 8-second promotional video for Guided Homework showing {scene_name.lower()}.\n\n")
            f.write("## Frame-by-Frame Breakdown\n\n")
            
            # Basic frame structure
            frame_descriptions = [
                "Child faces challenge, overwhelmed and stressed",
                "Parent enters with glowing smartphone (magical effect)",
                "Phone emits blue and gold magical energy",
                "Magic transforms the problem into understanding",
                "Parent guides child with confidence",
                "Child gains clarity and confidence",
                "Both celebrate the solved problem",
                "Final shot: confident smile, ready to learn more"
            ]
            
            for i, desc in enumerate(frame_descriptions, 1):
                f.write(f"**Frame {i} (0-{i}s):** {desc}\n")
            
            f.write("\n## Visual Elements\n")
            f.write("- Magical phone with blue and gold energy effects\n")
            f.write("- Pixar-quality 3D animation\n")
            f.write("- Warm, supportive parent-child interaction\n")
            f.write("- Clear transformation from chaos to clarity\n\n")
            f.write("## Color Palette\n")
            f.write("- Primary: Blue, Gold, Warm White\n")
            f.write("- Secondary: Orange (warm light), Purple (magic)\n")
            f.write("- Mood: Hopeful, Supportive, Magical\n\n")
            f.write("## Music Suggestion\n")
            f.write("- Uplifting orchestral soundtrack\n")
            f.write("- Builds from gentle to triumphant\n")
            f.write("- Family-friendly, inspirational\n")
        
        print(f"⚠️  Storyboard (fallback): {storyboard_path.name}")
        return storyboard_path
        
    except Exception as e:
        print(f"  Fallback error: {type(e).__name__}")
        return None


def poll_vertex_operation(operation_name, access_token, output_path, max_wait=600):
    """Poll Vertex AI operation"""
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/{operation_name}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"  Polling operation (max {max_wait}s)...")
    start = time.time()
    
    while time.time() - start < max_wait:
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get("done"):
                    return process_video_response(result.get("response", {}), output_path)
                progress = result.get('metadata', {}).get('progressPercent', 0)
                elapsed = int(time.time() - start)
                print(f"  Progress: {progress}% ({elapsed}s)")
        except:
            pass
        time.sleep(15)
    
    print(f"  ⏱️  Timeout - check status later")
    return None


def process_video_response(result, output_path):
    """Extract and save video"""
    video_data = None
    
    for key in ["predictions", "generatedVideos"]:
        if key in result:
            for item in result[key]:
                if isinstance(item, dict):
                    video_data = item.get("bytesBase64Encoded") or item.get("video", {}).get("bytesBase64Encoded")
                    if video_data:
                        break
    
    if video_data:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(base64.b64decode(video_data))
        print(f"✅ Video saved: {output_path.name}")
        return output_path
    
    return None


def create_video_from_frames(frame_paths, output_path):
    """Create video from frames with ffmpeg"""
    try:
        subprocess.run(['which', 'ffmpeg'], capture_output=True, check=True)
        
        concat_file = output_path.parent / "concat.txt"
        with open(concat_file, 'w') as f:
            for fp in frame_paths:
                f.write(f"file '{fp}'\nduration 2.67\n")
        
        subprocess.run(
            ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_file),
             '-vf', 'scale=1920:1080,fps=24', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
             str(output_path)],
            capture_output=True, timeout=60
        )
        
        if output_path.exists():
            print(f"✅ Video: {output_path.name}")
            return output_path
    except:
        pass
    
    return frame_paths[0] if frame_paths else None


def main():
    print("="*60)
    print("GUIDED HOMEWORK - VIDEO GENERATION")
    print("="*60)
    print(f"Project: {PROJECT_ID}")
    
    # Check auth
    print("\nAuthentication:")
    if GEMINI_API_KEY:
        print(f"  ✓ Gemini API key: {GEMINI_API_KEY[:20]}...")
    else:
        print("  ✗ No Gemini API key")
    
    access_token = get_access_token()
    if access_token:
        print(f"  ✓ OAuth token available")
    else:
        print("  ✗ No OAuth token")
    
    if not GEMINI_API_KEY and not access_token:
        print("\n⚠️  Need authentication:")
        print("  Get API key: https://aistudio.google.com/")
        print("  Or: gcloud auth login")
        return False
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load scenes
    scenes = load_scenes()
    base_prompt = load_base_prompt()
    
    if args.scene:
        if args.scene in scenes:
            scenes = {args.scene: scenes[args.scene]}
        else:
            print(f"Error: Scene '{args.scene}' not found")
            return False
    
    print(f"\nGenerating {len(scenes)} scene(s)...\n")
    
    # Generate
    results = []
    for scene_key, scene_data in scenes.items():
        scene_name = scene_data.get('title', scene_key)
        full_prompt = build_full_prompt(base_prompt, scene_data)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = OUTPUT_DIR / f"{scene_key}_{scene_name.replace(' ', '_')}_{timestamp}.mp4"
        
        result = generate_video(full_prompt, scene_name, output_file)
        results.append({
            "scene": scene_key,
            "name": scene_name,
            "file": str(result) if result else None,
            "status": "success" if result else "failed"
        })
        time.sleep(2)
    
    # Summary
    print("\n" + "="*60)
    success = sum(1 for r in results if r["status"] == "success")
    print(f"RESULTS: {success}/{len(results)} completed")
    print(f"Output: {OUTPUT_DIR}")
    
    # Save log
    with open(OUTPUT_DIR / "generation_log.json", 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "project": PROJECT_ID,
            "results": results
        }, f, indent=2)
    
    return success > 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
