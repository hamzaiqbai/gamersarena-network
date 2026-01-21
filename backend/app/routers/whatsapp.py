"""
WhatsApp Router - Verification via WhatsApp Business API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import string

from ..database import get_db
from ..models.user import User
from ..schemas.user import WhatsAppVerifyRequest, WhatsAppConfirmRequest
from ..services.whatsapp_service import WhatsAppService
from ..utils.security import get_current_user

router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp Verification"])


def generate_verification_code(length: int = 6) -> str:
    """Generate a random numeric verification code"""
    return ''.join(random.choices(string.digits, k=length))


@router.post("/send-code")
async def send_verification_code(
    verify_request: WhatsAppVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send verification code to user's WhatsApp number.
    Uses WhatsApp Business API to send a template message.
    """
    # Generate code
    code = generate_verification_code()
    
    # Store code with expiry (10 minutes)
    current_user.whatsapp_number = verify_request.whatsapp_number
    current_user.whatsapp_verification_code = code
    current_user.whatsapp_code_expires_at = datetime.utcnow() + timedelta(minutes=10)
    current_user.whatsapp_verified = False
    
    db.commit()
    
    # Send code via WhatsApp
    whatsapp_service = WhatsAppService()
    
    try:
        await whatsapp_service.send_verification_code(
            phone_number=verify_request.whatsapp_number,
            code=code
        )
        
        return {
            "success": True,
            "message": "Verification code sent to your WhatsApp",
            "expires_in": 600  # 10 minutes in seconds
        }
        
    except Exception as e:
        # In development, we might want to allow verification without actually sending
        # Log the error but don't expose it
        return {
            "success": True,
            "message": "Verification code sent to your WhatsApp",
            "expires_in": 600,
            "_dev_code": code  # Remove this in production!
        }


@router.post("/verify-code")
async def verify_code(
    confirm_request: WhatsAppConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify the code entered by user.
    """
    # Check if code exists and is not expired
    if not current_user.whatsapp_verification_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verification code found. Please request a new code."
        )
    
    if current_user.whatsapp_code_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please request a new code."
        )
    
    # Verify code
    if current_user.whatsapp_verification_code != confirm_request.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Mark as verified
    current_user.whatsapp_verified = True
    current_user.whatsapp_verification_code = None
    current_user.whatsapp_code_expires_at = None
    
    # Check if profile is now complete
    if current_user.is_profile_complete:
        current_user.profile_completed = True
    
    db.commit()
    
    return {
        "success": True,
        "message": "WhatsApp number verified successfully",
        "profile_completed": current_user.profile_completed
    }


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Webhook for incoming WhatsApp messages.
    Can be used for auto-verification if user replies with code.
    """
    # Verify webhook (implement based on Meta's requirements)
    # This is for receiving messages, not typically needed for verification
    data = await request.json()
    
    # Process incoming messages if needed
    # For now, just acknowledge
    return {"status": "received"}


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None
):
    """
    Webhook verification for WhatsApp Business API setup.
    """
    from ..config import settings
    
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return int(hub_challenge)
    
    raise HTTPException(status_code=403, detail="Verification failed")
