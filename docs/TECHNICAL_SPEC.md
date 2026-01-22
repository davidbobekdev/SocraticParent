# Technical Specification

## 1. Backend: Python/FastAPI
- **Framework**: FastAPI 0.110.0 with uvicorn
- **Python Version**: 3.12 (slim Docker image)
- **Endpoints:**
  - `GET /`: Serves complete HTML application (embedded frontend)
  - `POST /upload`: Accepts multipart image upload, returns structured lesson
  - `GET /health`: System health check
  - `GET /api/test`: AI model connectivity test
- **Processing Logic:**
  - Accept JPG/PNG images via multipart form data
  - Call Google Gemini 2.5 Flash API for intelligent analysis
  - Parse AI response into structured steps (Subject, Problem, Steps 1-6)
  - Return formatted JSON with step titles and content
- **AI Configuration:**
  - Model: `gemini-2.5-flash`
  - API: Google Generative AI SDK
  - Response: Structured text with markdown formatting
- **Security:** 
  - Environment-based API key management (`.env` + Railway vars)
  - No image storage (process and discard)
  - Non-root Docker container user
  - CORS enabled for development

## 2. Frontend: Vanilla Web Stack (Embedded in Python)
- **Stack**: HTML5, Custom CSS, Vanilla JavaScript (no frameworks)
- **Architecture**: Embedded directly in `main.py` as Python string (1000+ lines)
- **Key Features:**
  - Drag-and-drop file upload with visual feedback
  - File input with preview
  - Step-by-step navigation (Previous/Continue buttons)
  - Progress bar with percentage tracking
  - KaTeX math rendering on-the-fly
  - Responsive mobile/desktop layouts
  - Smooth animations and transitions
- **State Management:**
  - Global variables: `selectedFile`, `steps[]`, `currentStep`, `lessonData{}`
  - Dynamic DOM manipulation with `innerHTML`
  - CSS class toggling for step visibility (`.active`)
- **Math Rendering:**
  - KaTeX 0.16.9 CDN integration
  - Auto-rendering with `renderMathInElement()`
  - Custom CSS for Wolfram Alpha-style visuals
  - Re-rendering on each step transition

## 3. Data Schema

### API Request (POST /upload)
```
Content-Type: multipart/form-data
file: <image binary>
```

### API Response
```json
{
  "analysis": "**Subject & Topic:** Math - Linear Equations\n\n**The Problem:**\nSolve for x: 2²(x + 3) + 9 - 5 = 32\n\n**Step 1: Understanding**\nWe are given an equation...\n\n**Step 2: Identify the Rules**\n...\n\n**Step 6: Final Answer**\nx = 4"
}
```

### Internal Parsed Structure (Frontend)
```javascript
{
  subject: "Math - Linear Equations",
  problem: "Solve for x: 2²(x + 3) + 9 - 5 = 32",
  steps: [
    { title: "Step 1: Understanding", content: "We are given..." },
    { title: "Step 2: Identify the Rules", content: "..." },
    // ... Steps 3-6
  ]
}
```

## 4. Deployment

### Railway.app (Production)
- **Platform**: Railway (PaaS)
- **Build**: Automatic via `railway.json` and Dockerfile
- **Environment**: `GEMINI_API_KEY` set in Railway dashboard
- **URL**: https://socratesparent-production.up.railway.app/
- **Deployment**: Automated via `deploy-railway.sh` script

### Docker (Self-Hosted)
- **Base Image**: `python:3.12-slim`
- **Port**: 8000 (configurable via PORT env var)
- **Health Check**: GET /health every 30s
- **Restart Policy**: unless-stopped
- **User**: Non-root container user for security

## 5. Dependencies

### Python (requirements.txt)
```
fastapi==0.110.0
uvicorn[standard]==0.27.1
google-genai==0.2.2
pillow==10.2.0
python-multipart==0.0.9
```

### Frontend (CDN)
```
KaTeX 0.16.9 (CSS + JS + Auto-render)
```

## 6. Key Functions

### Backend
- `analyze_homework_with_ai()`: Calls Gemini API with structured prompt
- `/upload` endpoint: Handles file upload and AI processing

### Frontend
- `handleFile()`: Preview uploaded image
- `analyzeHomework()`: POST to /upload API
- `parseAndDisplayLesson()`: Parse AI response into steps
- `displayLesson()`: Render all steps to DOM
- `showStep(index)`: Display specific step with KaTeX rendering
- `nextStep()`: Navigate forward through steps
- `previousStep()`: Navigate backward through steps
- `resetUI()`: Clear content and restore upload state
- `tryAnother()`: Reset for new problem
- `formatStepContent()`: Format text with markdown and structure

## 7. Math Rendering Details

### KaTeX Integration
```javascript
// Render all math in container
renderMathInElement(document.getElementById('lessonContent'), {
    delimiters: [
        {left: '$$', right: '$$', display: true},
        {left: '$', right: '$', display: false}
    ],
    throwOnError: false
});
```

### Custom CSS Styling (Wolfram Alpha-inspired)
```css
/* Number styling */
.katex .mord.mathdefault { color: #1e40af; }

/* Exponent styling */
.katex .msupsub { color: #dc2626; font-size: 1.1em; }

/* Operator styling */
.katex .mbin, .katex .mrel { color: #059669; }

/* Parentheses */
.katex .mopen, .katex .mclose { color: #7c3aed; }

/* Variables */
.katex .mathrm { color: #be123c; font-style: italic; }

/* Display equations */
.katex-display {
    background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #bfdbfe;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}
```

## 8. Mobile Responsiveness

### Breakpoint Strategy
```css
@media (max-width: 768px) {
    /* Reduced spacing */
    .step-card { margin-bottom: 12px; padding: 20px; }
    
    /* Smaller typography */
    .step-title { font-size: 1.3em; }
    body { font-size: 1em; }
    
    /* Full-width layout */
    .container { padding: 16px; }
}
```

## 9. State Flow

### Initial Load
```
User visits / → FastAPI serves HTML → Browser renders UI → Ready for upload
```

### Image Analysis Flow
```
1. User selects image → handleFile() → Preview displayed
2. Click "Start Learning" → analyzeHomework() → Show loading
3. POST /upload → Gemini API → Parse response
4. parseAndDisplayLesson() → Extract steps → displayLesson()
5. Render HTML with KaTeX → showStep(0) → Display first step
```

### Navigation Flow
```
User clicks Continue → nextStep() → showStep(currentStep + 1) → 
  Remove all .active classes → Add .active to new step → 
  Re-render KaTeX in active step → Update progress bar
```

### Reset Flow
```
User clicks "Try Another Problem" → tryAnother() → Reset variables →
  resetUI() → Clear content → Restore navigation display →
  Show upload section
```
