// Login JavaScript
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const tabs = document.querySelectorAll('.tab');
const alertBox = document.getElementById('alertBox');

// Tab switching
tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const tabName = tab.dataset.tab;
        
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        document.querySelectorAll('.form').forEach(form => {
            form.classList.remove('active');
        });
        document.getElementById(tabName + 'Form').classList.add('active');
        
        hideAlert();
    });
});

function showAlert(message, type = 'error') {
    alertBox.textContent = message;
    alertBox.className = `alert alert-${type} show`;
}

function hideAlert() {
    alertBox.className = 'alert';
}

function saveToken(token) {
    localStorage.setItem('auth_token', token);
}

function getToken() {
    return localStorage.getItem('auth_token');
}

// Check if already logged in
async function checkAuth() {
    const token = getToken();
    if (token) {
        try {
            const response = await fetch('/api/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (response.ok) {
                // Check for upgrade parameter to redirect to checkout
                const urlParams = new URLSearchParams(window.location.search);
                if (urlParams.get('upgrade') === '1') {
                    window.location.href = '/app?upgrade=1';
                } else {
                    window.location.href = '/app';
                }
            } else {
                localStorage.removeItem('auth_token');
            }
        } catch (error) {
            localStorage.removeItem('auth_token');
        }
    }
}

checkAuth();

// Login Handler
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAlert();
    
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        showAlert('Please fill in all fields', 'error');
        return;
    }
    
    const submitBtn = loginForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Logging in...';
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            saveToken(data.access_token);
            showAlert('Login successful! Redirecting...', 'success');
            // Check for upgrade parameter
            const urlParams = new URLSearchParams(window.location.search);
            const redirect = urlParams.get('upgrade') === '1' ? '/app?upgrade=1' : '/app';
            setTimeout(() => window.location.href = redirect, 1000);
        } else {
            showAlert(data.detail || 'Login failed', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Login';
        }
    } catch (error) {
        showAlert('Connection error. Please try again.', 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Login';
    }
});

// Register Handler
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAlert();
    
    const username = document.getElementById('registerUsername').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value;
    const passwordConfirm = document.getElementById('registerPasswordConfirm').value;
    
    if (!username || !email || !password || !passwordConfirm) {
        showAlert('Please fill in all fields', 'error');
        return;
    }
    
    if (username.length < 3) {
        showAlert('Username must be at least 3 characters', 'error');
        return;
    }
    
    if (password.length < 6) {
        showAlert('Password must be at least 6 characters', 'error');
        return;
    }
    
    if (password !== passwordConfirm) {
        showAlert('Passwords do not match', 'error');
        return;
    }
    
    const submitBtn = registerForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating account...';
    
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            saveToken(data.access_token);
            showAlert('Account created! Redirecting...', 'success');
            // Check for upgrade parameter
            const urlParams = new URLSearchParams(window.location.search);
            const redirect = urlParams.get('upgrade') === '1' ? '/app?upgrade=1' : '/app';
            setTimeout(() => window.location.href = redirect, 1000);
        } else {
            showAlert(data.detail || 'Registration failed', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Account';
        }
    } catch (error) {
        showAlert('Connection error. Please try again.', 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Create Account';
    }
});

// Google Sign-In Configuration
// Will be loaded from server config
let GOOGLE_CLIENT_ID = null;

// Fetch Google Client ID from server
async function loadGoogleConfig() {
    try {
        const response = await fetch('/api/config/public');
        if (response.ok) {
            const config = await response.json();
            GOOGLE_CLIENT_ID = config.google_client_id;
            if (GOOGLE_CLIENT_ID) {
                initGoogleSignIn();
            } else {
                console.warn('Google Sign-In not configured (no client ID)');
                hideGoogleSignIn();
            }
        } else {
            console.warn('Failed to load config');
            hideGoogleSignIn();
        }
    } catch (error) {
        console.error('Error loading config:', error);
        hideGoogleSignIn();
    }
}

function hideGoogleSignIn() {
    const googleBtn = document.getElementById('googleSignInBtn');
    const divider = document.querySelector('.divider');
    if (googleBtn) googleBtn.style.display = 'none';
    if (divider) divider.style.display = 'none';
}

// Initialize Google Sign-In
function initGoogleSignIn() {
    if (typeof google === 'undefined') {
        // Google SDK not loaded yet, retry after a short delay
        setTimeout(initGoogleSignIn, 100);
        return;
    }
    
    google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleGoogleSignIn,
        auto_select: false,
        cancel_on_tap_outside: true
    });
    
    // Enable the custom button
    const googleBtn = document.getElementById('googleSignInBtn');
    if (googleBtn) {
        googleBtn.addEventListener('click', () => {
            google.accounts.id.prompt((notification) => {
                if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
                    // Fallback: use popup mode
                    google.accounts.oauth2.initTokenClient({
                        client_id: GOOGLE_CLIENT_ID,
                        scope: 'email profile',
                        callback: (response) => {
                            if (response.access_token) {
                                // Get user info with access token
                                fetchGoogleUserInfo(response.access_token);
                            }
                        }
                    }).requestAccessToken();
                }
            });
        });
    }
}

// Handle Google Sign-In callback (for One Tap)
async function handleGoogleSignIn(response) {
    const googleBtn = document.getElementById('googleSignInBtn');
    googleBtn.disabled = true;
    googleBtn.innerHTML = 'Signing in...';
    
    try {
        const result = await fetch('/api/auth/google', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ credential: response.credential })
        });
        
        const data = await result.json();
        
        if (result.ok) {
            saveToken(data.access_token);
            showAlert('Signed in with Google! Redirecting...', 'success');
            const urlParams = new URLSearchParams(window.location.search);
            const redirect = urlParams.get('upgrade') === '1' ? '/app?upgrade=1' : '/app';
            setTimeout(() => window.location.href = redirect, 1000);
        } else {
            showAlert(data.detail || 'Google sign-in failed', 'error');
            resetGoogleButton();
        }
    } catch (error) {
        console.error('Google sign-in error:', error);
        showAlert('Connection error. Please try again.', 'error');
        resetGoogleButton();
    }
}

// Fetch Google user info with access token (fallback method)
async function fetchGoogleUserInfo(accessToken) {
    const googleBtn = document.getElementById('googleSignInBtn');
    googleBtn.disabled = true;
    googleBtn.innerHTML = 'Signing in...';
    
    try {
        // Get user info from Google
        const userInfoResponse = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        
        const userInfo = await userInfoResponse.json();
        
        // Send to our backend
        const result = await fetch('/api/auth/google', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                access_token: accessToken,
                email: userInfo.email,
                name: userInfo.name,
                sub: userInfo.sub
            })
        });
        
        const data = await result.json();
        
        if (result.ok) {
            saveToken(data.access_token);
            showAlert('Signed in with Google! Redirecting...', 'success');
            const urlParams = new URLSearchParams(window.location.search);
            const redirect = urlParams.get('upgrade') === '1' ? '/app?upgrade=1' : '/app';
            setTimeout(() => window.location.href = redirect, 1000);
        } else {
            showAlert(data.detail || 'Google sign-in failed', 'error');
            resetGoogleButton();
        }
    } catch (error) {
        console.error('Google sign-in error:', error);
        showAlert('Connection error. Please try again.', 'error');
        resetGoogleButton();
    }
}

function resetGoogleButton() {
    const googleBtn = document.getElementById('googleSignInBtn');
    googleBtn.disabled = false;
    googleBtn.innerHTML = `
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
        </svg>
        Continue with Google
    `;
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', loadGoogleConfig);
