#!/usr/bin/env python3
"""
Test the AI prompt and response parsing
"""
import os
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv
import PIL.Image
import io

load_dotenv()

async def test_ai_analysis():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ No GEMINI_API_KEY found")
        return
    
    print("✅ API Key found")
    print("🔍 Testing AI analysis...")
    
    # Create a simple test image (white square with "2+2=?" text)
    img = PIL.Image.new('RGB', (400, 200), color='white')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_data = img_byte_arr.getvalue()
    
    client = genai.Client(api_key=api_key)
    
    prompt = """You are an expert tutor helping students learn step-by-step. Analyze this homework problem and create a structured learning experience.

Provide your response in EXACTLY this format:

**Subject & Topic:** [Brief description]

**The Problem:**
[Clearly state what needs to be solved]

**Step 1: Understanding**
[Explain what we're looking at and what we need to find]

**Step 2: Identify the Rules**
[What mathematical rules or concepts apply here?]

**Step 3: Set Up**
[How do we organize the problem? What's the first thing to do?]

**Step 4: Solve Part 1**
[First calculation or logical step with explanation]

**Step 5: Solve Part 2**
[Second calculation or logical step with explanation]

**Step 6: Final Answer**
[Complete the solution and state the answer clearly]

**Practice Question:**
[A similar but slightly different problem for them to try]

Keep each step clear, concise, and encouraging. Use simple language appropriate for students."""
    
    try:
        image_part = types.Part.from_bytes(
            data=img_data,
            mime_type='image/jpeg'
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, image_part]
        )
        
        print("\n" + "="*60)
        print("AI RESPONSE:")
        print("="*60)
        print(response.text)
        print("="*60)
        
        # Test parsing
        lines = response.text.split('\n')
        steps = []
        for line in lines:
            if line.strip().startswith('**Step'):
                steps.append(line.strip())
        
        print(f"\n✅ Found {len(steps)} steps")
        for step in steps:
            print(f"  - {step}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai_analysis())
