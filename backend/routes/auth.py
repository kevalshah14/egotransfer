"""
Authentication Routes
=====================
Google OAuth authentication routes compatible with Better Auth.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import RedirectResponse
from typing import Optional
import os
import logging
import secrets
import httpx
from datetime import datetime, timedelta

from jose import jwt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/callback/google")
BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"

# In-memory session storage (use Redis/DB in production)
oauth_sessions = {}
user_sessions = {}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


@router.get("/sign-in/google")
async def sign_in_google():
    """Initiate Google OAuth sign-in flow."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.error("Google OAuth credentials not configured")
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
        )
    
    logger.info(f"Starting OAuth flow with redirect URI: {GOOGLE_REDIRECT_URI}")
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    oauth_sessions[state] = {"created_at": datetime.utcnow()}
    
    # Google OAuth authorization URL
    from urllib.parse import quote_plus
    redirect_uri_encoded = quote_plus(GOOGLE_REDIRECT_URI)
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri_encoded}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile&"
        f"state={state}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    logger.debug(f"OAuth URL generated (client_id: {GOOGLE_CLIENT_ID[:20]}...)")
    return {"url": auth_url}


@router.get("/callback/google")
async def google_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None
):
    """Handle Google OAuth callback."""
    if error:
        logger.error(f"OAuth error: {error}")
        return RedirectResponse(url=f"{BASE_URL}/auth/error?error={error}")
    
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")
    
    # Verify state
    if state not in oauth_sessions:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    try:
        # Exchange authorization code for tokens
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            token_response.raise_for_status()
            tokens = token_response.json()
        
        # Get user info from Google
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            user_response.raise_for_status()
            user_info = user_response.json()
        
        # Create or update user session
        user_id = user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("picture")
        
        # Create JWT token
        token_data = {
            "sub": user_id,
            "email": email,
            "name": name,
            "picture": picture,
        }
        access_token = create_access_token(token_data)
        
        # Store session
        session_id = secrets.token_urlsafe(32)
        user_sessions[session_id] = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "created_at": datetime.utcnow(),
        }
        
        # Clean up OAuth session
        del oauth_sessions[state]
        
        # Redirect to frontend with token
        redirect_url = f"{BASE_URL}/?token={access_token}&session={session_id}"
        logger.info(f"Redirecting to: {redirect_url}")
        return RedirectResponse(url=redirect_url)
        
    except httpx.HTTPStatusError as e:
        error_detail = "Unknown error"
        try:
            error_response = e.response.json()
            error_detail = error_response.get("error_description", error_response.get("error", str(e)))
            logger.error(f"OAuth token exchange failed: {error_detail}")
        except:
            logger.error(f"OAuth token exchange failed: {e}")
            error_detail = str(e)
        
        # Provide helpful error messages
        if "invalid_client" in str(error_detail).lower():
            raise HTTPException(
                status_code=500,
                detail=f"Invalid OAuth client. Check that Client ID and Secret are correct, and redirect URI '{GOOGLE_REDIRECT_URI}' matches Google Cloud Console."
            )
        elif "redirect_uri_mismatch" in str(error_detail).lower():
            raise HTTPException(
                status_code=500,
                detail=f"Redirect URI mismatch. Ensure '{GOOGLE_REDIRECT_URI}' is added to Authorized redirect URIs in Google Cloud Console."
            )
        else:
            raise HTTPException(status_code=500, detail=f"Failed to exchange authorization code: {error_detail}")
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.get("/session")
async def get_session(session: Optional[str] = None):
    """Get current session information."""
    if not session:
        return {"user": None, "session": None}
    
    if session not in user_sessions:
        return {"user": None, "session": None}
    
    user_data = user_sessions[session]
    return {
        "user": {
            "id": user_data["user_id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "picture": user_data["picture"],
        },
        "session": session,
    }


@router.post("/sign-out")
async def sign_out(session: Optional[str] = None):
    """Sign out the current user."""
    if session and session in user_sessions:
        del user_sessions[session]
    
    return {"success": True, "message": "Signed out successfully"}


@router.get("/user")
async def get_current_user(request: Request):
    """Get current authenticated user."""
    # Get session from query parameter or cookie
    session = request.query_params.get("session")
    if not session:
        # Try to get from cookie
        session = request.cookies.get("auth_session")
    
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if session not in user_sessions:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_data = user_sessions[session]
    return {
        "id": user_data["user_id"],
        "email": user_data["email"],
        "name": user_data["name"],
        "picture": user_data["picture"],
    }


# Dependency to get current user (optional - returns None if not authenticated)
async def get_current_user_optional(request: Request) -> Optional[dict]:
    """Get current authenticated user or None if not authenticated."""
    # Get session from query parameter, cookie, or Authorization header
    session = request.query_params.get("session")
    if not session:
        session = request.cookies.get("auth_session")
    if not session:
        # Try to get from Authorization header (Bearer token format)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session = auth_header.split(" ")[1]
    
    if not session or session not in user_sessions:
        return None
    
    user_data = user_sessions[session]
    return {
        "id": user_data["user_id"],
        "email": user_data["email"],
        "name": user_data["name"],
        "picture": user_data["picture"],
    }


# Dependency to get current user (required - raises exception if not authenticated)
async def get_current_user_required(request: Request) -> dict:
    """Get current authenticated user or raise 401 if not authenticated."""
    user = await get_current_user_optional(request)
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Authentication required. Please sign in to access this resource."
        )
    return user

