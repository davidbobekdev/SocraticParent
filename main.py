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
    <title>Socratic Parent</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 { color: #667eea; margin-bottom: 10px; font-size: 2.5em; }
        .tagline { color: #666; margin-bottom: 30px; font-size: 1.1em; }
        .status { background: #e8f5e9; border: 2px solid #4caf50; border-radius: 10px; padding: 20px; margin: 20px 0; }
        .status.warning { background: #fff3e0; border-color: #ff9800; }
        .status-text { color: #2e7d32; font-size: 1.2em; font-weight: 600; }
        .status.warning .status-text { color: #e65100; }
        .info { background: #f5f5f5; border-radius: 10px; padding: 20px; margin: 20px 0; }
        .info p { color: #333; line-height: 1.6; margin-bottom: 10px; }
        .btn {
            background: #667eea; color: white; border: none; padding: 15px 30px;
            border-radius: 10px; font-size: 1em; cursor: pointer; width: 100%;
            margin-top: 20px; font-weight: 600; transition: all 0.3s;
        }
        .btn.secondary { background: #9c27b0; }
        .btn.secondary:hover { background: #7b1fa2; }
        .btn:hover { background: #5568d3; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }
        .upload-area {
            border: 2px dashed #667eea; border-radius: 10px; padding: 30px;
            margin: 20px 0; text-align: center; cursor: pointer; transition: all 0.3s;
        }
        .upload-area:hover { background: #f5f5ff; border-color: #5568d3; }
        .upload-area.dragover { background: #e8f0fe; border-color: #4285f4; }
        .preview-img { max-width: 100%; max-height: 300px; margin: 20px 0; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        #fileInput { display: none; }
        .response { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white;
            border-radius: 15px; 
            padding: 25px; 
            margin: 20px 0; 
            display: none;
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        }
        .response.show { display: block; }
        .response hr { border: 1px solid rgba(255,255,255,0.3); }
        .response strong { color: #fff; }
        .response small { color: rgba(255,255,255,0.8); }
        .api-key-section { background: #e3f2fd; border: 2px solid #2196f3; border-radius: 10px; padding: 20px; margin: 20px 0; }
        .input-group { margin: 10px 0; }
        .input-group label { display: block; color: #1565c0; font-weight: 600; margin-bottom: 5px; }
        .input-group input { width: 100%; padding: 10px; border: 1px solid #90caf9; border-radius: 5px; font-size: 0.9em; }
        .key-status { display: inline-block; padding: 5px 10px; border-radius: 5px; font-size: 0.85em; font-weight: 600; margin-left: 10px; }
        .key-status.saved { background: #c8e6c9; color: #2e7d32; }
        .key-status.none { background: #ffcdd2; color: #c62828; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 Socratic Parent</h1>
        <p class="tagline">The Anti-Homework-Solver</p>
        
        <div class="status" id="statusDiv">
            <p class="status-text">✅ Server is running!</p>
        </div>
        
        <div class="api-key-section">
            <h3 style="color: #1565c0; margin-bottom: 10px;">
                �� Your API Key 
                <span class="key-status" id="keyStatus">None</span>
            </h3>
            <p style="color: #555; font-size: 0.9em; margin-bottom: 15px;">
                <strong>Optional:</strong> Store your own Gemini API key securely in your browser. 
                Get one from <a href="https://makersuite.google.com/app/apikey" target="_blank" style="color: #2196f3;">Google AI Studio</a><br>
                <em style="color: #666;">If not provided, the server's key will be used (if available)</em>
            </p>
            <div class="input-group">
                <label for="apiKeyInput">Gemini API Key:</label>
                <input type="password" id="apiKeyInput" placeholder="AIza..." />
            </div>
            <button class="btn secondary" onclick="saveApiKey()">Save API Key</button>
            <button class="btn secondary" onclick="clearApiKey()" style="background: #f44336; margin-top: 10px;">Clear Key</button>
        </div>
        
        <div class="info">
            <p><strong>Version:</strong> Session Management</p>
            <p><strong>Status:</strong> Ready to upload & analyze</p>
            <p><strong>Privacy:</strong> Your API key stays in your browser</p>
        </div>
        
        <div id="uploadArea" class="upload-area" onclick="document.getElementById('fileInput').click()">
            <p style="font-size: 3em; margin: 0;">📸</p>
            <p style="margin: 10px 0; font-weight: 600;">Click or Drag & Drop</p>
            <p style="color: #666; font-size: 0.9em;">Upload a homework image (JPG, PNG)</p>
        </div>
        
        <input type="file" id="fileInput" accept="image/*" onchange="handleFileSelect(event)">
        <img id="preview" class="preview-img" style="display: none;">
        <button class="btn" id="uploadBtn" onclick="uploadImage()">Upload & Analyze</button>
        <button class="btn" onclick="testAPI()">Test API Connection</button>
        
        <div id="response" class="response"><p id="responseText"></p></div>
    </div>
    <script>
        let selectedFile = null;
        
        async function checkApiKey() {
            const apiKey = localStorage.getItem('gemini_api_key');
            const statusDiv = document.getElementById('statusDiv');
            const keyStatus = document.getElementById('keyStatus');
            
            // Check if server has a key
            let serverHasKey = false;
            try {
                const response = await fetch('/api/test');
                const data = await response.json();
                serverHasKey = data.server_key_available;
            } catch (e) {
                // Ignore error
            }
            
            if (apiKey) {
                keyStatus.textContent = '✓ Saved';
                keyStatus.className = 'key-status saved';
                document.getElementById('apiKeyInput').value = apiKey;
                statusDiv.className = 'status';
                statusDiv.querySelector('.status-text').textContent = '✅ Ready! Using your API key';
            } else if (serverHasKey) {
                keyStatus.textContent = '✗ None (using server)';
                keyStatus.className = 'key-status none';
                statusDiv.className = 'status';
                statusDiv.querySelector('.status-text').textContent = '✅ Ready! Using server API key';
            } else {
                keyStatus.textContent = '✗ None';
                keyStatus.className = 'key-status none';
                statusDiv.className = 'status warning';
                statusDiv.querySelector('.status-text').textContent = '⚠️ Please save your API key to enable AI analysis';
            }
        }
        
        function saveApiKey() {
            const apiKey = document.getElementById('apiKeyInput').value.trim();
            if (!apiKey) {
                alert('Please enter an API key');
                return;
            }
            if (!apiKey.startsWith('AIza')) {
                alert('API key should start with "AIza"');
                return;
            }
            localStorage.setItem('gemini_api_key', apiKey);
            checkApiKey();
            showMessage('success', '✓ API key saved to your browser!');
        }
        
        function clearApiKey() {
            if (confirm('Are you sure you want to clear your API key?')) {
                localStorage.removeItem('gemini_api_key');
                document.getElementById('apiKeyInput').value = '';
                checkApiKey();
                showMessage('info', 'API key cleared');
            }
        }
        
        function getApiKey() {
            return localStorage.getItem('gemini_api_key');
        }
        
        function showMessage(type, message) {
            const responseDiv = document.getElementById('response');
            const responseText = document.getElementById('responseText');
            responseText.innerHTML = `<strong>${message}</strong>`;
            responseDiv.classList.add('show');
        }
        
        // File upload handlers
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
            const file = event.target.files[0];
            if (file && file.type.startsWith('image/')) { handleFile(file); }
        }
        
        function handleFile(file) {
            selectedFile = file;
            const reader = new FileReader();
            reader.onload = (e) => {
                const preview = document.getElementById('preview');
                preview.src = e.target.result;
                preview.style.display = 'block';
                document.getElementById('uploadBtn').style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
        
        async function uploadImage() {
            console.log('uploadImage called, selectedFile:', selectedFile);
            if (!selectedFile) {
                alert('Please select an image first!');
                return;
            }
            const responseDiv = document.getElementById('response');
            const responseText = document.getElementById('responseText');
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            // Add user's key if available (otherwise server will use its own)
            const apiKey = getApiKey();
            if (apiKey) {
                formData.append('api_key', apiKey);
            }
            
            try {
                responseText.innerHTML = '<strong>🔄 Analyzing homework...</strong><br><em>This may take a few seconds</em>';
                responseDiv.classList.add('show');
                const response = await fetch('/upload', { method: 'POST', body: formData });
                const data = await response.json();
                
                const keyInfo = data.key_source === 'user' ? '🔑 Your key' : 
                               data.key_source === 'server' ? '🔑 Server key' : 
                               '⚠️ No key';
                
                let html = `<strong>✅ ${data.message}</strong><br>`;
                html += `<small>File: ${data.filename} | Size: ${data.size} bytes | Key: ${keyInfo}</small>`;
                
                // If AI analysis is available, display it nicely
                if (data.analysis) {
                    html += `<hr style="margin: 20px 0; border: 1px solid #ddd;">`;
                    html += `<div style="text-align: left; line-height: 1.8; white-space: pre-wrap;">`;
                    html += data.analysis.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
                    html += `</div>`;
                }
                
                responseText.innerHTML = html;
                responseDiv.classList.add('show');
            } catch (error) {
                responseText.innerHTML = `<strong>❌ Error:</strong> ${error.message}`;
                responseDiv.classList.add('show');
            }
        }
        
        async function testAPI() {
            const responseDiv = document.getElementById('response');
            const responseText = document.getElementById('responseText');
            
            try {
                const response = await fetch('/api/test');
                const data = await response.json();
                
                const apiKey = getApiKey();
                const userKeyStatus = apiKey ? '✓ Saved in browser' : '✗ Not saved';
                const serverKeyStatus = data.server_key_available ? '✓ Available on server' : '✗ Not set';
                
                responseText.innerHTML = `<strong>API Response:</strong><br>${JSON.stringify(data, null, 2)}<br><br><strong>Your API Key:</strong> ${userKeyStatus}<br><strong>Server API Key:</strong> ${serverKeyStatus}<br><br><em>Upload will use ${apiKey ? 'your key' : (data.server_key_available ? 'server key' : 'no key')}</em>`;
                responseDiv.classList.add('show');
            } catch (error) {
                responseText.innerHTML = `<strong>Error:</strong> ${error.message}`;
                responseDiv.classList.add('show');
            }
        }
        
        // Initialize on page load
        checkApiKey();
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
        
        prompt = """You are a Socratic teaching assistant helping parents guide their children through homework.

Analyze this homework image and provide:
1. A brief description of what you see (subject, topic, question type)
2. 3-5 Socratic questions that guide the student to discover the answer themselves (DO NOT give the answer directly)
3. Key concepts the student should understand

Format your response as:
**Subject & Topic:** [description]

**Socratic Questions:**
1. [Question that helps them understand the problem]
2. [Question that guides them to identify what they know]
3. [Question that helps them think about the approach]
4. [Question that encourages them to try solving]
5. [Question that helps them verify their answer]

**Key Concepts:**
- [concept 1]
- [concept 2]
- [concept 3]

Remember: Guide, don't solve! Help them think, don't give answers."""

        # Convert bytes to image part
        import PIL.Image
        import io
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
        img_byte_arr.seek(0)
        
        # Upload file
        uploaded_file = client.files.upload(file=img_byte_arr, mime_type='image/jpeg')
        
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[prompt, uploaded_file]
        )
        return {"success": True, "analysis": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/upload")
async def upload_image(file: UploadFile = File(...), api_key: str = Form(None)):
    if not file.content_type or not file.content_type.startswith('image/'):
        return JSONResponse(status_code=400, content={"error": "Invalid file type"})
    
    contents = await file.read()
    
    # Try user's key first, fall back to server key
    final_key = api_key if api_key else os.getenv("GEMINI_API_KEY")
    key_source = "user" if api_key else ("server" if final_key else "none")
    
    result = {
        "status": "success",
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents),
        "has_api_key": bool(final_key),
        "key_source": key_source,
    }
    
    # If we have an API key, analyze with AI
    if final_key:
        ai_result = await analyze_homework_with_ai(contents, final_key)
        if ai_result["success"]:
            result["analysis"] = ai_result["analysis"]
            result["message"] = "Image analyzed successfully!"
        else:
            result["message"] = f"Upload successful but AI analysis failed: {ai_result['error']}"
    else:
        result["message"] = "Image uploaded but no API key available for AI analysis."
    
    return result

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
