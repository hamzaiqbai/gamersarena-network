"""
User Schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """Base user schema"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None


class UserCreate(BaseModel):
    """Schema for creating a user via Google OAuth"""
    google_id: str
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    full_name: str = Field(..., min_length=2, max_length=255)
    age: int = Field(..., ge=13, le=100)  # Minimum age 13
    city: str = Field(..., min_length=2, max_length=100)
    country: str = Field(..., min_length=2, max_length=100)
    whatsapp_number: str = Field(..., pattern=r'^\+?[0-9]{10,15}$')
    player_id: str = Field(..., min_length=3, max_length=100)
    preferred_game: Optional[str] = None
    preferred_payment: str = Field(default="easypaisa", pattern=r'^(easypaisa|jazzcash|stripe)$')
    mobile_wallet_number: Optional[str] = None


class WhatsAppVerifyRequest(BaseModel):
    """Request to send WhatsApp verification code"""
    whatsapp_number: str = Field(..., pattern=r'^\+?[0-9]{10,15}$')


class WhatsAppConfirmRequest(BaseModel):
    """Request to confirm WhatsApp verification code"""
    code: str = Field(..., min_length=6, max_length=6)


class UserResponse(BaseModel):
    """User response schema"""
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    age: Optional[int] = None
    city: Optional[str] = None
    country: Optional[str] = None
    whatsapp_number: Optional[str] = None
    whatsapp_verified: bool = False
    player_id: Optional[str] = None
    preferred_game: Optional[str] = None
    preferred_payment: Optional[str] = None
    profile_completed: bool = False
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserPublicResponse(BaseModel):
    """Public user info (for leaderboards, etc.)"""
    id: UUID
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    player_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class GoogleAuthCallback(BaseModel):
    """Google OAuth callback data"""
    code: str
    state: Optional[str] = None
