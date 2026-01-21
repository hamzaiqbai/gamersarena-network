"""
Authentication Router - Google OAuth2
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import httpx
import jwt

from ..database import get_db
from ..config import settings
from ..models.user import User
from ..models.wallet import Wallet
from ..schemas.user import UserResponse, GoogleAuthCallback
from ..utils.security import create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Google OAuth URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.get("/google")
async def google_login():
    """
    Initiate Google OAuth login.
    Redirects user to Google's consent page.
    """
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    auth_url = f"{GOOGLE_AUTH_URL}?{query_string}"
    
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback.
    Exchanges code for tokens, creates/updates user, and redirects to frontend.
    """
    try:
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI
                }
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for tokens"
                )
            
            tokens = token_response.json()
            access_token = tokens.get("access_token")
            
            # Get user info from Google
            userinfo_response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if userinfo_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info from Google"
                )
            
            google_user = userinfo_response.json()
        
        # Check if user exists
        user = db.query(User).filter(User.google_id == google_user["id"]).first()
        
        if not user:
            # Create new user
            user = User(
                google_id=google_user["id"],
                email=google_user["email"],
                full_name=google_user.get("name"),
                avatar_url=google_user.get("picture"),
                profile_completed=False
            )
            db.add(user)
            db.flush()
            
            # Create wallet for new user
            wallet = Wallet(user_id=user.id)
            db.add(wallet)
            db.commit()
            db.refresh(user)
        else:
            # Update last login
            user.last_login = datetime.utcnow()
            user.avatar_url = google_user.get("picture", user.avatar_url)
            db.commit()
        
        # Create JWT token for our app
        app_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Determine redirect URL based on profile completion
        # In production, frontend is served from same origin
        if settings.ENVIRONMENT == "production":
            frontend_base = ""  # Same origin, just use relative paths
        else:
            frontend_base = settings.FRONTEND_URL
            
        if user.profile_completed:
            redirect_url = f"{frontend_base}/dashboard.html?token={app_token}"
        else:
            redirect_url = f"{frontend_base}/profile.html?token={app_token}"
        
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user information"""
    return current_user


@router.post("/logout")
async def logout(response: Response):
    """
    Logout user by instructing frontend to clear token.
    JWT tokens are stateless, so we just return success.
    """
    return {"message": "Logged out successfully"}


@router.get("/check")
async def check_auth(current_user: User = Depends(get_current_user)):
    """Check if user is authenticated"""
    return {
        "authenticated": True,
        "user_id": str(current_user.id),
        "email": current_user.email,
        "profile_completed": current_user.profile_completed
    }


# ============================================================
# DEVELOPMENT ONLY - Remove in production
# ============================================================
@router.get("/dev-login")
async def dev_login(
    email: str = "testuser@example.com",
    name: str = "Test User",
    db: Session = Depends(get_db)
):
    """
    Development login bypass - creates a test user and returns token.
    DO NOT USE IN PRODUCTION!
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev login is disabled in production"
        )
    
    # Check if test user exists
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Create test user
        import uuid
        user = User(
            google_id=f"dev_{uuid.uuid4().hex[:8]}",
            email=email,
            full_name=name,
            avatar_url="https://ui-avatars.com/api/?name=" + name.replace(" ", "+") + "&background=6c5ce7&color=fff",
            profile_completed=False
        )
        db.add(user)
        db.flush()
        
        # Create wallet with some test tokens
        wallet = Wallet(
            user_id=user.id,
            virtual_tokens=500,  # Give test user some tokens
            reward_tokens=100
        )
        db.add(wallet)
        db.commit()
        db.refresh(user)
    
    # Create JWT token
    app_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    # Determine redirect URL
    if user.profile_completed:
        redirect_url = f"{settings.FRONTEND_URL}/dashboard.html?token={app_token}"
    else:
        redirect_url = f"{settings.FRONTEND_URL}/profile.html?token={app_token}"
    
    return RedirectResponse(url=redirect_url)
