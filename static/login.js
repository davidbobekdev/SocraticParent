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
                window.location.href = '/app';
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
            setTimeout(() => window.location.href = '/app', 1000);
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
            setTimeout(() => window.location.href = '/app', 1000);
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
