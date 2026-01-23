/**
 * Socratic Parent - Frontend Application
 * Handles file upload, camera capture, and API communication
 */

// ===== Authentication =====
function getToken() {
    return localStorage.getItem('auth_token');
}

function logout() {
    localStorage.removeItem('auth_token');
    window.location.href = '/';
}

async function checkAuth() {
    const token = getToken();
    if (!token) {
        window.location.href = '/login.html';
        return false;
    }
    
    try {
        const response = await fetch('/api/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            localStorage.removeItem('auth_token');
            window.location.href = '/login.html';
            return false;
        }
        
        const user = await response.json();
        updateUserInfo(user);
        return true;
    } catch (error) {
        console.error('Auth check failed:', error);
        window.location.href = '/';
        return false;
    }
}

function updateUserInfo(user) {
    const userInfoEl = document.getElementById('userInfo');
    if (userInfoEl && user.username) {
        userInfoEl.textContent = `Logged in as: ${user.username}`;
    }
}

// ===== State Management =====
let selectedFile = null;
let cameraStream = null;
let solutionSteps = [];
let currentStepIndex = 0;
let sessionId = null;  // Store session ID

// ===== Initialize Session =====
async function initializeSession() {
    try {
        const token = getToken();
        const response = await fetch('/session', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        sessionId = data.session_id;
        console.log('Session initialized:', sessionId);
    } catch (error) {
        console.warn('Failed to initialize session:', error);
        // Continue anyway - backend will create one on first analyze
    }
}

// ===== DOM Elements =====
const elements = {
    // Upload Section
    uploadSection: document.getElementById('uploadSection'),
    dropZone: document.getElementById('dropZone'),
    fileInput: document.getElementById('fileInput'),
    browseBtn: document.getElementById('browseBtn'),
    imagePreview: document.getElementById('imagePreview'),
    previewImg: document.getElementById('previewImg'),
    removeBtn: document.getElementById('removeBtn'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    gradeSelect: document.getElementById('gradeSelect'),
    
    // Camera
    cameraBtn: document.getElementById('cameraBtn'),
    cameraModal: document.getElementById('cameraModal'),
    cameraStream: document.getElementById('cameraStream'),
    cameraCanvas: document.getElementById('cameraCanvas'),
    captureBtn: document.getElementById('captureBtn'),
    closeCameraBtn: document.getElementById('closeCameraBtn'),
    cancelCameraBtn: document.getElementById('cancelCameraBtn'),
    
    // Loading Section
    loadingSection: document.getElementById('loadingSection'),
    
    // Results Section
    resultsSection: document.getElementById('resultsSection'),
    subjectText: document.getElementById('subjectText'),
    foundationQuestion: document.getElementById('foundationQuestion'),
    bridgeQuestion: document.getElementById('bridgeQuestion'),
    masteryQuestion: document.getElementById('masteryQuestion'),
    behavioralTip: document.getElementById('behavioralTip'),
    newAnalysisBtn: document.getElementById('newAnalysisBtn'),
    showExampleBtn: document.getElementById('showExampleBtn'),
    exampleSection: document.getElementById('exampleSection'),
    exampleContent: document.getElementById('exampleContent'),
    
    // Solution Steps
    showStepsBtn: document.getElementById('showStepsBtn'),
    stepsSection: document.getElementById('stepsSection'),
    stepsContainer: document.getElementById('stepsContainer'),
    nextStepBtn: document.getElementById('nextStepBtn'),
    resetStepsBtn: document.getElementById('resetStepsBtn'),
    
    // Error Section
    errorSection: document.getElementById('errorSection'),
    errorMessage: document.getElementById('errorMessage'),
    retryBtn: document.getElementById('retryBtn'),
};

// ===== View Management =====
function showSection(sectionName) {
    // Hide all sections
    elements.uploadSection.classList.add('hidden');
    elements.loadingSection.classList.add('hidden');
    elements.resultsSection.classList.add('hidden');
    elements.errorSection.classList.add('hidden');
    
    // Show requested section
    switch (sectionName) {
        case 'upload':
            elements.uploadSection.classList.remove('hidden');
            break;
        case 'loading':
            elements.loadingSection.classList.remove('hidden');
            break;
        case 'results':
            elements.resultsSection.classList.remove('hidden');
            break;
        case 'error':
            elements.errorSection.classList.remove('hidden');
            break;
    }
}

// ===== File Upload Handlers =====
function handleFileSelect(file) {
    if (!file || !file.type.startsWith('image/')) {
        showError('Please select a valid image file');
        return;
    }
    
    selectedFile = file;
    
    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        elements.previewImg.src = e.target.result;
        elements.dropZone.querySelector('.drop-zone-content').style.display = 'none';
        elements.imagePreview.classList.remove('hidden');
        elements.analyzeBtn.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
}

// Browse button click
elements.browseBtn.addEventListener('click', (e) => {
    e.preventDefault();
    elements.fileInput.click();
});

// File input change
elements.fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        handleFileSelect(file);
    }
});

// Drag and drop handlers
elements.dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.dropZone.classList.add('drag-over');
});

elements.dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    elements.dropZone.classList.remove('drag-over');
});

elements.dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.dropZone.classList.remove('drag-over');
    
    const file = e.dataTransfer.files[0];
    if (file) {
        handleFileSelect(file);
    }
});

// Click on drop zone to browse
elements.dropZone.addEventListener('click', (e) => {
    if (e.target === elements.dropZone || e.target.closest('.drop-zone-content')) {
        elements.fileInput.click();
    }
});

// Remove image
elements.removeBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    selectedFile = null;
    elements.fileInput.value = '';
    elements.previewImg.src = '';
    elements.imagePreview.classList.add('hidden');
    elements.dropZone.querySelector('.drop-zone-content').style.display = 'flex';
    elements.analyzeBtn.classList.add('hidden');
});

// ===== Camera Handlers =====
elements.cameraBtn.addEventListener('click', async () => {
    try {
        // Request camera access
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' } // Prefer back camera on mobile
        });
        
        elements.cameraStream.srcObject = cameraStream;
        elements.cameraModal.classList.remove('hidden');
    } catch (error) {
        console.error('Camera access error:', error);
        showError('Unable to access camera. Please check permissions or use file upload instead.');
    }
});

// Capture photo
elements.captureBtn.addEventListener('click', () => {
    const video = elements.cameraStream;
    const canvas = elements.cameraCanvas;
    
    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw video frame to canvas
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    
    // Convert canvas to blob
    canvas.toBlob((blob) => {
        const file = new File([blob], 'homework-photo.jpg', { type: 'image/jpeg' });
        handleFileSelect(file);
        closeCameraModal();
    }, 'image/jpeg', 0.9);
});

// Close camera modal
function closeCameraModal() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    elements.cameraModal.classList.add('hidden');
}

elements.closeCameraBtn.addEventListener('click', closeCameraModal);
elements.cancelCameraBtn.addEventListener('click', closeCameraModal);

// ===== API Communication =====
async function analyzeHomework() {
    if (!selectedFile) {
        showError('Please select an image first');
        return;
    }
    
    // Show loading state
    showSection('loading');
    
    try {
        // Prepare form data
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        const grade = elements.gradeSelect.value;
        if (grade) {
            formData.append('grade', grade);
        }
        
        // Include session ID if available
        if (sessionId) {
            formData.append('session_id', sessionId);
        }
        
        const token = getToken();
        
        // Call API with proper error handling
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData,
            headers: {
                'Accept': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        }).catch(err => {
            throw new Error('Cannot connect to server. Please ensure the application is running.');
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Server error: ${response.status}`);
        }
        
        const result = await response.json();
        displayResults(result);
        
    } catch (error) {
        console.error('Analysis error:', error);
        const errorMsg = error.message || 'Connection failed. Please check if the server is running.';
        
        // Add helpful context for specific errors
        let helpText = '';
        if (errorMsg.includes('missing required fields')) {
            helpText = ' The AI response was incomplete. This is usually temporary - please try again.';
        } else if (errorMsg.includes('parsing error')) {
            helpText = ' The AI response format was invalid. Please try uploading the image again.';
        }
        
        showError(errorMsg + helpText);
    }
}

// Analyze button click
elements.analyzeBtn.addEventListener('click', analyzeHomework);

// ===== Results Display =====
function displayResults(data) {
    // Populate results - use innerHTML to allow math rendering
    elements.subjectText.textContent = data.subject || 'General Study';
    elements.foundationQuestion.innerHTML = formatMathContent(data.questions.foundation || '');
    elements.bridgeQuestion.innerHTML = formatMathContent(data.questions.bridge || '');
    elements.masteryQuestion.innerHTML = formatMathContent(data.questions.mastery || '');
    elements.behavioralTip.textContent = data.behavioral_tip || '';
    
    // Populate example approach if available
    if (data.example_approach) {
        elements.exampleContent.innerHTML = `<p>${data.example_approach}</p>`;
        elements.showExampleBtn.style.display = 'inline-flex';
    } else {
        elements.exampleContent.innerHTML = `
            <p><strong>Concept Overview:</strong> The problem requires understanding the relationship between the known and unknown elements.</p>
            <p><strong>Common Mistakes:</strong> Students often skip foundational steps or rush to the answer.</p>
            <p><strong>Guiding Principle:</strong> Break the problem into smaller parts and verify each step.</p>
            <p><strong>What NOT to say:</strong> Never give the final answer. Let them discover it through questioning.</p>
        `;
        elements.showExampleBtn.style.display = 'inline-flex';
    }
    
    // Render math in the displayed content
    setTimeout(() => {
        renderMath(document.getElementById('resultsSection'));
    }, 200);
    
    // Store solution steps if available
    if (data.solution_steps && data.solution_steps.length > 0) {
        solutionSteps = data.solution_steps;
        elements.showStepsBtn.style.display = 'inline-flex';
    } else {
        // Default fallback steps
        solutionSteps = [
            "Read the problem carefully and identify what is being asked.",
            "List out what information you already know from the problem.",
            "Think about what concept or formula applies to this type of problem.",
            "Break the problem into smaller, manageable parts.",
            "Work through each part step-by-step, checking your work as you go.",
            "Verify your final answer makes sense in the context of the problem."
        ];
        elements.showStepsBtn.style.display = 'inline-flex';
    }
    
    // Reset sections
    currentStepIndex = 0;
    elements.stepsContainer.innerHTML = '';
    elements.nextStepBtn.classList.remove('hidden');
    elements.resetStepsBtn.classList.add('hidden');
    
    // Reset example section to hidden
    elements.exampleSection.classList.add('hidden');
    elements.showExampleBtn.textContent = '💡 Need Help? Show Example Approach';
    
    // Show results section
    showSection('results');
}

// New analysis button
elements.newAnalysisBtn.addEventListener('click', () => {
    // Reset state
    selectedFile = null;
    elements.fileInput.value = '';
    elements.previewImg.src = '';
    elements.imagePreview.classList.add('hidden');
    elements.dropZone.querySelector('.drop-zone-content').style.display = 'flex';
    elements.analyzeBtn.classList.add('hidden');
    elements.gradeSelect.value = '';
    elements.exampleSection.classList.add('hidden');
    
    // Show upload section
    showSection('upload');
});

// Solution Steps - Show/Hide button
elements.showStepsBtn.addEventListener('click', () => {
    const isHidden = elements.stepsSection.classList.contains('hidden');
    
    if (isHidden) {
        elements.stepsSection.classList.remove('hidden');
        elements.showStepsBtn.textContent = '🔼 Hide Solution Steps';
    } else {
        elements.stepsSection.classList.add('hidden');
        elements.showStepsBtn.textContent = '📋 Show Solution Steps';
    }
});

// Solution Steps - Next Step button
elements.nextStepBtn.addEventListener('click', () => {
    if (currentStepIndex < solutionSteps.length) {
        renderStep(solutionSteps[currentStepIndex], currentStepIndex + 1);
        currentStepIndex++;
        
        // If all steps shown, hide next button and show reset button
        if (currentStepIndex >= solutionSteps.length) {
            elements.nextStepBtn.classList.add('hidden');
            elements.resetStepsBtn.classList.remove('hidden');
            
            // Show completion message
            const completionDiv = document.createElement('div');
            completionDiv.className = 'steps-complete';
            completionDiv.innerHTML = '✅ All steps revealed! Review the workings and try the practice question.';
            elements.stepsContainer.appendChild(completionDiv);
        }
    }
});

// Solution Steps - Reset button
elements.resetStepsBtn.addEventListener('click', () => {
    currentStepIndex = 0;
    elements.stepsContainer.innerHTML = '';
    elements.nextStepBtn.classList.remove('hidden');
    elements.resetStepsBtn.classList.add('hidden');
});

// Helper function to render a single step with LaTeX support
function renderStep(stepData, stepNumber) {
    const stepDiv = document.createElement('div');
    stepDiv.className = 'step-item';
    
    // Format the step content - handle both old format (string) and new format (object)
    let stepTitle = stepData.title || `Step ${stepNumber}`;
    const stepContent = stepData.content || stepData;
    
    // Clean up title - remove "Step X:" prefix if present since we have the badge
    stepTitle = stepTitle.replace(/^Step \d+:\s*/i, '');
    
    stepDiv.innerHTML = `
        <div class="step-header">
            <span class="step-number">${stepNumber}</span>
            <span class="step-title">${stepTitle}</span>
        </div>
        <div class="step-content">${formatMathContent(stepContent)}</div>
    `;
    elements.stepsContainer.appendChild(stepDiv);
    
    // Render any LaTeX math in the new step
    setTimeout(() => {
        renderMath(stepDiv);
    }, 200);
}

// Format content to highlight mathematical expressions and working
function formatMathContent(content) {
    if (!content) return '';
    
    // First, process markdown-style bold **text** -> <strong>text</strong>
    content = content.replace(/\*\*([^*]+?)\*\*/g, '<strong>$1</strong>');
    
    // Convert string to paragraphs for better formatting
    let formatted = content
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
        .map(line => {
            // Check if line looks like a calculation step (contains =, +, -, ×, ÷)
            if (/[=+\-×÷]/.test(line) && !line.startsWith('<strong>')) {
                return `<div class="calculation-step">${line}</div>`;
            }
            return `<p>${line}</p>`;
        })
        .join('');
    
    return formatted;
}

// Show example approach button
elements.showExampleBtn.addEventListener('click', () => {
    const isHidden = elements.exampleSection.classList.contains('hidden');
    
    if (isHidden) {
        elements.exampleSection.classList.remove('hidden');
        elements.showExampleBtn.textContent = '🔼 Hide Example Approach';
    } else {
        elements.exampleSection.classList.add('hidden');
        elements.showExampleBtn.textContent = '💡 Need Help? Show Example Approach';
    }
});

// ===== Error Handling =====
function showError(message) {
    elements.errorMessage.textContent = message;
    
    // Add retry information
    const retryNote = document.createElement('p');
    retryNote.style.marginTop = '1rem';
    retryNote.style.fontSize = '0.9rem';
    retryNote.textContent = '💡 Tip: If this keeps happening, try a clearer photo or a different angle.';
    elements.errorMessage.appendChild(retryNote);
    
    showSection('error');
}

elements.retryBtn.addEventListener('click', () => {
    showSection('upload');
});

// ===== Health Check on Load =====
async function checkHealth() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        if (!data.ai_configured) {
            console.warn('AI not configured. Using fallback responses.');
        }
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    showSection('upload');
});

// ===== Keyboard Shortcuts =====
document.addEventListener('keydown', (e) => {
    // Escape key closes camera modal
    if (e.key === 'Escape' && !elements.cameraModal.classList.contains('hidden')) {
        closeCameraModal();
    }
    
    // Enter key triggers analysis if file is selected
    if (e.key === 'Enter' && selectedFile && !elements.analyzeBtn.classList.contains('hidden')) {
        analyzeHomework();
    }
});

// ===== Prevent accidental page unload =====
window.addEventListener('beforeunload', (e) => {
    if (selectedFile && !elements.resultsSection.classList.contains('hidden')) {
        // Don't prevent if already showing results
        return;
    }
    
    if (selectedFile) {
        e.preventDefault();
        e.returnValue = '';
    }
});

// ===== Initialize on page load =====
document.addEventListener('DOMContentLoaded', async () => {
    const isAuthenticated = await checkAuth();
    if (isAuthenticated) {
        initializeSession();
    }
    
    // Wait for KaTeX to be fully loaded
    const waitForKaTeX = setInterval(() => {
        if (typeof renderMathInElement !== 'undefined') {
            clearInterval(waitForKaTeX);
            console.log('KaTeX loaded and ready');
        }
    }, 100);
});

// Helper function to render math in any element
function renderMath(element) {
    if (typeof renderMathInElement !== 'undefined') {
        try {
            renderMathInElement(element, {
                delimiters: [
                    {left: '$$', right: '$$', display: true},
                    {left: '$', right: '$', display: false}
                ],
                throwOnError: false,
                trust: true
            });
        } catch (e) {
            console.warn('KaTeX rendering error:', e);
        }
    }
}
