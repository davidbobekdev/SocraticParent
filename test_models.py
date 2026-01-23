#!/usr/bin/env python3
"""
Test script to verify which Gemini models are available
"""
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ No GEMINI_API_KEY found in environment")
    exit(1)

client = genai.Client(api_key=api_key)

print("🔍 Testing available Gemini models...\n")

# Models to test
models_to_test = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite", 
    "gemini-flash-latest",
    "gemini-3-flash",
]

for model_name in models_to_test:
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Hello, respond with OK"
        )
        print(f"✅ {model_name}: WORKING")
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            print(f"❌ {model_name}: NOT FOUND")
        elif "429" in error_msg:
            print(f"⚠️  {model_name}: QUOTA EXCEEDED (but exists)")
        else:
            print(f"❌ {model_name}: ERROR - {error_msg[:100]}")

print("\n✅ Test complete!")
