"""
Socratic Parent - Simple Version with Image Upload and API Key Session
"""

import os
from google import genai
from google.genai import types
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Learn Step-by-Step</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" onload="renderMathInElement(document.body, {delimiters: [{left: '$$', right: '$$', display: true}, {left: '$', right: '$', display: false}]});"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8fafc;
            min-height: 100vh;
            padding: 32px 20px;
        }
        .container {
            max-width: 720px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            border: 1px solid #e2e8f0;
        }
        .header {
            background: white;
            padding: 48px 40px 40px;
            text-align: center;
            border-bottom: 1px solid #e2e8f0;
        }
        h1 { 
            color: #0f172a; 
            font-size: 2.25em; 
            font-weight: 700;
            margin-bottom: 12px;
            letter-spacing: -0.02em;
        }
        .tagline { 
            color: #64748b; 
            font-size: 1.05em; 
            font-weight: 400;
            line-height: 1.6;
        }
        .content {
            padding: 40px;
        }
        .upload-section {
            background: #fafafa;
            border: 2px dashed #cbd5e1;
            border-radius: 12px;
            padding: 48px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-bottom: 20px;
            position: relative;
        }
        .upload-section * {
            pointer-events: none;
        }
        .upload-section:hover {
            border-color: #3b82f6;
            background: #f0f9ff;
        }
        .upload-section.dragover {
            border-color: #3b82f6;
            background: #eff6ff;
        }
        .upload-icon { font-size: 3em; margin-bottom: 16px; color: #3b82f6; }
        .upload-text {
            color: #334155;
            font-size: 1.1em;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .upload-hint {
            color: #64748b;
            font-size: 0.9em;
        }
        .preview-img {
            max-width: 100%;
            max-height: 400px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid #e2e8f0;
        }
        #fileInput { display: none; }
        .btn {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 14px 32px;
            border-radius: 8px;
            font-size: 1.05em;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: all 0.2s ease;
        }
        .btn:hover {
            background: #2563eb;
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        /* Step-by-step display */
        .lesson-container {
            display: none;
            animation: fadeIn 0.4s ease-out;
        }
        .lesson-container.show { display: block; }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .subject-badge {
            display: inline-block;
            background: #eff6ff;
            color: #1e40af;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 0.85em;
            font-weight: 600;
            margin-bottom: 24px;
            border: 1px solid #bfdbfe;
        }
        .problem-card {
            background: #f0f9ff;
            border-left: 4px solid #3b82f6;
            padding: 24px;
            border-radius: 8px;
            margin-bottom: 32px;
            border: 1px solid #bfdbfe;
        }
        .problem-card .label {
            color: #1e40af;
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }
        .problem-card .content {
            color: #1e40af;
            font-size: 1.15em;
            font-weight: 500;
            line-height: 1.6;
        }
        .step-card {
            background: white;
            padding: 0;
            margin-bottom: 20px;
            display: none;
        }
        .step-card.active {
            display: block;
            animation: slideInUp 0.3s ease-out;
        }
        @keyframes slideInUp {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .step-header {
            margin-bottom: 32px;
            padding-bottom: 24px;
            border-bottom: 2px solid #e2e8f0;
        }
        .step-number {
            display: inline-block;
            background: #eff6ff;
            color: #1e40af;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 0.85em;
            font-weight: 600;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .step-title {
            color: #0f172a;
            font-size: 1.75em;
            font-weight: 700;
            line-height: 1.3;
            letter-spacing: -0.01em;
        }
        .step-content {
            color: #334155;
            font-size: 1.125em;
            line-height: 1.75;
            max-width: 65ch;
        }
        .step-content p {
            margin: 24px 0;
        }
        .step-content .step-item {
            margin: 32px 0;
            padding: 24px;
            background: #f8fafc;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
        }
        .step-content .step-number-inline {
            font-weight: 700;
            color: #1e40af;
            font-size: 1em;
            display: block;
            margin-bottom: 12px;
        }
        .step-content ul, .step-content ol {
            margin: 24px 0;
            padding-left: 28px;
        }
        .step-content li {
            margin: 16px 0;
            line-height: 1.7;
            color: #475569;
        }
        .step-content strong, .step-content b {
            color: #0f172a;
            font-weight: 700;
        }
        .math-expr {
            font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
            font-weight: 600;
            color: #1e40af;
            font-size: 1em;
            background: #eff6ff;
            padding: 2px 6px;
            border-radius: 4px;
        }
        /* KaTeX math styling */
        .katex {
            font-size: 1.05em;
        }
        .katex-display {
            margin: 24px 0;
        }
        .step-content .katex-display {
            background: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
        }
        .practice-card {
            background: #f0f9ff;
            border: 1px solid #bfdbfe;
            border-left: 4px solid #3b82f6;
            padding: 24px;
            border-radius: 8px;
            margin-top: 32px;
        }
        .practice-card .label {
            color: #1e40af;
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }
        .practice-card .content {
            color: #1e40af;
            font-size: 1.1em;
            font-weight: 500;
            line-height: 1.6;
        }
        .navigation {
            display: flex;
            gap: 12px;
            margin-top: 48px;
            padding-top: 32px;
            border-top: 1px solid #e2e8f0;
        }
        .nav-btn {
            flex: 1;
            background: #3b82f6;
            color: white;
            border: none;
            padding: 14px 24px;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .nav-btn:hover:not(:disabled) {
            background: #2563eb;
        }
        .nav-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }
        .nav-btn.primary {
            background: #3b82f6;
        }
        .progress-bar {
            background: #e2e8f0;
            height: 6px;
            border-radius: 3px;
            overflow: hidden;
            margin-bottom: 40px;
        }
        .progress-fill {
            background: #3b82f6;
            height: 100%;
            border-radius: 3px;
            transition: width 0.5s ease;
        }
        .completion-badge {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 32px;
            border-radius: 8px;
            text-align: center;
            margin-top: 24px;
        }
        .completion-badge .icon { font-size: 3.5em; margin-bottom: 16px; }
        .completion-badge .title { font-size: 1.6em; font-weight: 700; margin-bottom: 8px; }
        .completion-badge .message { font-size: 1em; opacity: 0.95; }
        .loading {
            text-align: center;
            padding: 48px;
            color: #64748b;
        }
        .loading .spinner {
            border: 3px solid #e2e8f0;
            border-top: 3px solid #3b82f6;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Step-by-Step Learning</h1>
            <p class="tagline">Master every problem, one step at a time</p>
        </div>
        
        <div class="content">
            <div id="uploadSection">
                <input type="file" id="fileInput" accept="image/*" onchange="handleFileSelect(event)" style="display: none;">
                <div class="upload-section" id="uploadArea" onclick="document.getElementById('fileInput').click()">
                    <div class="upload-icon">📸</div>
                    <div class="upload-text">Upload Your Homework</div>
                    <div class="upload-hint">Click or drag and drop an image</div>
                </div>
                <img id="preview" class="preview-img" style="display: none;">
                <button class="btn" id="analyzeBtn" onclick="analyzeHomework()" style="display: none;">
                    🚀 Start Learning
                </button>
            </div>
            
            <div id="loadingSection" class="loading" style="display: none;">
                <div class="spinner"></div>
                <div style="font-size: 1.2em; font-weight: 600;">Analyzing your problem...</div>
            </div>
            
            <div id="lessonSection" class="lesson-container" style="display: none;">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill" style="width: 0%"></div>
                </div>
                <div id="lessonContent"></div>
                <div class="navigation">
                    <button class="nav-btn" id="prevBtn" onclick="previousStep()">← Previous</button>
                    <button class="nav-btn primary" id="nextBtn" onclick="nextStep()">Continue →</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedFile = null;
        let steps = [];
        let currentStep = 0;
        let lessonData = {};
        
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.classList.add('dragover'); });
        uploadArea.addEventListener('dragleave', () => { uploadArea.classList.remove('dragover'); });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0 && files[0].type.startsWith('image/')) { handleFile(files[0]); }
        });
        
        function handleFileSelect(event) {
            console.log('File selected:', event.target.files);
            const file = event.target.files[0];
            if (file) {
                console.log('File details:', file.name, file.type, file.size);
                if (file.type.startsWith('image/')) { 
                    handleFile(file);
                } else {
                    alert('Please select an image file (JPG, PNG, etc.)');
                }
            }
        }
        
        function handleFile(file) {
            console.log('Handling file:', file.name);
            selectedFile = file;
            const reader = new FileReader();
            reader.onload = (e) => {
                console.log('File loaded successfully');
                document.getElementById('preview').src = e.target.result;
                document.getElementById('preview').style.display = 'block';
                document.getElementById('analyzeBtn').style.display = 'block';
            };
            reader.onerror = (e) => {
                console.error('Error reading file:', e);
                alert('Error reading file. Please try again.');
            };
            reader.readAsDataURL(file);
        }
        
        async function analyzeHomework() {
            if (!selectedFile) return;
            
            document.getElementById('uploadSection').style.display = 'none';
            document.getElementById('loadingSection').style.display = 'block';
            
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            try {
                const response = await fetch('/upload', { method: 'POST', body: formData });
                const data = await response.json();
                
                console.log('Server response:', data);
                
                if (data.analysis) {
                    parseAndDisplayLesson(data.analysis);
                } else if (data.error) {
                    alert('Error: ' + data.error);
                    resetUI();
                } else {
                    alert('Error: No analysis returned from server');
                    resetUI();
                }
            } catch (error) {
                console.error('Fetch error:', error);
                alert('Error: ' + error.message);
                resetUI();
            }
        }
        
        function parseAndDisplayLesson(analysis) {
            const lines = analysis.split('\\n');
            steps = [];
            let currentSection = null;
            let content = '';
            
            for (let line of lines) {
                line = line.trim();
                if (!line) continue;
                
                if (line.includes('Subject & Topic:')) {
                    lessonData.subject = line.replace(/\\*\\*Subject & Topic:\\*\\*/g, '').replace('Subject & Topic:', '').trim();
                } else if (line.includes('The Problem:')) {
                    if (currentSection && typeof currentSection === 'object' && currentSection.type === 'step' && content) {
                        steps.push({ title: currentSection.title, content: content.trim() });
                    }
                    currentSection = 'problem';
                    content = '';
                } else if (line.includes('Step ') && line.includes(':')) {
                    if (currentSection === 'problem' && content) {
                        lessonData.problem = content.trim();
                    }
                    if (currentSection && typeof currentSection === 'object' && currentSection.type === 'step' && content) {
                        steps.push({ title: currentSection.title, content: content.trim() });
                    }
                    const title = line.replace(/\\*\\*/g, '').trim();
                    currentSection = { title: title, type: 'step' };
                    content = '';
                } else if (line.includes('Practice Question:')) {
                    if (currentSection && typeof currentSection === 'object' && currentSection.type === 'step' && content) {
                        steps.push({ title: currentSection.title, content: content.trim() });
                    }
                    currentSection = 'practice';
                    content = '';
                } else {
                    content += line + '\\n';
                }
            }
            
            if (currentSection === 'practice' && content) {
                lessonData.practice = content.trim();
            } else if (currentSection && typeof currentSection === 'object' && currentSection.type === 'step' && content) {
                steps.push({ title: currentSection.title, content: content.trim() });
            }
            
            displayLesson();
        }
        
        function formatStepContent(content) {
            // First, convert backtick expressions to styled math expressions
            content = content.replace(/`([^`]+)`/g, '<span class="math-expr">$1</span>');
            
            // Auto-detect and highlight math expressions (numbers with operators)
            // Match patterns like: 6 ÷ 2, 3 * 3, 6 ÷ 2 = 3, (1 + 2), etc.
            content = content.replace(/(\d+\s*[+\-×÷*\/]\s*\d+(?:\s*[+\-×÷*\/]\s*\d+)*(?:\s*=\s*\d+)?)/g, '<span class="math-expr">$1</span>');
            
            // Match expressions with parentheses like (1 + 2) or 2(1+2)
            content = content.replace(/(\d*\([^)]+\)(?:\s*[+\-×÷*\/]\s*\d+)?)/g, function(match) {
                // Don't double-wrap if already wrapped
                if (!match.includes('class="math-expr"')) {
                    return '<span class="math-expr">' + match + '</span>';
                }
                return match;
            });
            
            // Convert **text** to bold
            content = content.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
            
            // Split into sentences for better readability
            let formatted = '';
            
            // Split by asterisk bullet points first
            const lines = content.split('\\n');
            let hasBullets = false;
            let bulletItems = [];
            let regularText = '';
            
            for (let line of lines) {
                line = line.trim();
                if (line.startsWith('* ') || line.startsWith('- ')) {
                    hasBullets = true;
                    bulletItems.push(line.substring(2).trim());
                } else if (line) {
                    regularText += line + ' ';
                }
            }
            
            if (hasBullets) {
                if (regularText) {
                    formatted += '<p>' + regularText.trim() + '</p>';
                }
                formatted += '<ul>';
                for (let item of bulletItems) {
                    formatted += '<li>' + item + '</li>';
                }
                formatted += '</ul>';
            } else {
                // Split content by numbered steps (1., 2., 3., etc.)
                const stepPattern = /\\b(\\d+)\\./g;
                const parts = content.split(stepPattern);
                
                if (parts.length > 2) {
                    // Has numbered steps
                    formatted += '<div class=\"step-item\">';
                    for (let i = 1; i < parts.length; i += 2) {
                        const stepNum = parts[i];
                        const stepContent = parts[i + 1];
                        if (stepContent && stepContent.trim()) {
                            formatted += '<div class=\"step-number-inline\">' + stepNum + '.</div>';
                            formatted += '<p>' + stepContent.trim() + '</p>';
                        }
                    }
                    formatted += '</div>';
                } else {
                    // No numbered steps, format as regular paragraphs
                    const sentences = content.split('. ');
                    let currentPara = '';
                    
                    for (let sentence of sentences) {
                        sentence = sentence.trim();
                        if (!sentence) continue;
                        
                        currentPara += sentence + '. ';
                        
                        if (currentPara.split('.').length > 3 || currentPara.length > 200) {
                            formatted += '<p>' + currentPara.trim() + '</p>';
                            currentPara = '';
                        }
                    }
                    
                    if (currentPara.trim()) {
                        formatted += '<p>' + currentPara.trim() + '</p>';
                    }
                }
            }
            
            return formatted || '<p>' + content + '</p>';
        }
        
        function displayLesson() {
            document.getElementById('loadingSection').style.display = 'none';
            const lessonSection = document.getElementById('lessonSection');
            lessonSection.style.display = 'block';
            lessonSection.classList.add('show');
            
            let html = '';
            if (lessonData.subject) {
                html += '<div class="subject-badge">📖 ' + lessonData.subject + '</div>';
            }
            if (lessonData.problem) {
                html += '<div class="problem-card"><div class="label">The Problem</div><div class="content">' + lessonData.problem + '</div></div>';
            }
            
            steps.forEach((step, index) => {
                html += '<div class="step-card" id="step' + index + '">';
                html += '<div class="step-header">';
                html += '<div class="step-number">' + (index + 1) + '</div>';
                html += '<div class="step-title">' + step.title.replace(/Step \\d+: /g, '') + '</div>';
                html += '</div>';
                html += '<div class="step-content">' + formatStepContent(step.content) + '</div>';
                html += '</div>';
            });
            
            if (lessonData.practice) {
                html += '<div class="practice-card"><div class="label">🎯 Try This Next</div><div class="content">' + lessonData.practice + '</div></div>';
            }
            
            document.getElementById('lessonContent').innerHTML = html;
            
            // Render math expressions with KaTeX
            if (typeof renderMathInElement !== 'undefined') {
                renderMathInElement(document.getElementById('lessonContent'), {
                    delimiters: [
                        {left: '$$', right: '$$', display: true},
                        {left: '$', right: '$', display: false}
                    ],
                    throwOnError: false
                });
            }
            
            currentStep = 0;
            showStep(0);
        }
        
        function showStep(index) {
            document.querySelectorAll('.step-card').forEach(card => card.classList.remove('active'));
            const stepCard = document.getElementById('step' + index);
            if (stepCard) stepCard.classList.add('active');
            
            currentStep = index;
            updateNavigation();
            updateProgress();
        }
        
        function updateNavigation() {
            document.getElementById('prevBtn').disabled = currentStep === 0;
            
            if (currentStep === steps.length - 1) {
                document.getElementById('nextBtn').textContent = 'Finish 🎉';
            } else {
                document.getElementById('nextBtn').textContent = 'Continue →';
            }
        }
        
        function updateProgress() {
            const progress = ((currentStep + 1) / steps.length) * 100;
            document.getElementById('progressFill').style.width = progress + '%';
        }
        
        function nextStep() {
            if (currentStep < steps.length - 1) {
                showStep(currentStep + 1);
            } else {
                showCompletion();
            }
        }
        
        function previousStep() {
            if (currentStep > 0) {
                showStep(currentStep - 1);
            }
        }
        
        function showCompletion() {
            document.querySelector('.navigation').style.display = 'none';
            document.querySelectorAll('.step-card').forEach(card => card.style.display = 'block');
            
            const completion = '<div class="completion-badge"><div class="icon">🎉</div><div class="title">You Did It!</div><div class="message">Great job working through this problem step by step!</div><button class="btn" onclick="tryAnother()" style="margin-top: 20px; width: auto; padding: 14px 32px;">📚 Try Another Problem</button></div>';
            document.getElementById('lessonContent').innerHTML += completion;
            
            document.getElementById('progressFill').style.width = '100%';
        }
        
        function tryAnother() {
            selectedFile = null;
            steps = [];
            currentStep = 0;
            lessonData = {};
            document.getElementById('preview').style.display = 'none';
            document.getElementById('analyzeBtn').style.display = 'none';
            document.getElementById('fileInput').value = '';
            resetUI();
        }
        
        function resetUI() {
            document.getElementById('uploadSection').style.display = 'block';
            document.getElementById('loadingSection').style.display = 'none';
            const lessonSection = document.getElementById('lessonSection');
            lessonSection.style.display = 'none';
            lessonSection.classList.remove('show');
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML_CONTENT

@app.get("/api/test")
async def test_endpoint():
    server_key = os.getenv("GEMINI_API_KEY")
    return {
        "status": "success", 
        "message": "API is working!", 
        "version": "session-v2-with-fallback", 
        "ready": True,
        "server_key_available": bool(server_key)
    }

async def analyze_homework_with_ai(image_bytes: bytes, api_key: str):
    """Analyze homework image using Google Gemini and generate Socratic questions"""
    try:
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

        # Convert bytes to image part
        import PIL.Image
        import io
        import base64
        
        image = PIL.Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if needed (for PNG with palette, etc.)
        if image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = PIL.Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to bytes for API
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_data = img_byte_arr.getvalue()
        
        # Create image part for Gemini API
        image_part = types.Part.from_bytes(
            data=img_data,
            mime_type='image/jpeg'
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, image_part]
        )
        return {"success": True, "analysis": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith('image/'):
        return JSONResponse(status_code=400, content={"error": "Invalid file type"})
    
    contents = await file.read()
    
    # Use server API key
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return JSONResponse(status_code=500, content={"error": "No API key configured on server"})
    
    # Analyze with AI
    ai_result = await analyze_homework_with_ai(contents, api_key)
    
    if ai_result["success"]:
        return {
            "status": "success",
            "analysis": ai_result["analysis"],
            "filename": file.filename
        }
    else:
        return JSONResponse(
            status_code=500, 
            content={"error": f"Analysis failed: {ai_result['error']}"}
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
