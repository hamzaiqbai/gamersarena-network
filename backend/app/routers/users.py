"""
Users Router - Profile management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import get_db
from ..models.user import User
from ..schemas.user import UserResponse, UserProfileUpdate
from ..utils.security import get_current_user

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile"""
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user profile.
    This is called after Google OAuth signup to complete profile.
    """
    # Update user fields
    current_user.full_name = profile_data.full_name
    current_user.age = profile_data.age
    current_user.city = profile_data.city
    current_user.country = profile_data.country
    current_user.whatsapp_number = profile_data.whatsapp_number
    current_user.player_id = profile_data.player_id
    current_user.preferred_game = profile_data.preferred_game
    current_user.preferred_payment = profile_data.preferred_payment
    
    if profile_data.mobile_wallet_number:
        current_user.mobile_wallet_number = profile_data.mobile_wallet_number
    
    # Check if all required fields are filled
    if current_user.whatsapp_verified:
        current_user.profile_completed = True
    
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.get("/check-profile-status")
async def check_profile_status(
    current_user: User = Depends(get_current_user)
):
    """Check what profile fields are missing"""
    missing_fields = []
    
    if not current_user.full_name:
        missing_fields.append("full_name")
    if not current_user.age:
        missing_fields.append("age")
    if not current_user.city:
        missing_fields.append("city")
    if not current_user.country:
        missing_fields.append("country")
    if not current_user.whatsapp_number:
        missing_fields.append("whatsapp_number")
    if not current_user.whatsapp_verified:
        missing_fields.append("whatsapp_verification")
    if not current_user.player_id:
        missing_fields.append("player_id")
    
    return {
        "profile_completed": current_user.profile_completed,
        "whatsapp_verified": current_user.whatsapp_verified,
        "missing_fields": missing_fields
    }


@router.get("/search")
async def search_users(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search for a user by email (for token transfers).
    Returns limited public info.
    """
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot search for yourself"
        )
    
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url
    }
