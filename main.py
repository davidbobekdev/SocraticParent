"""
Socratic Parent Backend - FastAPI Application
The "Anti-Homework-Solver" for the 2026 AI-Saturated Era
"""

import os
import base64
import uuid
import time
from io import BytesIO
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Session Management
sessions = {}  # {session_id: {"created": timestamp, "key": api_key}}
SESSION_TIMEOUT = 24 * 60 * 60  # 24 hours

def create_session():
    """Create a new session with a unique ID"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "created": time.time(),
        "key": os.getenv("GEMINI_API_KEY")
    }
    return session_id

def get_session_key(session_id: str) -> Optional[str]:
    """Get API key for a session, creating one if needed"""
    if not session_id or session_id not in sessions:
        return None
    
    session = sessions[session_id]
    # Check if session expired
    if time.time() - session["created"] > SESSION_TIMEOUT:
        del sessions[session_id]
        return None
    
    return session["key"]

def cleanup_expired_sessions():
    """Remove expired sessions"""
    current_time = time.time()
    expired = [sid for sid, s in sessions.items() 
               if current_time - s["created"] > SESSION_TIMEOUT]
    for sid in expired:
        del sessions[sid]

# Initialize FastAPI app
app = FastAPI(
    title="Socratic Parent API",
    description="Pedagogical Firewall: Turning homework into meaningful learning moments",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Google Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None

# System prompt for the AI "Silent Coach"
SYSTEM_PROMPT = """You are a master educator. You are looking at a student's homework through a parent's eyes.

YOUR TWO-PART MISSION:
PART 1 - SOCRATIC QUESTIONS (Never solve directly):
- DO NOT give the final answer in the questions
- Guide with questions that activate thinking

PART 2 - SOLUTION STEPS (Complete calculation with actual work):
- SOLVE the problem completely with real calculations
- Show ALL the work with actual numbers
- Break down into clear, numbered steps
- Include every calculation detail (e.g., "5 + 3 = 8", "12 ÷ 4 = 3")
- These are for "last resort" viewing only, so be thorough

Provide a 'Coaching Card' for the parent in this EXACT JSON format:
{
  "subject": "[Subject Name like Math, Science, etc.]",
  "questions": {
    "foundation": "[THE SPARK: A question to activate what they already know - DO NOT reveal the answer]",
    "bridge": "[THE CLIMB: A question that points to the specific error/roadblock - DO NOT reveal the answer]",
    "mastery": "[THE SUMMIT: A question to verify they can do it alone next time - DO NOT reveal the answer]"
  },
  "behavioral_tip": "[TEACHER TIP: A 1-sentence behavioral tip for parent-child harmony]",
  "example_approach": "[OPTIONAL: A brief explanation of the concept and approach for the parent to understand. Explain the method WITHOUT giving the final answer.]",
  "solution_steps": [
    "Step with actual calculation: e.g., 'First, identify the numbers: 12 and 5'",
    "Step with actual work: e.g., 'Add the numbers: 12 + 5 = 17'",
    "Continue with ALL steps showing complete work with real digits",
    "Final step: e.g., 'Therefore, the answer is 17'"
  ]
}

IMPORTANT FOR solution_steps:
- Include ACTUAL numbers from the problem
- Show COMPLETE calculations (e.g., "24 ÷ 6 = 4")
- Be specific, not generic
- Solve the problem fully in these steps
- Use as many steps as needed for clarity (5-8 steps typical)

Analyze the homework image and provide ONLY the JSON response. Be encouraging, patient, and precise."""


class AnalysisResponse(BaseModel):
    """Response model for homework analysis"""
    subject: str
    questions: dict
    behavioral_tip: str
    example_approach: Optional[str] = None
    solution_steps: Optional[list] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    ai_configured: bool


def compress_image(image_bytes: bytes, max_size: tuple = (1024, 1024), quality: int = 85) -> bytes:
    """
    Compress image for faster API processing and cost optimization
    """
    try:
        img = Image.open(BytesIO(image_bytes))
        
        # Convert RGBA to RGB if necessary
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        
        # Resize if larger than max_size
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to bytes buffer
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        return buffer.getvalue()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image processing error: {str(e)}")


async def analyze_with_ai(image_bytes: bytes, grade: Optional[str] = None, api_key: Optional[str] = None) -> dict:
    """
    Analyze homework image using Google Gemini AI
    """
    # Use provided API key or fallback to default
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        # Fallback response when API key is not configured
        return {
            "subject": "General Study",
            "questions": {
                "foundation": "What do you already know about this topic? Can you explain it in your own words?",
                "bridge": "Let's look at where you got stuck. What was the last step you were confident about?",
                "mastery": "Now try to solve the next part on your own. What would you do first?"
            },
            "behavioral_tip": "Remember to let your child think out loud. Resist the urge to jump in with answers!",
            "example_approach": "This is a general approach for any homework problem. The key is to: 1) Identify what the student knows, 2) Find where they're stuck, 3) Guide them to discover the next step themselves. The goal is not to solve it FOR them, but to help them develop problem-solving strategies they can use independently."
        }
    
    try:
        # Compress image for API efficiency
        compressed_image = compress_image(image_bytes)
        
        # Prepare the prompt with grade context if provided
        prompt = SYSTEM_PROMPT
        if grade:
            prompt += f"\n\nSTUDENT GRADE LEVEL: {grade}"
        
        # Create client with the provided API key
        session_client = genai.Client(api_key=api_key)
        
        # Generate response using the modern google.genai API
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = session_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[
                        prompt,
                        types.Part(inline_data=types.Blob(
                            data=compressed_image,
                            mime_type='image/jpeg'
                        ))
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        top_p=0.95,
                        max_output_tokens=3072,  # Increased for complete responses
                        response_mime_type="application/json",  # Request JSON directly
                    )
                )
                break  # Success, exit retry loop
            except Exception as e:
                # If quota exceeded or not found, provide intelligent fallback
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "404" in str(e):
                    return {
                        "subject": "Homework Analysis (Fallback Mode)",
                        "questions": {
                            "foundation": "Let's start with what you remember. Can you explain the main concept in your own words?",
                            "bridge": "Now show me exactly where you're stuck. What's the last step you understood completely?",
                            "mastery": "Great! Now that we've discussed it, try the next similar problem on your own. What would you do first?"
                        },
                        "behavioral_tip": "Take breaks together. Learning happens best when both parent and child stay patient and curious!",
                        "example_approach": "ℹ️ Using smart fallback mode (API issue detected).\n\nGeneral coaching approach: 1) Ask your child to read the problem out loud, 2) Have them explain what they think it's asking, 3) Guide them to break it into smaller steps, 4) Let them try each step before helping. The goal is building their confidence and problem-solving skills!",
                        "solution_steps": []
                    }
                if attempt == max_retries - 1:
                    raise
                # Retry on other errors
                continue
        
        # Extract JSON from response with better error handling
        response_text = response.text.strip()
        
        # Try to extract JSON if wrapped in markdown code blocks
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        # Try parsing the JSON
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError as json_err:
            # Try to fix common JSON issues
            try:
                # Remove trailing commas
                fixed_text = response_text.replace(',]', ']').replace(',}', '}')
                result = json.loads(fixed_text)
            except:
                # If still fails, return a structured error response
                raise HTTPException(
                    status_code=500, 
                    detail=f"AI returned incomplete response. Please try again. (Parse error: {str(json_err)})"
                )
        
        # Validate required fields
        if not all(key in result for key in ['subject', 'questions', 'behavioral_tip']):
            raise HTTPException(
                status_code=500,
                detail="AI response missing required fields. Please try again."
            )
        
        return result
        
    except json.JSONDecodeError as e:
        # Return helpful error message
        raise HTTPException(
            status_code=500, 
            detail=f"AI returned incomplete response. Please try uploading the image again."
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis error: {str(e)}")


@app.get("/session")
async def get_session():
    """Create or retrieve session, return session ID"""
    cleanup_expired_sessions()
    session_id = create_session()
    response = JSONResponse(
        content={"session_id": session_id, "status": "created"}
    )
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=SESSION_TIMEOUT,
        httponly=True,
        samesite="Lax"
    )
    return response


@app.get("/", response_class=FileResponse)
async def root():
    """Serve the main frontend page"""
    return FileResponse("static/index.html")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Returns system status and AI configuration state
    """
    return HealthResponse(
        status="healthy",
        message="Socratic Parent is ready to transform homework time!",
        ai_configured=client is not None
    )


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_homework(
    file: UploadFile = File(...),
    grade: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None)
):
    """
    Analyze homework image and generate Socratic questioning script
    
    Args:
        file: Image file of homework (JPEG, PNG, etc.)
        grade: Optional grade level for better context
    
    Returns:
        Coaching card with guided inquiry questions
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an image file."
        )
    
    try:
        # Read image bytes
        image_bytes = await file.read()
        
        # Get API key for this session
        api_key = None
        if session_id:
            api_key = get_session_key(session_id)
        
        # Fallback to default if no session
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY")
        
        # Analyze with AI
        result = await analyze_with_ai(image_bytes, grade, api_key)
        
        return AnalysisResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
