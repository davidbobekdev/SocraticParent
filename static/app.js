/**
 * Socratic Parent - Frontend Application
 * Handles file upload, camera capture, and API communication
 */

// ===== Math Formatting Utilities =====
function formatMathContent(text) {
    if (!text) return '';
    
    // Split into paragraphs
    let paragraphs = text.split('\n').filter(p => p.trim());
    
    // Process each paragraph
    let formatted = paragraphs.map(para => {
        para = para.trim();
        
        // Skip if empty
        if (!para) return '';
        
        // Check if it's a list item
        if (para.match(/^[\*\-\d+\.]\s/)) {
            // It's a list item - wrap in <li>
            let content = para.replace(/^[\*\-\d+\.]\s+/, '');
            content = content.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
            return `<li>${content}</li>`;
        } else {
            // Regular paragraph - convert **bold**
            para = para.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
            return `<p>${para}</p>`;
        }
    }).join('\n');
    
    // Wrap consecutive <li> elements in <ul>
    formatted = formatted.replace(/(<li>.*?<\/li>\n?)+/gs, match => {
        return `<ul>${match}</ul>`;
    });
    
    return formatted;
}

function renderMath(element) {
    if (typeof renderMathInElement !== 'undefined') {
        try {
            renderMathInElement(element, {
                delimiters: [
                    {left: "$$", right: "$$", display: true},
                    {left: "$", right: "$", display: false}
                ],
                throwOnError: false,
                strict: false
            });
        } catch (e) {
            console.error('KaTeX rendering error:', e);
        }
    }
}

// ===== Authentication =====
function getToken() {
    return localStorage.getItem('auth_token');
}

function logout() {
    localStorage.removeItem('auth_token');
    window.location.href = '/';
}

// ===== Trial Mode Detection =====
function isTrialMode() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('trial') === '1';
}

function hasUsedTrial() {
    return localStorage.getItem('trial_used') === 'true';
}

function markTrialUsed() {
    localStorage.setItem('trial_used', 'true');
}

function getTrialId() {
    let trialId = localStorage.getItem('trial_id');
    if (!trialId) {
        trialId = 'trial_' + Math.random().toString(36).substring(2, 15) + Date.now();
        localStorage.setItem('trial_id', trialId);
    }
    return trialId;
}

async function checkAuth() {
    // Check if upgrade parameter - redirect to login if not authenticated
    const urlParams = new URLSearchParams(window.location.search);
    const wantsUpgrade = urlParams.get('upgrade') === '1';
    
    const token = getToken();
    if (wantsUpgrade && !token) {
        // User wants to upgrade but isn't logged in - send to login
        window.location.href = '/login.html?redirect=app&upgrade=1';
        return false;
    }
    
    // Check if trial mode
    if (isTrialMode()) {
        // Trial mode - allow access without auth
        console.log('Trial mode active');
        
        // Hide user-specific UI elements
        const userInfoEl = document.getElementById('userInfo');
        const usageInfoEl = document.getElementById('usageInfo');
        const upgradeBtn = document.getElementById('upgradeBtn');
        const settingsIcon = document.querySelector('.settings-icon');
        const logoutBtn = document.querySelector('.logout-btn');
        
        if (userInfoEl) userInfoEl.textContent = '🎁 Free Trial';
        if (usageInfoEl) usageInfoEl.style.display = 'none';
        if (upgradeBtn) upgradeBtn.style.display = 'none';
        if (settingsIcon) settingsIcon.style.display = 'none';
        if (logoutBtn) logoutBtn.textContent = 'Sign Up';
        if (logoutBtn) logoutBtn.onclick = () => window.location.href = '/login.html';
        
        // Show trial upgrade banner
        const trialBanner = document.getElementById('trialUpgradeBanner');
        if (trialBanner) trialBanner.style.display = 'block';
        
        // Add home button for trial users
        const headerRight = document.querySelector('.header-right');
        if (headerRight && !document.getElementById('homeBtn')) {
            const homeBtn = document.createElement('button');
            homeBtn.id = 'homeBtn';
            homeBtn.className = 'home-btn';
            homeBtn.innerHTML = '🏠';
            homeBtn.title = 'Back to Home';
            homeBtn.onclick = () => window.location.href = '/';
            headerRight.insertBefore(homeBtn, headerRight.firstChild);
        }
        
        return true; // Allow access in trial mode
    }
    
    if (!token) {
        window.location.href = '/';
        return false;
    }
    
    try {
        const response = await fetch('/api/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            localStorage.removeItem('auth_token');
            window.location.href = '/';
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
        
        // Fetch user status for premium/usage info
        await fetchUserStatus();
    } catch (error) {
        console.warn('Failed to initialize session:', error);
        // Continue anyway - backend will create one on first analyze
    }
}

// ===== Premium & Payment Functions =====
async function fetchUserStatus() {
    try {
        const token = getToken();
        const response = await fetch('/api/user/status', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('User status fetched:', data);
            updateUsageDisplay(data);
            return data;
        } else {
            console.error('Failed to fetch user status:', response.status);
        }
    } catch (error) {
        console.error('Failed to fetch user status:', error);
    }
}

function updateUsageDisplay(data) {
    const usageInfo = elements.usageInfo;
    const upgradeBtn = elements.upgradeBtn;
    
    console.log('Updating usage display with:', data);
    
    if (data.is_premium) {
        usageInfo.textContent = '∞ Unlimited';
        usageInfo.classList.add('unlimited');
        // Hide upgrade button for premium users
        if (upgradeBtn) {
            upgradeBtn.classList.remove('show');
        }
        console.log('User is premium - showing unlimited, hiding upgrade button');
    } else {
        // Backend returns 'scans_left', not 'daily_scans_left'
        const scansLeft = data.scans_left !== undefined ? data.scans_left : (data.daily_scans_left || 0);
        usageInfo.textContent = `${scansLeft} scan${scansLeft !== 1 ? 's' : ''} left`;
        usageInfo.classList.remove('unlimited');
        // Always show upgrade button for non-premium users
        if (upgradeBtn) {
            upgradeBtn.classList.add('show');
        }
        console.log('User is free tier - scans left:', scansLeft);
    }
}

async function handlePaymentSuccess() {
    console.log('Payment successful! Processing immediately...');
    // Wait just 500ms for webhook to process
    await new Promise(resolve => setTimeout(resolve, 500));
    console.log('Fetching updated user status...');
    const status = await fetchUserStatus();
    
    // Show thank you message
    alert('🎉 Thank you for joining!\n\nYou can now enjoy unlimited usage of this tool.');
    
    console.log('Performing hard reload...');
    // Force hard reload to clear all caches
    window.location.href = window.location.href.split('?')[0] + '?t=' + Date.now();
}

async function openPaddleCheckout() {
    trackEvent('upgrade_clicked');
    
    try {
        if (typeof Paddle === 'undefined') {
            alert('Payment system not loaded. Please refresh the page.');
            trackEvent('payment_error', { error: 'paddle_not_loaded' });
            return;
        }
        
        // Get Paddle config from backend
        const token = getToken();
        const response = await fetch('/api/paddle/client-token', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            throw new Error('Failed to get payment configuration');
        }
        
        const config = await response.json();
        
        trackEvent('checkout_opened');
        
        // Initialize Paddle with sandbox environment (until account is approved)
        Paddle.Environment.set('sandbox');
        Paddle.Initialize({ 
            token: config.client_token,
            eventCallback: function(data) {
                console.log('Paddle event:', data);
                
                // Handle checkout completion
                if (data.name === 'checkout.completed') {
                    console.log('Payment completed! Processing...');
                    trackEvent('payment_completed');
                    handlePaymentSuccess();
                }
            }
        });
        
        // Open checkout
        Paddle.Checkout.open({
            items: [{ priceId: config.price_id, quantity: 1 }],
            customer: { email: config.user_email },
            customData: { user_id: config.user_id }
        });
        
    } catch (error) {
        console.error('Payment error:', error);
        trackEvent('payment_error', { error: error.message });
        alert('Unable to open checkout. Please try again or contact support.');
    }
}

function showPaywall(paywallData) {
    // Display the results section with blurred content
    showSection('results');
    
    // Show paywall overlay if it exists
    if (elements.paywallOverlay) {
        elements.paywallOverlay.classList.remove('hidden');
    }
    
    // Update usage display
    if (paywallData.usage) {
        updateUsageDisplay(paywallData.usage);
    }
}

// ===== Trial Modals =====
function showTrialExhaustedModal() {
    showSection('upload');
    
    // Remove any existing modal first
    const existingModal = document.getElementById('trialExhaustedModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create fresh modal with absolute positioning
    const modal = document.createElement('div');
    modal.id = 'trialExhaustedModal';
    modal.style.cssText = `
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        background: rgba(30, 41, 59, 0.8) !important;
        backdrop-filter: blur(10px) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        z-index: 999999 !important;
        opacity: 0;
        transition: opacity 0.3s ease;
        margin: 0 !important;
        padding: 20px !important;
        box-sizing: border-box !important;
    `;
    
    modal.innerHTML = `
        <div class="trial-modal-content" style="
            background: white !important;
            border-radius: 24px !important;
            padding: 48px 40px !important;
            max-width: 440px !important;
            width: 90% !important;
            max-height: 90vh !important;
            text-align: center !important;
            box-shadow: 0 25px 80px rgba(0, 0, 0, 0.25), 0 0 1px rgba(0, 0, 0, 0.1) !important;
            transform: scale(0.95);
            transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            position: relative !important;
            margin: 0 auto !important;
            overflow-y: auto !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
        ">
            <div class="trial-modal-icon" style="font-size: 4rem; margin-bottom: 20px; line-height: 1;">🎯</div>
            <h2 style="color: #1e293b; margin-bottom: 12px; font-size: 1.75rem; font-weight: 700; line-height: 1.3;">You've Used Your Free Trial!</h2>
            <p style="color: #64748b; margin-bottom: 32px; font-size: 1.05rem; line-height: 1.6;">You've seen how Socratic Parent works. Now unlock unlimited access!</p>
            <ul style="list-style: none; padding: 0; margin: 28px 0 32px 0; text-align: left;">
                <li style="padding: 10px 0; color: #1e293b; font-size: 1rem; display: flex; align-items: center; gap: 10px;">
                    <span style="color: #10b981; font-size: 1.2rem;">✅</span>
                    <span style="font-weight: 500;">5 free scans a day</span>
                </li>
                <li style="padding: 10px 0; color: #1e293b; font-size: 1rem; display: flex; align-items: center; gap: 10px;">
                    <span style="color: #10b981; font-size: 1.2rem;">✅</span>
                    <span style="font-weight: 500;">Full coaching scripts</span>
                </li>
                <li style="padding: 10px 0; color: #1e293b; font-size: 1rem; display: flex; align-items: center; gap: 10px;">
                    <span style="color: #10b981; font-size: 1.2rem;">✅</span>
                    <span style="font-weight: 500;">All subjects supported</span>
                </li>
                <li style="padding: 10px 0; color: #1e293b; font-size: 1rem; display: flex; align-items: center; gap: 10px;">
                    <span style="color: #10b981; font-size: 1.2rem;">✅</span>
                    <span style="font-weight: 500;">Step-by-step solutions</span>
                </li>
            </ul>
            <button onclick="window.location.href='/login.html'" style="
                display: block;
                width: 100%;
                padding: 16px 24px;
                margin: 0 0 12px 0;
                border: none;
                border-radius: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                font-size: 1.05rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
                font-family: inherit;
            " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(102, 126, 234, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.3)';">
                📧 Create Free Account
            </button>
            <button onclick="closeTrialModal()" style="
                display: block;
                width: 100%;
                padding: 14px 24px;
                margin: 0 0 20px 0;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                background: white;
                color: #64748b;
                font-size: 0.95rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                font-family: inherit;
            " onmouseover="this.style.borderColor='#cbd5e1'; this.style.color='#475569';" onmouseout="this.style.borderColor='#e2e8f0'; this.style.color='#64748b';">
                Maybe Later
            </button>
            <p style="color: #94a3b8; font-size: 0.9rem; margin: 0; line-height: 1.4;">No credit card required</p>
        </div>
    `;
    
    // Append directly to document.documentElement to bypass all containers
    document.documentElement.appendChild(modal);
    
    // Force reflow then show
    setTimeout(() => {
        modal.style.opacity = '1';
        const content = modal.querySelector('.trial-modal-content');
        if (content) {
            content.style.transform = 'scale(1)';
        }
    }, 10);
}

function showSignupPromptModal() {
    // Remove any existing modal first
    const existingModal = document.getElementById('signupPromptModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create fresh modal with inline styles
    const modal = document.createElement('div');
    modal.id = 'signupPromptModal';
    modal.style.cssText = `
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        background: rgba(30, 41, 59, 0.8) !important;
        backdrop-filter: blur(10px) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        z-index: 999999 !important;
        opacity: 0;
        transition: opacity 0.3s ease;
        margin: 0 !important;
        padding: 20px !important;
        box-sizing: border-box !important;
    `;
    
    modal.innerHTML = `
        <div class="trial-modal-content" style="
            background: white !important;
            border-radius: 24px !important;
            padding: 48px 40px !important;
            max-width: 440px !important;
            width: 90% !important;
            max-height: 90vh !important;
            text-align: center !important;
            box-shadow: 0 25px 80px rgba(0, 0, 0, 0.25), 0 0 1px rgba(0, 0, 0, 0.1) !important;
            transform: scale(0.95);
            transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            position: relative !important;
            margin: 0 auto !important;
            overflow-y: auto !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
        ">
            <div class="trial-modal-icon" style="font-size: 4rem; margin-bottom: 20px; line-height: 1;">🎉</div>
            <h2 style="color: #1e293b; margin-bottom: 12px; font-size: 1.75rem; font-weight: 700; line-height: 1.3;">That Was Your Free Preview!</h2>
            <p style="color: #64748b; margin-bottom: 32px; font-size: 1.05rem; line-height: 1.6;">Love it? Create a free account to keep using Socratic Parent!</p>
            <ul style="list-style: none; padding: 0; margin: 28px 0 32px 0; text-align: left;">
                <li style="padding: 10px 0; color: #1e293b; font-size: 1rem; display: flex; align-items: center; gap: 10px;">
                    <span style="color: #10b981; font-size: 1.2rem;">✅</span>
                    <span style="font-weight: 500;">5 free scans every day</span>
                </li>
                <li style="padding: 10px 0; color: #1e293b; font-size: 1rem; display: flex; align-items: center; gap: 10px;">
                    <span style="color: #10b981; font-size: 1.2rem;">✅</span>
                    <span style="font-weight: 500;">Step-by-step coaching scripts</span>
                </li>
                <li style="padding: 10px 0; color: #1e293b; font-size: 1rem; display: flex; align-items: center; gap: 10px;">
                    <span style="color: #10b981; font-size: 1.2rem;">✅</span>
                    <span style="font-weight: 500;">All subjects supported</span>
                </li>
                <li style="padding: 10px 0; color: #1e293b; font-size: 1rem; display: flex; align-items: center; gap: 10px;">
                    <span style="color: #10b981; font-size: 1.2rem;">✅</span>
                    <span style="font-weight: 500;">Never store your homework photos</span>
                </li>
            </ul>
            <button onclick="window.location.href='/login.html'" style="
                display: block;
                width: 100%;
                padding: 16px 24px;
                margin: 0 0 12px 0;
                border: none;
                border-radius: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                font-size: 1.05rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
                font-family: inherit;
            " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(102, 126, 234, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.3)';">
                🚀 Create Free Account
            </button>
            <button onclick="closeTrialModal()" style="
                display: block;
                width: 100%;
                padding: 14px 24px;
                margin: 0 0 20px 0;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                background: white;
                color: #64748b;
                font-size: 0.95rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                font-family: inherit;
            " onmouseover="this.style.borderColor='#cbd5e1'; this.style.color='#475569';" onmouseout="this.style.borderColor='#e2e8f0'; this.style.color='#64748b';">
                Keep Browsing Results
            </button>
            <p style="color: #94a3b8; font-size: 0.9rem; margin: 0; line-height: 1.4;">Takes 10 seconds • No credit card</p>
        </div>
    `;
    
    // Append directly to document.documentElement to bypass all containers
    document.documentElement.appendChild(modal);
    
    // Force reflow then show
    setTimeout(() => {
        modal.style.opacity = '1';
        const content = modal.querySelector('.trial-modal-content');
        if (content) {
            content.style.transform = 'scale(1)';
        }
    }, 10);
}

function closeTrialModal() {
    const exhaustedModal = document.getElementById('trialExhaustedModal');
    const promptModal = document.getElementById('signupPromptModal');
    
    if (exhaustedModal) {
        exhaustedModal.style.opacity = '0';
        const content = exhaustedModal.querySelector('.trial-modal-content');
        if (content) {
            content.style.transform = 'scale(0.9)';
        }
        // Remove after animation
        setTimeout(() => {
            if (exhaustedModal.parentNode) {
                exhaustedModal.parentNode.removeChild(exhaustedModal);
            }
        }, 300);
    }
    if (promptModal) {
        promptModal.style.opacity = '0';
        const promptContent = promptModal.querySelector('.trial-modal-content');
        if (promptContent) {
            promptContent.style.transform = 'scale(0.9)';
        }
        setTimeout(() => {
            if (promptModal.parentNode) {
                promptModal.parentNode.removeChild(promptModal);
            }
        }, 300);
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
    
    // Premium elements
    upgradeBtn: document.getElementById('upgradeBtn'),
    usageInfo: document.getElementById('usageInfo'),
    paywallOverlay: document.getElementById('paywallOverlay'),
    paywallUpgradeBtn: document.getElementById('paywallUpgradeBtn'),
    
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
        elements.fileInput.style.display = 'none'; // Hide file input overlay
        elements.imagePreview.classList.remove('hidden');
        elements.analyzeBtn.classList.remove('hidden');
    };
    reader.onerror = (e) => {
        console.error('FileReader error:', e);
        showError('Error reading file');
    };
    reader.readAsDataURL(file);
}

// Browse button click - file input is now an overlay so this just prevents default
if (elements.browseBtn) {
    elements.browseBtn.addEventListener('click', (e) => {
        e.stopPropagation(); // Let the file input overlay handle it
    });
}

// File input change
elements.fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        handleFileSelect(file);
        trackEvent('file_selected', { fileSize: file.size, fileType: file.type });
        // Clear input to allow re-selecting same file next time
        setTimeout(() => {
            e.target.value = '';
        }, 1000);
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

// File input is now an overlay on dropzone, so it handles clicks directly
// Remove dropzone click handler to avoid conflicts

// Remove image
elements.removeBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    selectedFile = null;
    elements.fileInput.value = '';
    elements.fileInput.style.display = 'block'; // Show file input overlay again
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
    
    // Check if trial mode and already used
    if (isTrialMode() && hasUsedTrial()) {
        showTrialExhaustedModal();
        return;
    }
    
    trackEvent('analyze_started', { 
        grade: elements.gradeSelect.value,
        fileSize: selectedFile.size,
        isTrialMode: isTrialMode()
    });
    
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
        
        // Determine endpoint and headers based on mode
        let endpoint = '/analyze';
        let headers = { 'Accept': 'application/json' };
        
        if (isTrialMode()) {
            endpoint = '/analyze-trial';
            formData.append('trial_id', getTrialId());
        } else {
            // Include session ID and auth for regular mode
            if (sessionId) {
                formData.append('session_id', sessionId);
            }
            const token = getToken();
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        // Call API with proper error handling
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData,
            headers: headers
        }).catch(err => {
            throw new Error('Cannot connect to server. Please ensure the application is running.');
        });
        
        // Handle trial exhausted (402)
        if (response.status === 402) {
            const data = await response.json().catch(() => ({}));
            if (data.show_signup || isTrialMode()) {
                markTrialUsed();
                showTrialExhaustedModal();
                return;
            }
            // Regular paywall for authenticated users
            showPaywall(data);
            return;
        }
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Server error: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Handle trial response
        if (result.trial_used) {
            markTrialUsed();
        }
        
        // Update usage display if usage info is included
        if (result.usage) {
            updateUsageDisplay(result.usage);
        }
        
        trackEvent('analyze_success', { 
            subject: result.subject,
            isPremium: result.usage?.is_premium || false,
            isTrial: isTrialMode()
        });
        
        displayResults(result);
        
        // Show signup prompt after displaying results in trial mode
        if (result.show_signup_prompt) {
            setTimeout(() => {
                showSignupPromptModal();
            }, 30000); // Show after 30 seconds to let them fully explore results
        }
        
    } catch (error) {
        console.error('Analysis error:', error);
        const errorMsg = error.message || 'Connection failed. Please check if the server is running.';
        
        trackEvent('analyze_error', { 
            error: errorMsg,
            errorType: error.name || 'UnknownError'
        });
        
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
    // Populate results
    elements.subjectText.textContent = data.subject || 'General Study';
    elements.foundationQuestion.innerHTML = formatMathContent(data.questions.foundation || '');
    elements.bridgeQuestion.innerHTML = formatMathContent(data.questions.bridge || '');
    elements.masteryQuestion.innerHTML = formatMathContent(data.questions.mastery || '');
    elements.behavioralTip.textContent = data.behavioral_tip || '';
    
    // Render math in question elements after a brief delay
    setTimeout(() => {
        renderMath(elements.foundationQuestion);
        renderMath(elements.bridgeQuestion);
        renderMath(elements.masteryQuestion);
    }, 100);
    
    // Populate example approach if available
    if (data.example_approach) {
        const formattedExample = formatMathContent(data.example_approach);
        elements.exampleContent.innerHTML = formattedExample;
        elements.showExampleBtn.style.display = 'inline-flex';
        
        // Render math in example content
        setTimeout(() => {
            renderMath(elements.exampleContent);
        }, 100);
    } else {
        elements.exampleContent.innerHTML = `
            <p><strong>Concept Overview:</strong> The problem requires understanding the relationship between the known and unknown elements.</p>
            <p><strong>Common Mistakes:</strong> Students often skip foundational steps or rush to the answer.</p>
            <p><strong>Guiding Principle:</strong> Break the problem into smaller parts and verify each step.</p>
            <p><strong>What NOT to say:</strong> Never give the final answer. Let them discover it through questioning.</p>
        `;
        elements.showExampleBtn.style.display = 'inline-flex';
    }
    
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
    
    // Reset upload state for next image
    selectedFile = null;
    elements.fileInput.value = '';
    elements.fileInput.style.display = 'block'; // Show file input overlay again
    elements.previewImg.src = '';
    elements.imagePreview.classList.add('hidden');
    elements.dropZone.querySelector('.drop-zone-content').style.display = 'flex';
    elements.analyzeBtn.classList.add('hidden');
    
    // Show results section
    showSection('results');
}

// New analysis button
elements.newAnalysisBtn.addEventListener('click', (e) => {
    // In trial mode, if trial is used, show signup modal
    if (isTrialMode() && hasUsedTrial()) {
        showTrialExhaustedModal();
        return;
    }
    
    // Reset state
    selectedFile = null;
    elements.fileInput.value = '';
    elements.fileInput.style.display = 'block'; // Show file input overlay
    elements.previewImg.src = '';
    elements.imagePreview.classList.add('hidden');
    elements.dropZone.querySelector('.drop-zone-content').style.display = 'flex';
    elements.analyzeBtn.classList.add('hidden');
    elements.gradeSelect.value = '';
    elements.exampleSection.classList.add('hidden');
    
    // Show upload section
    showSection('upload');
    
    // Remove focus to prevent purple background
    e.target.blur();
});

// Solution Steps - Show/Hide button
elements.showStepsBtn.addEventListener('click', (e) => {
    const isHidden = elements.stepsSection.classList.contains('hidden');
    
    if (isHidden) {
        // Close example section if it's open
        elements.exampleSection.classList.add('hidden');
        elements.showExampleBtn.textContent = '💡 Need Help? Show Example Approach';
        
        // Open steps section
        elements.stepsSection.classList.remove('hidden');
        elements.showStepsBtn.textContent = '🔼 Hide Solution Steps';
    } else {
        elements.stepsSection.classList.add('hidden');
        elements.showStepsBtn.textContent = '📋 Show Solution Steps';
    }
    
    // Remove focus to prevent purple background
    e.target.blur();
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
            completionDiv.innerHTML = '✅ All steps revealed! Review and try applying them.';
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

// Helper function to render a single step
function renderStep(stepData, stepNumber) {
    const stepDiv = document.createElement('div');
    stepDiv.className = 'step-item';
    
    // Handle both old string format and new object format
    let stepTitle = '';
    let stepContent = '';
    
    if (typeof stepData === 'string') {
        stepContent = stepData;
    } else if (stepData && typeof stepData === 'object') {
        stepTitle = stepData.title || '';
        stepContent = stepData.content || '';
    }
    
    // Clean up title - remove redundant "Step X:" prefix if present
    if (stepTitle) {
        stepTitle = stepTitle.replace(/^Step\s*\d+\s*[:\-]\s*/i, '');
    }
    
    // Check if this is a final answer step
    const isFinalAnswer = stepTitle.toLowerCase().includes('final answer') || 
                          stepTitle.toLowerCase().includes('conclusion') ||
                          stepTitle.toLowerCase().includes('verify');
    
    // Format math content
    const formattedContent = formatMathContent(stepContent);
    
    // Extract final answer value if present - look for the answer in the content
    let finalAnswerHtml = '';
    if (isFinalAnswer && stepContent.toLowerCase().includes('final answer')) {
        // Match patterns like "final answer is 9" or "final answer is: 9" 
        // Avoid capturing LaTeX $ symbols
        const answerMatch = stepContent.match(/final answer is[:\s]*\$?([^$\n.]+)/i);
        if (answerMatch) {
            let answer = answerMatch[1].trim();
            // Clean up any remaining LaTeX or punctuation
            answer = answer.replace(/\$/g, '').replace(/\\[a-z]+/gi, '').trim();
            if (answer && answer.length < 20) {  // Sanity check
                finalAnswerHtml = `<div class="final-answer">🎯 Final Answer<strong>${answer}</strong></div>`;
            }
        }
    }
    
    stepDiv.innerHTML = `
        <div class="step-num">Step ${stepNumber}</div>
        ${stepTitle ? `<div class="step-title">${stepTitle}</div>` : ''}
        <div class="step-text">${formattedContent}</div>
        ${finalAnswerHtml}
    `;
    elements.stepsContainer.appendChild(stepDiv);
    
    // Render math in this step
    renderMath(stepDiv);
}

// Show example approach button
elements.showExampleBtn.addEventListener('click', (e) => {
    const isHidden = elements.exampleSection.classList.contains('hidden');
    
    if (isHidden) {
        // Close steps section if it's open
        elements.stepsSection.classList.add('hidden');
        elements.showStepsBtn.textContent = '📋 Show Solution Steps';
        
        // Open example section
        elements.exampleSection.classList.remove('hidden');
        elements.showExampleBtn.textContent = '🔼 Hide Example Approach';
    } else {
        elements.exampleSection.classList.add('hidden');
        elements.showExampleBtn.textContent = '💡 Need Help? Show Example Approach';
    }
    
    // Remove focus to prevent purple background
    e.target.blur();
});

// ===== Error Handling =====
function showError(message, options = {}) {
    const { showRetry = true, retryAction = null } = options;
    
    // Clear previous error content
    elements.errorMessage.innerHTML = '';
    
    // Create error icon
    const errorIcon = document.createElement('div');
    errorIcon.style.fontSize = '3rem';
    errorIcon.style.marginBottom = '1rem';
    errorIcon.textContent = '⚠️';
    elements.errorMessage.appendChild(errorIcon);
    
    // Main error message
    const errorText = document.createElement('p');
    errorText.style.fontSize = '1.1rem';
    errorText.style.fontWeight = '600';
    errorText.style.marginBottom = '1rem';
    errorText.textContent = message;
    elements.errorMessage.appendChild(errorText);
    
    // Add contextual help based on error type
    if (message.includes('network') || message.includes('connect') || message.includes('fetch')) {
        const helpText = document.createElement('p');
        helpText.style.fontSize = '0.95rem';
        helpText.style.color = '#6B7280';
        helpText.innerHTML = '💡 <strong>Check your internet connection</strong> and try again.';
        elements.errorMessage.appendChild(helpText);
    } else if (message.includes('limit') || message.includes('quota')) {
        const helpText = document.createElement('p');
        helpText.style.fontSize = '0.95rem';
        helpText.style.color = '#6B7280';
        helpText.innerHTML = '💡 <strong>Free tier limit reached.</strong> Upgrade to Premium for unlimited analyses.';
        elements.errorMessage.appendChild(helpText);
    } else if (message.includes('clear') || message.includes('visible')) {
        const helpText = document.createElement('p');
        helpText.style.fontSize = '0.95rem';
        helpText.style.color = '#6B7280';
        helpText.innerHTML = '💡 <strong>Try these tips:</strong><br>• Use good lighting<br>• Make sure text is clear<br>• Avoid shadows or glare';
        elements.errorMessage.appendChild(helpText);
    } else {
        // Generic retry tip
        const helpText = document.createElement('p');
        helpText.style.fontSize = '0.95rem';
        helpText.style.color = '#6B7280';
        helpText.textContent = '💡 This is usually temporary. Try again in a moment.';
        elements.errorMessage.appendChild(helpText);
    }
    
    // Contact support link
    const supportLink = document.createElement('p');
    supportLink.style.marginTop = '1.5rem';
    supportLink.style.fontSize = '0.9rem';
    supportLink.innerHTML = 'Still having issues? <a href="mailto:david.bobek.business@gmail.com" style="color: #4F46E5; font-weight: 600;">Contact Support</a>';
    elements.errorMessage.appendChild(supportLink);
    
    showSection('error');
}

elements.retryBtn.addEventListener('click', () => {
    showSection('upload');
});

// ===== Analytics Tracking =====
function trackEvent(eventName, properties = {}) {
    try {
        const token = getToken();
        
        // Basic event data
        const eventData = {
            event: eventName,
            timestamp: new Date().toISOString(),
            user_agent: navigator.userAgent,
            ...properties
        };
        
        console.log('📊 Event:', eventName, properties);
        
        // Send to backend (non-blocking, don't await)
        fetch('/api/analytics/event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(eventData)
        }).catch(err => {
            // Silently fail - analytics should never break the app
            console.debug('Analytics failed:', err);
        });
    } catch (error) {
        // Silently fail - analytics should never break the app
        console.debug('Analytics error:', error);
    }
}

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
        
        // Check if user wants to upgrade
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('upgrade') === '1') {
            // Remove the upgrade parameter from URL and open checkout
            window.history.replaceState({}, document.title, window.location.pathname);
            setTimeout(() => openPaddleCheckout(), 500);
        }
    }
});

// ===== Premium Button Event Listeners =====
if (elements.upgradeBtn) {
    elements.upgradeBtn.addEventListener('click', openPaddleCheckout);
}

if (elements.paywallUpgradeBtn) {
    elements.paywallUpgradeBtn.addEventListener('click', openPaddleCheckout);
}
