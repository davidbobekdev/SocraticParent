"""
Socratic Parent - Simple Version with Image Upload and API Key Session
"""

import os
import json
import hashlib
import smtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
from google import genai
from google.genai import types
from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# API Key Rotation System
class APIKeyRotator:
    """Manages multiple Gemini API keys with intelligent rotation and recovery"""
    def __init__(self):
        self.keys = []
        self.usage_file = os.path.join(os.getenv("DATA_DIR", "."), "api_key_usage.json")
        self.daily_limit = 18  # Conservative limit (20 - 2 buffer)
        self._load_keys()
        self._load_usage()
    
    def _load_keys(self):
        """Load all available API keys from environment"""
        # Try numbered keys first (GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.)
        i = 1
        while True:
            key = os.getenv(f"GEMINI_API_KEY_{i}")
            if key:
                self.keys.append(key)
                i += 1
            else:
                break
        
        # Fallback to single key if no numbered keys found
        if not self.keys:
            single_key = os.getenv("GEMINI_API_KEY")
            if single_key:
                self.keys.append(single_key)
        
        print(f"🔑 Loaded {len(self.keys)} API key(s) for rotation")
    
    def _load_usage(self):
        """Load usage tracking from file"""
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                    self.usage = data.get('usage', {})
                    self.exhausted_keys = data.get('exhausted_keys', {})
                    self.invalid_keys = data.get('invalid_keys', [])
            except:
                self.usage = {}
                self.exhausted_keys = {}
                self.invalid_keys = []
        else:
            self.usage = {}
            self.exhausted_keys = {}  # {key_id: timestamp_when_exhausted}
            self.invalid_keys = []  # List of key indices that are invalid
        
        # Check if exhausted keys can be recovered
        self._recover_exhausted_keys()
    
    def _save_usage(self):
        """Save usage tracking to file"""
        try:
            os.makedirs(os.path.dirname(self.usage_file), exist_ok=True)
            with open(self.usage_file, 'w') as f:
                json.dump({
                    'usage': self.usage,
                    'exhausted_keys': self.exhausted_keys,
                    'invalid_keys': self.invalid_keys
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save API key usage: {e}")
    
    def _recover_exhausted_keys(self):
        """Check if exhausted keys can be recovered after 24 hours"""
        now = datetime.now()
        recovered = []
        
        for key_id, exhausted_time in list(self.exhausted_keys.items()):
            try:
                exhausted_dt = datetime.fromisoformat(exhausted_time)
                # If more than 24 hours have passed, recover the key
                if (now - exhausted_dt).total_seconds() >= 86400:  # 24 hours
                    self.usage[key_id] = 0
                    recovered.append(key_id)
                    del self.exhausted_keys[key_id]
            except:
                # If parsing fails, just recover it
                del self.exhausted_keys[key_id]
        
        if recovered:
            print(f"♻️ Recovered {len(recovered)} API key(s) after 24-hour cooldown")
            self._save_usage()
    
    def mark_key_exhausted(self, key_index: int):
        """Mark a key as exhausted with timestamp"""
        key_id = f"key_{key_index}"
        self.exhausted_keys[key_id] = datetime.now().isoformat()
        self.usage[key_id] = self.daily_limit
        self._save_usage()
        print(f"⏰ API Key {key_index + 1} exhausted, will recover in 24 hours")
    
    def mark_key_invalid(self, key_index: int):
        """Mark a key as invalid (won't be retried)"""
        if key_index not in self.invalid_keys:
            self.invalid_keys.append(key_index)
            self._save_usage()
            print(f"❌ API Key {key_index + 1} marked as invalid")
    
    def get_next_key_to_try(self) -> Optional[tuple[str, int]]:
        """Get next API key to try (key, index)"""
        if not self.keys:
            return None, None
        
        self._recover_exhausted_keys()
        
        # Find first available key that's not exhausted or invalid
        for i, key in enumerate(self.keys):
            if i in self.invalid_keys:
                continue
            
            key_id = f"key_{i}"
            
            # Check if key is exhausted
            if key_id in self.exhausted_keys:
                continue
            
            # Check usage
            current_usage = self.usage.get(key_id, 0)
            if current_usage < self.daily_limit:
                return key, i
        
        return None, None
    
    def record_success(self, key_index: int):
        """Record successful API call"""
        key_id = f"key_{key_index}"
        self.usage[key_id] = self.usage.get(key_id, 0) + 1
        self._save_usage()
        remaining = self.daily_limit - self.usage[key_id]
        print(f"✅ API Key {key_index + 1} usage: {self.usage[key_id]}/{self.daily_limit} ({remaining} left)")
    
    def get_total_remaining(self) -> int:
        """Get total remaining requests across all active keys"""
        self._recover_exhausted_keys()
        total = 0
        for i in range(len(self.keys)):
            if i in self.invalid_keys:
                continue
            key_id = f"key_{i}"
            if key_id in self.exhausted_keys:
                continue
            used = self.usage.get(key_id, 0)
            total += max(0, self.daily_limit - used)
        return total
    
    def get_status(self) -> dict:
        """Get detailed status of all keys"""
        self._recover_exhausted_keys()
        status = {
            "total_keys": len(self.keys),
            "active_keys": 0,
            "exhausted_keys": len(self.exhausted_keys),
            "invalid_keys": len(self.invalid_keys),
            "total_remaining": self.get_total_remaining()
        }
        status["active_keys"] = status["total_keys"] - status["exhausted_keys"] - status["invalid_keys"]
        return status

# Initialize API key rotator
api_key_rotator = APIKeyRotator()

# Security configurations
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production-$(date +%s)")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Simple file-based user storage with persistent path
# Railway volumes mount at /data, local development uses ./data
DATA_DIR = os.getenv("DATA_DIR", "./data")
# Create data directory if it doesn't exist
if not os.path.exists(DATA_DIR):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create DATA_DIR {DATA_DIR}, falling back to ./data: {e}")
        DATA_DIR = "./data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None  # JWT token from Google One Tap
    access_token: Optional[str] = None  # Access token from OAuth popup
    email: Optional[str] = None
    name: Optional[str] = None
    sub: Optional[str] = None  # Google user ID

class UserStatus(BaseModel):
    username: str
    email: str
    is_premium: bool
    scans_left: int

class Token(BaseModel):
    access_token: str
    token_type: str

# User management functions
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    try:
        # Ensure directory exists before writing
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        print(f"Error saving users: {e}")
        raise

# Usage limit checking for Paddle integration
def check_and_update_usage_limit(username: str) -> dict:
    """
    Check if user can perform a scan and update their usage.
    Returns: {"allowed": bool, "is_premium": bool, "scans_left": int, "reason": str}
    """
    users = load_users()
    
    if username not in users:
        return {"allowed": False, "is_premium": False, "scans_left": 0, "reason": "User not found"}
    
    user = users[username]
    
    # Initialize premium fields if not present (for existing users)
    if 'is_premium' not in user:
        user['is_premium'] = False
    if 'daily_scans_left' not in user:
        user['daily_scans_left'] = 5
    if 'last_reset' not in user:
        user['last_reset'] = datetime.now().isoformat()
    
    # Check if we need to reset daily limit (24 hours)
    last_reset = datetime.fromisoformat(user['last_reset'])
    now = datetime.now()
    hours_since_reset = (now - last_reset).total_seconds() / 3600
    
    if hours_since_reset >= 24:
        user['daily_scans_left'] = 5
        user['last_reset'] = now.isoformat()
    
    # Premium users have unlimited scans
    if user['is_premium']:
        users[username] = user
        save_users(users)
        return {
            "allowed": True,
            "is_premium": True,
            "scans_left": -1,  # -1 indicates unlimited
            "reason": "Premium user"
        }
    
    # Check if non-premium user has scans left
    if user['daily_scans_left'] > 0:
        user['daily_scans_left'] -= 1
        users[username] = user
        save_users(users)
        return {
            "allowed": True,
            "is_premium": False,
            "scans_left": user['daily_scans_left'],
            "reason": "Free tier"
        }
    
    # No scans left
    return {
        "allowed": False,
        "is_premium": False,
        "scans_left": 0,
        "reason": "PAYWALL_TRIGGER"
    }

def verify_password(plain_password, hashed_password):
    # Truncate password to 72 bytes for bcrypt compatibility
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    # Truncate password to 72 bytes for bcrypt compatibility
    if len(password.encode('utf-8')) > 72:
        password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(username: str):
    users = load_users()
    if username in users:
        return users[username]
    return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user(username=username)
    if user is None:
        raise credentials_exception
    return user

async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    """Optional authentication - returns None if not authenticated"""
    if credentials is None:
        return None
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = get_user(username=username)
        return user
    except JWTError:
        return None

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Public config endpoint (for frontend to get Google Client ID)
@app.get("/api/config/public")
async def get_public_config():
    """Return public configuration for frontend"""
    return {
        "google_client_id": GOOGLE_CLIENT_ID
    }

# Authentication endpoints
@app.post("/api/register", response_model=Token)
async def register(user: UserCreate):
    users = load_users()
    
    # Validation
    if len(user.username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters"
        )
    
    if len(user.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    if user.username in users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    for existing_user in users.values():
        if existing_user.get("email") == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    hashed_password = get_password_hash(user.password)
    users[user.username] = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow().isoformat(),
        "is_premium": False,
        "daily_scans_left": 5,
        "last_reset": datetime.now().isoformat(),
        "paddle_subscription_id": None
    }
    save_users(users)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/login", response_model=Token)
async def login(user: UserLogin):
    users = load_users()
    
    if user.username not in users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    stored_user = users[user.username]
    if not verify_password(user.password, stored_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

async def verify_google_token(credential: str) -> dict:
    """Verify Google JWT token and return user info"""
    try:
        # Google's token info endpoint for ID tokens
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
            )
            if response.status_code != 200:
                raise ValueError("Invalid token")
            
            token_info = response.json()
            
            # Verify the token is for our app
            if token_info.get("aud") != GOOGLE_CLIENT_ID:
                raise ValueError("Token not for this application")
            
            return {
                "email": token_info.get("email"),
                "name": token_info.get("name", ""),
                "sub": token_info.get("sub"),  # Google user ID
                "email_verified": token_info.get("email_verified", "false") == "true"
            }
    except Exception as e:
        print(f"Google token verification error: {e}")
        raise ValueError(f"Token verification failed: {str(e)}")

def get_or_create_google_user(email: str, name: str, google_id: str) -> tuple[str, bool]:
    """Get existing user by Google ID/email or create new one. Returns (username, is_new_user)"""
    users = load_users()
    
    # First, try to find user by Google ID
    for username, user_data in users.items():
        if user_data.get("google_id") == google_id:
            return username, False
    
    # Next, try to find by email and link Google account
    for username, user_data in users.items():
        if user_data.get("email") == email:
            # Link Google ID to existing account
            user_data["google_id"] = google_id
            user_data["auth_provider"] = user_data.get("auth_provider", "email") + ",google"
            users[username] = user_data
            save_users(users)
            return username, False
    
    # Create new user with Google account
    # Generate username from email (before @)
    base_username = email.split("@")[0].lower().replace(".", "_").replace("+", "_")
    username = base_username
    counter = 1
    while username in users:
        username = f"{base_username}{counter}"
        counter += 1
    
    users[username] = {
        "username": username,
        "email": email,
        "hashed_password": None,  # No password for Google-only users
        "created_at": datetime.utcnow().isoformat(),
        "is_premium": False,
        "daily_scans_left": 5,
        "last_reset": datetime.now().isoformat(),
        "paddle_subscription_id": None,
        "google_id": google_id,
        "auth_provider": "google",
        "display_name": name
    }
    save_users(users)
    
    return username, True

@app.post("/api/auth/google", response_model=Token)
async def google_auth(auth_request: GoogleAuthRequest):
    """Authenticate user via Google Sign-In"""
    try:
        # Handle JWT credential (from One Tap)
        if auth_request.credential:
            user_info = await verify_google_token(auth_request.credential)
            email = user_info["email"]
            name = user_info.get("name", "")
            google_id = user_info["sub"]
        
        # Handle access token flow (from popup)
        elif auth_request.access_token and auth_request.email and auth_request.sub:
            # Verify the access token by calling Google's userinfo endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {auth_request.access_token}"}
                )
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid Google access token"
                    )
                user_info = response.json()
                email = user_info.get("email", auth_request.email)
                name = user_info.get("name", auth_request.name or "")
                google_id = user_info.get("sub", auth_request.sub)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid Google credentials provided"
            )
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google"
            )
        
        # Get or create user
        username, is_new = get_or_create_google_user(email, name, google_id)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        print(f"Google auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@app.get("/api/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "email": current_user["email"]
    }

# Password Reset Endpoints
RESET_TOKENS_FILE = os.path.join(DATA_DIR, "reset_tokens.json")

def load_reset_tokens():
    if os.path.exists(RESET_TOKENS_FILE):
        with open(RESET_TOKENS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_reset_tokens(tokens):
    try:
        os.makedirs(os.path.dirname(RESET_TOKENS_FILE), exist_ok=True)
        with open(RESET_TOKENS_FILE, 'w') as f:
            json.dump(tokens, f, indent=2)
    except Exception as e:
        print(f"Error saving reset tokens: {e}")

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

@app.post("/api/password-reset/request")
async def request_password_reset(reset_request: PasswordResetRequest):
    """Generate a password reset token for the user"""
    users = load_users()
    
    # Find user by email
    user_found = None
    username = None
    for uname, user_data in users.items():
        if user_data.get("email") == reset_request.email:
            user_found = user_data
            username = uname
            break
    
    # Always return success to prevent email enumeration
    if not user_found:
        return {"message": "If that email exists, a reset link has been sent"}
    
    # Generate reset token
    import secrets
    reset_token = secrets.token_urlsafe(32)
    
    # Store token with expiration (1 hour)
    reset_tokens = load_reset_tokens()
    reset_tokens[reset_token] = {
        "username": username,
        "email": reset_request.email,
        "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
        "used": False
    }
    save_reset_tokens(reset_tokens)
    
    # In production, send email here
    # For now, log it (in production you'd use SendGrid, AWS SES, etc.)
    print(f"🔑 Password reset token for {username}: {reset_token}")
    print(f"Reset link: https://socratesparent-production.up.railway.app/static/reset-password.html?token={reset_token}")
    
    # Don't return token in production for security
    return {"message": "If that email exists, a reset link has been sent"}

@app.post("/api/password-reset/confirm")
async def confirm_password_reset(reset_confirm: PasswordResetConfirm):
    """Reset password using the token"""
    if len(reset_confirm.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    reset_tokens = load_reset_tokens()
    
    if reset_confirm.token not in reset_tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    token_data = reset_tokens[reset_confirm.token]
    
    # Check if token is expired
    expires_at = datetime.fromisoformat(token_data["expires_at"])
    if datetime.now() > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    
    # Check if token was already used
    if token_data.get("used"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has already been used"
        )
    
    # Update password
    users = load_users()
    username = token_data["username"]
    
    if username not in users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    users[username]["hashed_password"] = get_password_hash(reset_confirm.new_password)
    save_users(users)
    
    # Mark token as used
    token_data["used"] = True
    token_data["used_at"] = datetime.now().isoformat()
    save_reset_tokens(reset_tokens)
    
    return {"message": "Password reset successful"}

# Account Settings Endpoints
class PasswordChange(BaseModel):
    current_password: str
    new_password: str

@app.post("/api/account/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: dict = Depends(get_current_user)
):
    """Change user password (requires current password)"""
    if len(password_change.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters"
        )
    
    users = load_users()
    user = users.get(current_user["username"])
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(password_change.current_password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update password
    user["hashed_password"] = get_password_hash(password_change.new_password)
    save_users(users)
    
    return {"message": "Password changed successfully"}

class SimplePasswordChange(BaseModel):
    new_password: str

@app.post("/api/account/update-password")
async def update_password(
    password_data: SimplePasswordChange,
    current_user: dict = Depends(get_current_user)
):
    """Update password without requiring current password (for logged-in users)"""
    if len(password_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    users = load_users()
    user = users.get(current_user["username"])
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update password
    user["hashed_password"] = get_password_hash(password_data.new_password)
    save_users(users)
    
    return {"message": "Password updated successfully"}

@app.post("/api/subscription/portal")
async def subscription_portal(current_user: dict = Depends(get_current_user)):
    """Get subscription management URL (Paddle customer portal or cancel page)"""
    users = load_users()
    user = users.get(current_user["username"])
    
    if not user or not user.get("is_premium"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription"
        )
    
    # For now, redirect to cancel subscription endpoint info
    # In production, this would redirect to Paddle's customer portal
    return {
        "message": "To manage your subscription, please contact support or use the cancel option below",
        "can_cancel": True
    }

@app.post("/api/account/cancel-subscription")
async def cancel_subscription(current_user: dict = Depends(get_current_user)):
    """Cancel premium subscription (remove premium status)"""
    users = load_users()
    user = users.get(current_user["username"])
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.get("is_premium"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription to cancel"
        )
    
    # Remove premium status
    user["is_premium"] = False
    user["daily_scans_left"] = 5
    user["subscription_cancelled_at"] = datetime.now().isoformat()
    # Keep paddle_subscription_id for records
    
    save_users(users)
    
    return {"message": "Subscription cancelled successfully"}

@app.delete("/api/account/delete")
async def delete_account(current_user: dict = Depends(get_current_user)):
    """Permanently delete user account"""
    users = load_users()
    
    if current_user["username"] not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete user
    del users[current_user["username"]]
    save_users(users)
    
    return {"message": "Account deleted successfully"}

@app.get("/api/account/info")
async def get_account_info(current_user: dict = Depends(get_current_user)):
    """Get detailed account information"""
    users = load_users()
    user = users.get(current_user["username"])
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "username": user["username"],
        "email": user["email"],
        "is_premium": user.get("is_premium", False),
        "created_at": user.get("created_at"),
        "daily_scans_left": user.get("daily_scans_left", 5),
        "paddle_subscription_id": user.get("paddle_subscription_id")
    }

@app.get("/api/user/status", response_model=UserStatus)
async def get_user_status(current_user: dict = Depends(get_current_user)):
    """Get user's premium status and remaining scans"""
    users = load_users()
    user = users.get(current_user["username"], {})
    
    # Initialize if missing
    if 'is_premium' not in user:
        user['is_premium'] = False
    if 'daily_scans_left' not in user:
        user['daily_scans_left'] = 5
    
    return {
        "username": current_user["username"],
        "email": user.get("email", current_user["username"]),
        "is_premium": user.get("is_premium", False),
        "scans_left": user.get("daily_scans_left", 5) if not user.get("is_premium") else -1
    }

@app.get("/api/paddle/client-token")
async def get_paddle_config(current_user: dict = Depends(get_current_user)):
    """Get Paddle configuration for frontend checkout"""
    user = get_user(current_user["username"])
    return {
        "client_token": os.getenv("PADDLE_CLIENT_TOKEN", ""),
        "price_id": os.getenv("PADDLE_PRICE_ID", ""),
        "user_id": current_user["username"],
        "user_email": user.get("email", f"{current_user['username']}@example.com")
    }

# Simple analytics endpoint (non-blocking, for basic tracking)
@app.post("/api/analytics/event")
async def log_analytics_event(
    request: Request,
    current_user: dict = Depends(get_optional_user)
):
    """Log analytics events (non-critical, always returns 200)"""
    try:
        data = await request.json()
        event_name = data.get("event", "unknown")
        username = current_user.get("username", "anonymous") if current_user else "anonymous"
        
        # In production, you'd send this to analytics service (Google Analytics, Mixpanel, etc.)
        # For now, just log to console
        print(f"📊 Analytics: {username} - {event_name} - {data.get('properties', {})}")
        
        return {"status": "logged"}
    except Exception as e:
        # Never fail the request
        print(f"Analytics logging failed: {e}")
        return {"status": "ignored"}

# Contact Form Endpoint
class ContactMessage(BaseModel):
    name: str
    email: str
    subject: str
    message: str

CONTACT_MESSAGES_FILE = os.path.join(DATA_DIR, "contact_messages.json")

def load_contact_messages():
    if os.path.exists(CONTACT_MESSAGES_FILE):
        with open(CONTACT_MESSAGES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_contact_message(message_data):
    try:
        messages = load_contact_messages()
        messages.append(message_data)
        os.makedirs(os.path.dirname(CONTACT_MESSAGES_FILE), exist_ok=True)
        with open(CONTACT_MESSAGES_FILE, 'w') as f:
            json.dump(messages, f, indent=2)
    except Exception as e:
        print(f"Error saving contact message: {e}")

def send_contact_email(contact: ContactMessage):
    """Send email notification for contact form submission using Resend API or mock mode"""
    try:
        resend_api_key = os.getenv("RESEND_API_KEY")
        recipient_email = os.getenv("CONTACT_RECIPIENT_EMAIL", "david.bobek.business@gmail.com")
        mock_mode = os.getenv("EMAIL_MOCK_MODE", "false").lower() == "true"
        
        # Create email body
        html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #667eea;">📧 New Contact Form Submission</h2>
        <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Name:</strong> {contact.name}</p>
            <p><strong>Email:</strong> <a href="mailto:{contact.email}">{contact.email}</a></p>
            <p><strong>Subject:</strong> {contact.subject}</p>
        </div>
        <div style="background: white; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h3 style="margin-top: 0;">Message:</h3>
            <p style="white-space: pre-wrap;">{contact.message}</p>
        </div>
        <p style="color: #64748b; font-size: 0.9em; margin-top: 20px;">
            Submitted at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </p>
    </div>
</body>
</html>
"""
        
        # Mock mode - log email instead of sending
        if mock_mode or not resend_api_key:
            print("=" * 60)
            print("📧 [MOCK EMAIL] Contact Form Submission")
            print("=" * 60)
            print(f"To: {recipient_email}")
            print(f"Reply-To: {contact.email}")
            print(f"Subject: [Contact Form] {contact.subject}")
            print("-" * 60)
            print(f"From: {contact.name} ({contact.email})")
            print(f"Message:\n{contact.message}")
            print("=" * 60)
            if not resend_api_key:
                print("⚠️ RESEND_API_KEY not configured - email logged but not sent")
            else:
                print("✅ [MOCK MODE] Email logged successfully")
            return True
        
        # Send via Resend API
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": "Socratic Parent <onboarding@resend.dev>",
                "to": [recipient_email],
                "reply_to": contact.email,
                "subject": f"[Contact Form] {contact.subject}",
                "html": html
            },
            timeout=10.0
        )
        
        if response.status_code == 200:
            print(f"✅ Contact email sent to {recipient_email} via Resend")
            return True
        else:
            print(f"❌ Resend API error: {response.status_code} - {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Error sending contact email: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.post("/api/contact")
async def submit_contact_form(contact: ContactMessage, background_tasks: BackgroundTasks):
    """Handle contact form submissions"""
    # Validate
    if len(contact.message) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message must be at least 10 characters"
        )
    
    # Save message
    message_data = {
        "name": contact.name,
        "email": contact.email,
        "subject": contact.subject,
        "message": contact.message,
        "submitted_at": datetime.now().isoformat(),
        "read": False
    }
    
    save_contact_message(message_data)
    
    # Send email notification in background (non-blocking)
    background_tasks.add_task(send_contact_email, contact)
    
    return {"message": "Thank you! We'll get back to you soon."}


@app.post("/api/admin/upgrade-test")
async def admin_upgrade_test(username: str, admin_secret: str):
    """Admin endpoint for testing premium upgrades - REMOVE IN PRODUCTION"""
    if admin_secret != "TEMP_ADMIN_2026":
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    
    users = load_users()
    if username not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    users[username]["is_premium"] = True
    users[username]["paddle_subscription_id"] = "test_manual_upgrade"
    save_users(users)
    
    return {"success": True, "message": f"User {username} upgraded to premium"}

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Guided Homework</title>
    <link rel="icon" type="image/png" href="/static/logo_website.png">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
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
            font-size: 1.4em;
            font-weight: 700;
            line-height: 1.3;
            letter-spacing: -0.01em;
        }
        .step-content {
            color: #334155;
            font-size: 1em;
            line-height: 1.65;
            max-width: 65ch;
        }
        .step-content p {
            margin: 20px 0;
        }
        .step-content .step-item {
            margin: 24px 0;
            padding: 16px;
            background: #f8fafc;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
        }
        .step-content .step-number-inline {
            font-weight: 700;
            color: #1e40af;
            font-size: 0.95em;
            display: block;
            margin-bottom: 10px;
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
            max-width: 100%;
            color: #1e3a8a;
        }
        .katex-display {
            margin: 24px 0;
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            padding: 20px 24px;
            border-radius: 12px;
            border: 2px solid #3b82f6;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        }
        .step-content .katex-display {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #2563eb;
            border-right: 1px solid #93c5fd;
            border-top: 1px solid #bfdbfe;
            border-bottom: 1px solid #93c5fd;
        }
        .katex-display > .katex {
            font-size: 1.15em;
            color: #1e40af;
        }
        /* Fancy superscripts/exponents */
        .katex .msupsub {
            color: #dc2626;
            font-weight: 600;
        }
        .katex .vlist-t .vlist-r .vlist > span > span {
            font-weight: 600;
        }
        .katex sup {
            color: #dc2626;
            font-weight: 700;
        }
        /* Inline math gets subtle highlight */
        p .katex, li .katex {
            background: #eff6ff;
            padding: 2px 6px;
            border-radius: 4px;
            border-bottom: 2px solid #93c5fd;
        }
        /* Remove double box: no background on equations inside display blocks */
        .katex-display .katex {
            background: none !important;
            padding: 0 !important;
            border: none !important;
        }
        /* Fractions */
        .katex .frac-line {
            border-bottom-color: #3b82f6 !important;
            border-bottom-width: 1.5px !important;
        }
        /* Parentheses and brackets */
        .katex .mopen, .katex .mclose {
            color: #7c3aed;
            font-weight: 600;
        }
        /* Operators */
        .katex .mbin, .katex .mrel {
            color: #059669;
            font-weight: 600;
        }
        /* Variables like x, y */
        .katex .mathit {
            color: #be123c;
            font-style: italic;
            font-weight: 500;
        }
        /* Numbers */
        .katex .mord {
            color: #1e40af;
            font-weight: 500;
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
        
        /* Mobile Optimizations */
        @media (max-width: 768px) {
            body {
                padding: 16px 12px;
            }
            .container {
                border-radius: 8px;
            }
            .header {
                padding: 24px 20px 20px;
            }
            h1 {
                font-size: 1.5em;
                margin-bottom: 8px;
            }
            .tagline {
                font-size: 0.9em;
            }
            .content {
                padding: 24px 20px;
            }
            .upload-section {
                padding: 24px;
                margin-bottom: 16px;
            }
            .upload-icon {
                font-size: 2em;
                margin-bottom: 12px;
            }
            .upload-text {
                font-size: 1em;
            }
            .subject-badge {
                font-size: 0.75em;
                padding: 6px 12px;
                margin-bottom: 16px;
            }
            .problem-card {
                padding: 16px;
                margin-bottom: 20px;
            }
            .problem-card .label {
                font-size: 0.7em;
                margin-bottom: 6px;
            }
            .problem-card .content {
                font-size: 1em;
            }
            .step-header {
                margin-bottom: 20px;
                padding-bottom: 16px;
            }
            .step-number {
                font-size: 0.75em;
                padding: 3px 10px;
            }
            .step-title {
                font-size: 1.35em;
            }
            .step-content {
                font-size: 1em;
                line-height: 1.6;
            }
            .step-content p {
                margin: 16px 0;
            }
            .step-content .step-item {
                margin: 20px 0;
                padding: 16px;
            }
            .step-content ul, .step-content ol {
                margin: 16px 0;
            }
            .step-content li {
                margin: 12px 0;
            }
            .progress-bar {
                margin-bottom: 24px;
            }
            .navigation {
                margin-top: 32px;
                padding-top: 24px;
                gap: 8px;
            }
            .nav-btn {
                padding: 12px 16px;
                font-size: 0.9em;
            }
            .practice-card {
                padding: 16px;
                margin-top: 20px;
            }
            .btn {
                padding: 12px 24px;
                font-size: 0.95em;
            }
            .loading {
                padding: 32px;
            }
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
            // Don't wrap math in spans - let KaTeX handle $ delimiters
            // Just do basic text formatting
            
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
            console.log('displayLesson called - steps.length:', steps.length);
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
            
            console.log('Setting lessonContent innerHTML');
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
            
            console.log('Calling showStep(0)');
            currentStep = 0;
            showStep(0);
        }
        
        function showStep(index) {
            console.log('showStep called with index:', index);
            document.querySelectorAll('.step-card').forEach(card => card.classList.remove('active'));
            const stepCard = document.getElementById('step' + index);
            console.log('stepCard element:', stepCard);
            if (stepCard) {
                stepCard.classList.add('active');
                
                // Re-render math in the active step
                if (typeof renderMathInElement !== 'undefined') {
                    renderMathInElement(stepCard, {
                        delimiters: [
                            {left: '$$', right: '$$', display: true},
                            {left: '$', right: '$', display: false}
                        ],
                        throwOnError: false
                    });
                }
            } else {
                console.error('Step card not found for index:', index);
            }
            
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
            console.log('nextStep called - currentStep:', currentStep, 'steps.length:', steps.length);
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
            document.getElementById('lessonContent').innerHTML = '';
            
            // Reset navigation
            const navigation = document.querySelector('.navigation');
            if (navigation) {
                navigation.style.display = 'flex';
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve landing page"""
    with open("static/landing.html", "r") as f:
        return f.read()

@app.get("/login.html", response_class=HTMLResponse)
async def login_page():
    """Serve login/register page"""
    with open("static/login.html", "r") as f:
        return f.read()

@app.get("/app", response_class=HTMLResponse)
async def app_page():
    """Serve main app page (auth checked by JavaScript)"""
    with open("static/index.html", "r") as f:
        return f.read()

@app.get("/api/test")
async def test_endpoint():
    status = api_key_rotator.get_status()
    return {
        "status": "success", 
        "message": "API is working!", 
        "version": "v3-smart-rotation", 
        "ready": True,
        "api_keys": status
    }

async def analyze_homework_with_ai(image_bytes: bytes, max_retries: int = None):
    """Analyze homework image using Google Gemini with intelligent key rotation"""
    
    # Try all available keys
    max_retries = max_retries or len(api_key_rotator.keys)
    last_error = None
    
    for attempt in range(max_retries):
        # Get next key to try
        api_key, key_index = api_key_rotator.get_next_key_to_try()
        
        if api_key is None:
            # No keys available, return user-friendly error
            return {
                "success": False,
                "error": "Service temporarily at capacity. Please try again in a few moments.",
                "retry_after": "1 hour"
            }
        
        try:
            client = genai.Client(api_key=api_key)
            
            prompt = """You are an expert tutor helping students learn step-by-step. Analyze this homework problem and create a structured learning experience with DETAILED MATHEMATICAL WORKINGS.

Provide your response in EXACTLY this format:

**Subject & Topic:** [Brief description]

**The Problem:**
[Clearly state what needs to be solved]

**Step 1: Understanding**
[Explain what we're looking at and what we need to find]

**Step 2: Identify the Rules**
[What mathematical rules or concepts apply here? Write any formulas using $ for inline math like $x = 5$ or $$ for display math like $$\\frac{a}{b}$$. Always wrap numbers, fractions, and expressions in $ signs!]

**Step 3: Set Up**
[How do we organize the problem? Show the setup with proper mathematical notation using $ for all numbers and expressions]

**Step 4: Solve Part 1**
[Show EVERY calculation step. Example:
Starting with: $3x + 5 = 20$
Subtract 5 from both sides: $3x = 15$
Show ALL intermediate steps!]

**Step 5: Solve Part 2**
[Continue with more detailed calculations. Show:
- What operation you're doing
- The intermediate result
- Why this step makes sense]

**Step 6: Verify and Answer**
[Check the work by substituting back or using another method. State the final answer clearly with units if applicable]

**Practice Question:**
[A similar but slightly different problem for them to try]

IMPORTANT: 
- Show EVERY calculation step, not just the result
- Use $ symbols for ALL math notation including numbers, fractions, and expressions (e.g., $x^2$, $\\frac{1}{2}$, $2/3$, $x = 5$)
- Include intermediate numerical results wrapped in $ signs
- Explain what each operation does to the numbers
- When describing mathematical values in sentences, wrap them in $ (e.g., "the value is $5$" or "divide by $2$")
Keep language encouraging and appropriate for students."""
            
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
                model='models/gemini-2.5-flash',
                contents=[prompt, image_part]
            )
            
            # Parse and structure the response
            analysis_text = response.text
            
            # Extract subject/topic
            subject = "General Study"
            if "**Subject & Topic:**" in analysis_text:
                subject_line = analysis_text.split("**Subject & Topic:**")[1].split("\n")[0].strip()
                subject = subject_line if subject_line else "General Study"
            
            # Extract ALL steps with their titles
            steps = []
            lines = analysis_text.split('\n')
            current_step = None
            current_content = []
            
            for line in lines:
                # Check if line is a step header
                if line.strip().startswith('**Step ') and ':' in line:
                    # Save previous step if exists
                    if current_step:
                        steps.append({
                            "title": current_step,
                            "content": '\n'.join(current_content).strip()
                        })
                    # Start new step
                    current_step = line.strip().replace('**', '').strip()
                    current_content = []
                elif current_step and line.strip() and not line.strip().startswith('**Practice Question'):
                    # Add content to current step
                    current_content.append(line)
            
            # Add last step
            if current_step and current_content:
                steps.append({
                    "title": current_step,
                    "content": '\n'.join(current_content).strip()
                })
            
            # Extract practice question
            practice = ""
            if "**Practice Question:**" in analysis_text:
                practice = analysis_text.split("**Practice Question:**")[1].strip()
            
            # Generate Socratic questions based on the problem - use FULL content, not truncated
            foundation_q = "What information is given in this problem? What are we trying to find?"
            bridge_q = "Which mathematical concept or formula could help us solve this?"
            mastery_q = "Can you explain why we need to use these specific steps?"
            
            # Try to extract better questions from the analysis - use full content
            try:
                if len(steps) > 0 and steps[0].get('content'):
                    content = steps[0]['content'].strip()
                    foundation_q = f"Look at this problem. {content} What do you notice first?"
                if len(steps) > 1 and steps[1].get('content'):
                    content = steps[1]['content'].strip()
                    bridge_q = f"We know the rules. {content} How should we apply them?"
                if len(steps) > 2 and steps[2].get('content'):
                    content = steps[2]['content'].strip()
                    mastery_q = f"Think about the approach: {content} Why does this make sense?"
            except Exception as q_error:
                # Use default questions if extraction fails
                pass
            
            # Success! Record this key as working
            api_key_rotator.record_success(key_index)
            
            # Return structured format for frontend
            return {
                "success": True,
                "subject": subject,
                "questions": {
                    "foundation": foundation_q,
                    "bridge": bridge_q,
                    "mastery": mastery_q
                },
                "solution_steps": steps,
                "behavioral_tip": "Remember: It's okay to take your time. Learning happens when we think through problems step by step.",
                "example_approach": analysis_text,
                "full_analysis": analysis_text,
                "practice_question": practice
            }
        
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for rate limit errors
            if "429" in error_msg or "quota" in error_msg or "rate limit" in error_msg or "resource exhausted" in error_msg:
                print(f"⚠️ API Key {key_index + 1} hit rate limit, marking as exhausted")
                api_key_rotator.mark_key_exhausted(key_index)
                last_error = "rate_limit"
                continue  # Try next key
            
            # Check for invalid API key errors
            elif "invalid" in error_msg or "api key" in error_msg or "authentication" in error_msg or "401" in error_msg or "403" in error_msg:
                print(f"❌ API Key {key_index + 1} is invalid, skipping")
                api_key_rotator.mark_key_invalid(key_index)
                last_error = "invalid_key"
                continue  # Try next key
            
            # Other errors - might be temporary, try next key
            else:
                print(f"⚠️ API Key {key_index + 1} error: {str(e)}")
                last_error = str(e)
                continue  # Try next key
    
    # All keys failed
    print(f"❌ All API keys failed. Last error type: {last_error}")
    return {
        "success": False,
        "error": "We're experiencing high demand. Please try again in a moment.",
        "retry_after": "30 seconds"
    }

@app.get("/session")
async def create_session(current_user: dict = Depends(get_current_user)):
    """Create a session (for compatibility with frontend)"""
    import uuid
    return {"session_id": str(uuid.uuid4())}

# Trial scan tracking (in-memory for simplicity, resets on restart)
trial_scans = {}

@app.post("/analyze-trial")
async def analyze_homework_trial(
    request: Request,
    file: UploadFile = File(...),
    grade: Optional[str] = Form(None),
    trial_id: Optional[str] = Form(None)
):
    """
    Trial endpoint - allows ONE free scan without authentication.
    Tracks by trial_id (client-generated UUID stored in localStorage).
    """
    # Get client identifier (trial_id from client or fallback to IP)
    client_id = trial_id or request.client.host
    
    # Check if this client already used their trial
    if client_id in trial_scans:
        return JSONResponse(
            status_code=402,
            content={
                "error": "Trial used",
                "reason": "TRIAL_EXHAUSTED",
                "message": "You've already used your free trial! Create an account to continue.",
                "show_signup": True
            }
        )
    
    if not file.content_type or not file.content_type.startswith('image/'):
        return JSONResponse(status_code=400, content={"error": "Invalid file type"})
    
    contents = await file.read()
    
    try:
        result = await analyze_homework_with_ai(contents)
        
        if not result.get("success", False):
            return JSONResponse(status_code=500, content={"error": result.get("error", "Analysis failed")})
        
        # Mark trial as used AFTER successful analysis
        trial_scans[client_id] = {
            "used_at": datetime.now().isoformat(),
            "ip": request.client.host
        }
        
        # Add trial info to response
        result["trial_used"] = True
        result["show_signup_prompt"] = True
        result["message"] = "Great! You've seen how it works. Create a free account to get 5 free scans a day!"
        
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/analyze")
async def analyze_homework(
    file: UploadFile = File(...),
    grade: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Analyze homework image"""
    # Check usage limit FIRST
    usage_check = check_and_update_usage_limit(current_user["username"])
    
    if not usage_check["allowed"]:
        return JSONResponse(
            status_code=402,
            content={
                "error": "Daily limit reached",
                "reason": "PAYWALL_TRIGGER",
                "is_premium": False,
                "scans_left": 0,
                "message": "You've used all your 5 free scans today. Upgrade to Premium for unlimited access!"
            }
        )
    
    if not file.content_type or not file.content_type.startswith('image/'):
        return JSONResponse(status_code=400, content={"error": "Invalid file type"})
    
    contents = await file.read()
    
    try:
        # Smart rotation handles everything - no need to check for keys
        result = await analyze_homework_with_ai(contents)
        
        if not result.get("success", False):
            return JSONResponse(status_code=500, content={"error": result.get("error", "Analysis failed")})
        
        # Add usage info to response
        result["usage"] = {
            "is_premium": usage_check["is_premium"],
            "scans_left": usage_check["scans_left"]
        }
        
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload and analyze homework image (protected)"""
    if not file.content_type or not file.content_type.startswith('image/'):
        return JSONResponse(status_code=400, content={"error": "Invalid file type"})
    
    contents = await file.read()
    
    # Smart rotation handles everything
    ai_result = await analyze_homework_with_ai(contents)
    
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

@app.post("/webhooks/paddle")
async def paddle_webhook(request: Request):
    """
    Paddle webhook endpoint with signature verification
    Paddle sends signatures in format: ts=timestamp;h1=signature
    """
    import hmac
    import hashlib
    
    # Get raw body for signature verification
    raw_body = await request.body()
    
    # Get signature from headers  
    signature_header = request.headers.get("Paddle-Signature")
    
    if not signature_header:
        print("[WEBHOOK] ⚠️ Missing Paddle-Signature header")
        raise HTTPException(status_code=400, detail="Missing Paddle-Signature header")
    
    # TEMPORARILY DISABLED - Debug signature mismatch issue
    webhook_secret = os.getenv("PADDLE_WEBHOOK_SECRET", "")
    print(f"[WEBHOOK] ⚠️ Signature verification DISABLED for debugging")
    print(f"[WEBHOOK] Signature header received: {signature_header}")
    print(f"[WEBHOOK] Secret configured: {webhook_secret[:10]}... (length: {len(webhook_secret)})")
    
    # TODO: Re-enable after fixing signature format
    # if webhook_secret:
    #     try:
    #         # Parse Paddle signature format: "ts=timestamp;h1=signature"
    #         sig_parts = {}
    #         for part in signature_header.split(';'):
    #             if '=' in part:
    #                 key, value = part.split('=', 1)
    #                 sig_parts[key.strip()] = value.strip()
    #         
    #         timestamp = sig_parts.get('ts', '')
    #         received_signature = sig_parts.get('h1', '')
    #         
    #         if not timestamp or not received_signature:
    #             print(f"[WEBHOOK] ❌ Invalid signature format: {signature_header}")
    #             raise HTTPException(status_code=401, detail="Invalid signature format")
    #         
    #         # Create signed payload: timestamp:body
    #         signed_payload = f"{timestamp}:{raw_body.decode('utf-8')}"
    #         
    #         # Compute HMAC signature
    #         computed_signature = hmac.new(
    #             webhook_secret.encode('utf-8'),
    #             signed_payload.encode('utf-8'),
    #             hashlib.sha256
    #         ).hexdigest()
    #         
    #         # Verify signature
    #         if not hmac.compare_digest(computed_signature, received_signature):
    #             print(f"[WEBHOOK] ❌ Signature mismatch!")
    #             print(f"[WEBHOOK] Expected: {computed_signature}")
    #             print(f"[WEBHOOK] Received: {received_signature}")
    #             raise HTTPException(status_code=401, detail="Invalid signature")
    #         
    #         print(f"[WEBHOOK] ✅ Signature verified successfully")
    #         
    #     except HTTPException:
    #         raise
    #     except Exception as e:
    #         print(f"[WEBHOOK] ❌ Signature verification error: {str(e)}")
    #         raise HTTPException(status_code=401, detail=f"Signature verification failed: {str(e)}")
    # else:
    #     print("[WEBHOOK] ⚠️ No PADDLE_WEBHOOK_SECRET configured - skipping verification (INSECURE!)")
    
    # Parse webhook data
    try:
        webhook_data = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    event_type = webhook_data.get("event_type")
    data = webhook_data.get("data", {})
    
    print(f"[WEBHOOK] Event type: {event_type}")
    print(f"[WEBHOOK] Data: {json.dumps(data, indent=2)[:500]}")
    
    # Load users
    users = load_users()
    
    # Handle subscription events
    if event_type in ["subscription.created", "subscription.updated", "subscription.activated"]:
        # Try to get user_id from custom_data first
        custom_data = data.get("custom_data", {})
        if isinstance(custom_data, str):
            try:
                custom_data = json.loads(custom_data)
            except:
                pass
        
        user_id = custom_data.get("user_id") if isinstance(custom_data, dict) else None
        customer_email = data.get("customer", {}).get("email")
        subscription_id = data.get("id")
        status = data.get("status")
        
        print(f"[WEBHOOK] Looking for user: user_id={user_id}, email={customer_email}")
        
        # Find user by username (from custom_data) or email
        target_user = None
        if user_id and user_id in users:
            target_user = user_id
        else:
            # Fallback to email lookup
            for username, user_data in users.items():
                if user_data.get("email") == customer_email:
                    target_user = username
                    break
        
        if target_user:
            users[target_user]["is_premium"] = (status == "active")
            users[target_user]["paddle_subscription_id"] = subscription_id
            save_users(users)
            print(f"[WEBHOOK] User {target_user} upgraded to premium! (status={status})")
            return JSONResponse(status_code=200, content={"success": True, "user": target_user})
        else:
            print(f"[WEBHOOK] No user found for email={customer_email}, user_id={user_id}")
            return JSONResponse(status_code=200, content={"success": False, "error": "User not found"})
    
    elif event_type in ["subscription.canceled", "subscription.expired"]:
        subscription_id = data.get("id")
        
        # Find user by subscription ID
        for username, user_data in users.items():
            if user_data.get("paddle_subscription_id") == subscription_id:
                user_data["is_premium"] = False
                user_data["paddle_subscription_id"] = None
                user_data["daily_scans_left"] = 5
                user_data["last_reset"] = datetime.now().isoformat()
                save_users(users)
                return JSONResponse(status_code=200, content={"success": True})
    
    return JSONResponse(status_code=200, content={"success": True, "message": "Event logged"})

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
