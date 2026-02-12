"""
Admin Router - Admin panel API endpoints
Handles admin authentication, dashboard stats, and CRUD operations
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, EmailStr
import jwt
import secrets
import os
import uuid

from ..database import get_db
from ..config import settings
from ..models.admin import AdminUser
from ..models.user import User
from ..models.wallet import Wallet
from ..models.tournament import Tournament, TokenBundle
from ..models.transaction import Transaction
from ..models.registration import Registration
from ..models.settings import SiteSettings, MAINTENANCE_ENABLED, MAINTENANCE_END_TIME, MAINTENANCE_MESSAGE, MAINTENANCE_TITLE
from ..models.product import Product, ProductType, ProductCategory, ProductValidity

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Upload directory for banners
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "banners")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============================================================
# Pydantic Schemas
# ============================================================

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str

class AdminLoginResponse(BaseModel):
    token: str
    admin: dict

class AdminCreateRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "admin"

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class TournamentCreateRequest(BaseModel):
    title: str
    game: str
    description: Optional[str] = None
    rules: Optional[str] = None
    entry_fee: int = 0
    prize_pool: int = 0
    first_place_reward: int = 0
    second_place_reward: int = 0
    third_place_reward: int = 0
    fourth_place_reward: int = 0
    fifth_place_reward: int = 0
    max_participants: int = 100
    min_participants: int = 2
    registration_start: Optional[datetime] = None
    registration_end: Optional[datetime] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    status: str = "upcoming"
    banner_url: Optional[str] = None

class TournamentUpdateRequest(BaseModel):
    title: Optional[str] = None
    game: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[str] = None
    entry_fee: Optional[int] = None
    prize_pool: Optional[int] = None
    first_place_reward: Optional[int] = None
    second_place_reward: Optional[int] = None
    third_place_reward: Optional[int] = None
    fourth_place_reward: Optional[int] = None
    fifth_place_reward: Optional[int] = None
    max_participants: Optional[int] = None
    status: Optional[str] = None
    registration_start: Optional[datetime] = None
    registration_end: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    banner_url: Optional[str] = None

# ============================================================
# Helper Functions
# ============================================================

def create_admin_token(admin_id: str, email: str) -> str:
    """Create JWT token for admin"""
    payload = {
        "sub": admin_id,
        "email": email,
        "type": "admin",
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_admin_token(token: str) -> dict:
    """Verify admin JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "admin":
            raise HTTPException(status_code=401, detail="Invalid admin token")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_admin(authorization: str = Header(None), db: Session = Depends(get_db)) -> AdminUser:
    """Dependency to get current admin from token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = authorization.split(" ")[1]
    payload = verify_admin_token(token)
    
    admin = db.query(AdminUser).filter(AdminUser.id == payload["sub"]).first()
    if not admin or not admin.is_active:
        raise HTTPException(status_code=401, detail="Admin not found or inactive")
    
    return admin

# ============================================================
# Authentication Endpoints
# ============================================================

@router.post("/auth/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest, db: Session = Depends(get_db)):
    """Admin login with email and password"""
    admin = db.query(AdminUser).filter(AdminUser.email == request.email).first()
    
    if not admin or not admin.check_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not admin.is_active:
        raise HTTPException(status_code=401, detail="Account is disabled")
    
    # Update last login
    admin.last_login = datetime.utcnow()
    db.commit()
    
    token = create_admin_token(str(admin.id), admin.email)
    
    return {
        "token": token,
        "admin": admin.to_dict()
    }

@router.get("/auth/check-setup")
async def check_setup_needed(db: Session = Depends(get_db)):
    """
    Check if first-time setup is needed (no admins exist).
    """
    existing = db.query(AdminUser).count()
    return {
        "setup_needed": existing == 0,
        "admin_count": existing
    }

@router.post("/auth/setup")
async def admin_setup(request: AdminCreateRequest, db: Session = Depends(get_db)):
    """
    First-time admin setup. Only works if no admins exist.
    """
    existing = db.query(AdminUser).count()
    if existing > 0:
        raise HTTPException(status_code=403, detail="Admin already exists. Use login instead.")
    
    admin = AdminUser(
        email=request.email,
        full_name=request.full_name,
        role="superadmin"  # First admin is always superadmin
    )
    admin.set_password(request.password)
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    token = create_admin_token(str(admin.id), admin.email)
    
    return {
        "message": "Admin account created successfully",
        "token": token,
        "admin": admin.to_dict()
    }

@router.post("/auth/reset-password-request")
async def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset - generates token"""
    admin = db.query(AdminUser).filter(AdminUser.email == request.email).first()
    
    if admin:
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        admin.password_reset_token = reset_token
        admin.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        
        # In production, send email with reset link
        # For now, return the token (remove in production!)
        return {
            "message": "Password reset token generated",
            "reset_token": reset_token,  # Remove this line in production!
            "note": "In production, this token would be sent via email"
        }
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/auth/reset-password")
async def reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Reset password using token"""
    admin = db.query(AdminUser).filter(
        AdminUser.password_reset_token == request.token,
        AdminUser.password_reset_expires > datetime.utcnow()
    ).first()
    
    if not admin:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    admin.set_password(request.new_password)
    admin.password_reset_token = None
    admin.password_reset_expires = None
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.get("/auth/me")
async def get_admin_profile(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get current admin profile"""
    admin = get_current_admin(authorization, db)
    return admin.to_dict()

# ============================================================
# Dashboard Statistics
# ============================================================

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get overview statistics for dashboard"""
    get_current_admin(authorization, db)
    
    # User stats
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    verified_users = db.query(User).filter(User.whatsapp_verified == True).count()
    new_users_today = db.query(User).filter(
        User.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
    ).count()
    
    # Wallet stats
    total_virtual_tokens = db.query(func.sum(Wallet.virtual_tokens)).scalar() or 0
    total_reward_tokens = db.query(func.sum(Wallet.reward_tokens)).scalar() or 0
    total_spent_pkr = db.query(func.sum(Wallet.total_spent_pkr)).scalar() or 0
    
    # Tournament stats
    total_tournaments = db.query(Tournament).count()
    active_tournaments = db.query(Tournament).filter(
        Tournament.status.in_(["upcoming", "registration_open", "active"])
    ).count()
    completed_tournaments = db.query(Tournament).filter(
        Tournament.status == "completed"
    ).count()
    
    # Registration stats
    total_registrations = db.query(Registration).count()
    
    # Transaction stats
    total_transactions = db.query(Transaction).count()
    completed_transactions = db.query(Transaction).filter(
        Transaction.status == "completed"
    ).count()
    pending_transactions = db.query(Transaction).filter(
        Transaction.status == "pending"
    ).count()
    failed_transactions = db.query(Transaction).filter(
        Transaction.status == "failed"
    ).count()
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "verified": verified_users,
            "new_today": new_users_today,
            "blocked": total_users - active_users
        },
        "wallets": {
            "total_virtual_tokens": total_virtual_tokens,
            "total_reward_tokens": total_reward_tokens,
            "total_spent_pkr": float(total_spent_pkr)
        },
        "tournaments": {
            "total": total_tournaments,
            "active": active_tournaments,
            "completed": completed_tournaments,
            "total_registrations": total_registrations
        },
        "transactions": {
            "total": total_transactions,
            "completed": completed_transactions,
            "pending": pending_transactions,
            "failed": failed_transactions
        }
    }

# ============================================================
# User Management
# ============================================================

@router.get("/users")
async def list_users(
    authorization: str = Header(None),
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    search_by: Optional[str] = None,  # email, phone, whatsapp, player_id, name, all
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all users with pagination and filters"""
    get_current_admin(authorization, db)
    
    query = db.query(User)
    
    if search:
        if search_by == "email":
            query = query.filter(User.email.ilike(f"%{search}%"))
        elif search_by == "phone":
            query = query.filter(User.whatsapp_number.ilike(f"%{search}%"))
        elif search_by == "whatsapp":
            query = query.filter(User.whatsapp_number.ilike(f"%{search}%"))
        elif search_by == "player_id":
            query = query.filter(User.player_id.ilike(f"%{search}%"))
        elif search_by == "name":
            query = query.filter(User.full_name.ilike(f"%{search}%"))
        else:
            # Search all fields
            query = query.filter(
                (User.email.ilike(f"%{search}%")) |
                (User.full_name.ilike(f"%{search}%")) |
                (User.player_id.ilike(f"%{search}%")) |
                (User.whatsapp_number.ilike(f"%{search}%"))
            )
    
    if status == "active":
        query = query.filter(User.is_active == True)
    elif status == "blocked":
        query = query.filter(User.is_active == False)
    elif status == "verified":
        query = query.filter(User.whatsapp_verified == True)
    
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "users": [u.to_dict() for u in users]
    }

@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get detailed user information"""
    get_current_admin(authorization, db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    registrations = db.query(Registration).filter(Registration.user_id == user_id).all()
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.created_at.desc()).limit(20).all()
    
    return {
        "user": user.to_dict(),
        "wallet": wallet.to_dict() if wallet else None,
        "registrations": [r.to_dict() for r in registrations],
        "recent_transactions": [t.to_dict() for t in transactions]
    }

@router.put("/users/{user_id}/block")
async def block_user(
    user_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Block a user"""
    get_current_admin(authorization, db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = False
    db.commit()
    
    return {"message": "User blocked successfully"}

@router.put("/users/{user_id}/unblock")
async def unblock_user(
    user_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Unblock a user"""
    get_current_admin(authorization, db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    db.commit()
    
    return {"message": "User unblocked successfully"}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Delete a user and all associated data"""
    get_current_admin(authorization, db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete associated data
    db.query(Transaction).filter(Transaction.user_id == user_id).delete()
    db.query(Registration).filter(Registration.user_id == user_id).delete()
    db.query(Wallet).filter(Wallet.user_id == user_id).delete()
    
    # Delete the user
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

# ============================================================
# Wallet Management
# ============================================================

@router.get("/wallets")
async def list_wallets(
    authorization: str = Header(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all wallets with user info"""
    get_current_admin(authorization, db)
    
    wallets = db.query(Wallet).join(User).order_by(Wallet.updated_at.desc()).offset(skip).limit(limit).all()
    total = db.query(Wallet).count()
    
    result = []
    for w in wallets:
        data = w.to_dict()
        data["user_email"] = w.user.email if w.user else None
        data["user_name"] = w.user.full_name if w.user else None
        result.append(data)
    
    return {
        "total": total,
        "wallets": result
    }

@router.post("/wallets/{user_id}/add-tokens")
async def add_tokens_to_wallet(
    user_id: str,
    amount: int,
    token_type: str = "virtual",  # virtual or reward
    reason: str = "Admin adjustment",
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Manually add tokens to a user's wallet"""
    admin = get_current_admin(authorization, db)
    
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    if token_type == "virtual":
        wallet.virtual_tokens += amount
    else:
        wallet.reward_tokens += amount
    
    # Create transaction record
    tx = Transaction(
        user_id=user_id,
        type="bonus",
        status="completed",
        token_amount=amount,
        token_type=token_type,
        description=f"Admin adjustment: {reason}",
        notes=f"Added by admin {admin.email}"
    )
    tx.mark_completed()
    db.add(tx)
    db.commit()
    
    return {"message": f"Added {amount} {token_type} tokens", "new_balance": wallet.total_balance}

# ============================================================
# Tournament Management
# ============================================================

@router.get("/tournaments")
async def list_tournaments_admin(
    authorization: str = Header(None),
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    game: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all tournaments for admin"""
    get_current_admin(authorization, db)
    
    query = db.query(Tournament)
    
    if status:
        query = query.filter(Tournament.status == status)
    if game:
        query = query.filter(Tournament.game == game)
    
    total = query.count()
    tournaments = query.order_by(Tournament.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "tournaments": [t.to_dict(include_room_info=True) for t in tournaments]
    }

@router.post("/upload/banner")
async def upload_banner(
    file: UploadFile = File(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Upload a tournament banner image"""
    get_current_admin(authorization, db)
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: JPEG, PNG, GIF, WebP")
    
    # Validate file size (max 5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max size: 5MB")
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    with open(filepath, "wb") as f:
        f.write(contents)
    
    # Return the URL path (use API path so nginx proxies it)
    banner_url = f"/api/admin/uploads/banners/{filename}"
    
    return {
        "message": "Banner uploaded successfully",
        "banner_url": banner_url,
        "filename": filename
    }

# Route to serve banner images (public access)
@router.get("/uploads/banners/{filename}", include_in_schema=False)
async def serve_banner(filename: str):
    """Serve banner image files"""
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Banner not found")
    return FileResponse(filepath)

@router.post("/tournaments")
async def create_tournament(
    request: TournamentCreateRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Create a new tournament"""
    get_current_admin(authorization, db)
    
    # Generate slug from title
    import re
    slug = re.sub(r'[^a-z0-9]+', '-', request.title.lower()).strip('-')
    slug = f"{slug}-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
    
    tournament = Tournament(
        title=request.title,
        slug=slug,
        game=request.game,
        description=request.description,
        rules=request.rules,
        entry_fee=request.entry_fee,
        prize_pool=request.prize_pool,
        first_place_reward=request.first_place_reward,
        second_place_reward=request.second_place_reward,
        third_place_reward=request.third_place_reward,
        fourth_place_reward=request.fourth_place_reward,
        fifth_place_reward=request.fifth_place_reward,
        max_participants=request.max_participants,
        min_participants=request.min_participants,
        registration_start=request.registration_start,
        registration_end=request.registration_end,
        start_date=request.start_date,
        end_date=request.end_date,
        status=request.status,
        banner_url=request.banner_url
    )
    
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    
    return {
        "message": "Tournament created successfully",
        "tournament": tournament.to_dict(include_room_info=True)
    }

@router.get("/tournaments/{tournament_id}")
async def get_tournament_admin(
    tournament_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get tournament details including registrations"""
    get_current_admin(authorization, db)
    
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    registrations = db.query(Registration).filter(
        Registration.tournament_id == tournament_id
    ).all()
    
    return {
        "tournament": tournament.to_dict(include_room_info=True),
        "registrations": [r.to_dict(include_user=True) for r in registrations]
    }

@router.put("/tournaments/{tournament_id}")
async def update_tournament(
    tournament_id: str,
    request: TournamentUpdateRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Update tournament details"""
    get_current_admin(authorization, db)
    
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(tournament, field, value)
    
    db.commit()
    db.refresh(tournament)
    
    return {
        "message": "Tournament updated successfully",
        "tournament": tournament.to_dict(include_room_info=True)
    }

@router.delete("/tournaments/{tournament_id}")
async def delete_tournament(
    tournament_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Delete a tournament (soft delete by setting status to cancelled)"""
    get_current_admin(authorization, db)
    
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Check if there are registrations
    reg_count = db.query(Registration).filter(Registration.tournament_id == tournament_id).count()
    if reg_count > 0:
        # Soft delete - just cancel
        tournament.status = "cancelled"
        db.commit()
        return {"message": "Tournament cancelled (has registrations)"}
    else:
        # Hard delete if no registrations
        db.delete(tournament)
        db.commit()
        return {"message": "Tournament deleted"}

@router.post("/tournaments/{tournament_id}/complete")
async def complete_tournament(
    tournament_id: str,
    winners: Optional[dict] = None,  # {"1st": user_id, "2nd": user_id, "3rd": user_id}
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Mark tournament as completed and distribute rewards"""
    get_current_admin(authorization, db)
    
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    tournament.status = "completed"
    
    # Distribute rewards if winners provided
    if winners:
        rewards = {
            "1st": tournament.first_place_reward,
            "2nd": tournament.second_place_reward,
            "3rd": tournament.third_place_reward,
            "4th": tournament.fourth_place_reward,
            "5th": tournament.fifth_place_reward
        }
        
        for place, user_id in winners.items():
            if user_id and rewards.get(place, 0) > 0:
                wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
                if wallet:
                    wallet.add_reward_tokens(rewards[place])
                    
                    # Update registration
                    reg = db.query(Registration).filter(
                        Registration.tournament_id == tournament_id,
                        Registration.user_id == user_id
                    ).first()
                    if reg:
                        reg.position = int(place[0])
                        reg.reward_earned = rewards[place]
                    
                    # Create transaction
                    tx = Transaction(
                        user_id=user_id,
                        type="tournament_reward",
                        status="completed",
                        token_amount=rewards[place],
                        token_type="reward",
                        tournament_id=tournament_id,
                        description=f"{place} place in {tournament.title}"
                    )
                    tx.mark_completed()
                    db.add(tx)
    
    db.commit()
    
    return {"message": "Tournament completed and rewards distributed"}

# ============================================================
# Payment/Transaction Management
# ============================================================

@router.get("/transactions")
async def list_transactions(
    authorization: str = Header(None),
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all transactions"""
    get_current_admin(authorization, db)
    
    query = db.query(Transaction)
    
    if status:
        query = query.filter(Transaction.status == status)
    if type:
        query = query.filter(Transaction.type == type)
    
    total = query.count()
    transactions = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "transactions": [t.to_dict() for t in transactions]
    }

@router.get("/transactions/stats")
async def get_transaction_stats(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get transaction statistics"""
    get_current_admin(authorization, db)
    
    # By status
    status_stats = db.query(
        Transaction.status,
        func.count(Transaction.id)
    ).group_by(Transaction.status).all()
    
    # By type
    type_stats = db.query(
        Transaction.type,
        func.count(Transaction.id)
    ).group_by(Transaction.type).all()
    
    # Revenue
    total_revenue = db.query(func.sum(Transaction.amount_pkr)).filter(
        Transaction.type == "purchase",
        Transaction.status == "completed"
    ).scalar() or 0
    
    return {
        "by_status": {s: c for s, c in status_stats},
        "by_type": {t: c for t, c in type_stats},
        "total_revenue_pkr": float(total_revenue)
    }

# ============================================================
# Rewards/Leaderboard
# ============================================================

@router.get("/rewards/leaderboard")
async def get_rewards_leaderboard(
    authorization: str = Header(None),
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get top earners leaderboard"""
    get_current_admin(authorization, db)
    
    top_earners = db.query(Wallet).join(User).order_by(
        Wallet.total_tokens_earned.desc()
    ).limit(limit).all()
    
    return {
        "leaderboard": [
            {
                "user_id": str(w.user_id),
                "user_name": w.user.full_name if w.user else "Unknown",
                "player_id": w.user.player_id if w.user else None,
                "total_earned": w.total_tokens_earned,
                "current_reward_balance": w.reward_tokens
            }
            for w in top_earners
        ]
    }

@router.get("/rewards/stats")
async def get_rewards_stats(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get reward distribution statistics"""
    get_current_admin(authorization, db)
    
    total_distributed = db.query(func.sum(Wallet.total_tokens_earned)).scalar() or 0
    total_reward_balance = db.query(func.sum(Wallet.reward_tokens)).scalar() or 0
    
    # Top tournaments by rewards
    top_tournaments = db.query(
        Tournament.title,
        Tournament.prize_pool,
        func.count(Registration.id).label('participants')
    ).join(Registration, isouter=True).filter(
        Tournament.status == "completed"
    ).group_by(Tournament.id).order_by(Tournament.prize_pool.desc()).limit(10).all()
    
    return {
        "total_distributed": total_distributed,
        "current_reward_balance": total_reward_balance,
        "top_tournaments": [
            {"title": t.title, "prize_pool": t.prize_pool, "participants": t.participants}
            for t in top_tournaments
        ]
    }

# ============================================================
# Maintenance Mode
# ============================================================

class MaintenanceSettingsRequest(BaseModel):
    enabled: bool = False
    end_time: Optional[datetime] = None
    title: Optional[str] = "Under Maintenance"
    message: Optional[str] = "We're performing scheduled maintenance. We'll be back soon!"

def get_setting(db: Session, key: str) -> Optional[str]:
    """Get a setting value by key"""
    setting = db.query(SiteSettings).filter(SiteSettings.key == key).first()
    return setting.value if setting else None

def set_setting(db: Session, key: str, value: str):
    """Set a setting value"""
    setting = db.query(SiteSettings).filter(SiteSettings.key == key).first()
    if setting:
        setting.value = value
    else:
        setting = SiteSettings(key=key, value=value)
        db.add(setting)
    db.commit()

@router.get("/maintenance")
async def get_maintenance_settings(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get current maintenance mode settings"""
    get_current_admin(authorization, db)
    
    enabled = get_setting(db, MAINTENANCE_ENABLED)
    end_time = get_setting(db, MAINTENANCE_END_TIME)
    title = get_setting(db, MAINTENANCE_TITLE)
    message = get_setting(db, MAINTENANCE_MESSAGE)
    
    return {
        "enabled": enabled == "true" if enabled else False,
        "end_time": end_time,
        "title": title or "Under Maintenance",
        "message": message or "We're performing scheduled maintenance. We'll be back soon!"
    }

@router.put("/maintenance")
async def update_maintenance_settings(
    request: MaintenanceSettingsRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Update maintenance mode settings"""
    get_current_admin(authorization, db)
    
    set_setting(db, MAINTENANCE_ENABLED, "true" if request.enabled else "false")
    set_setting(db, MAINTENANCE_END_TIME, request.end_time.isoformat() if request.end_time else "")
    set_setting(db, MAINTENANCE_TITLE, request.title or "Under Maintenance")
    set_setting(db, MAINTENANCE_MESSAGE, request.message or "We're performing scheduled maintenance. We'll be back soon!")
    
    return {
        "message": "Maintenance settings updated successfully",
        "enabled": request.enabled,
        "end_time": request.end_time.isoformat() if request.end_time else None
    }


# ============================================================
# Products (Subscriptions & Game Tokens) Endpoints
# ============================================================

class ProductCreateRequest(BaseModel):
    product_type: str  # "subscription" or "game_token"
    category: str  # e.g., "pubg_royal_pass", "pubg_uc", etc.
    name: str
    description: Optional[str] = None
    token_price: int
    token_amount: Optional[int] = None  # For game tokens
    validity: str = "current_season"  # current_season, current_event, lifetime
    banner_url: Optional[str] = None

class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    token_price: Optional[int] = None
    token_amount: Optional[int] = None
    validity: Optional[str] = None
    banner_url: Optional[str] = None
    is_active: Optional[str] = None


@router.get("/products")
async def get_products(
    product_type: Optional[str] = None,
    status: Optional[str] = None,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get all products with optional filtering"""
    get_current_admin(authorization, db)
    
    query = db.query(Product)
    
    if product_type:
        query = query.filter(Product.product_type == product_type)
    if status:
        query = query.filter(Product.is_active == status)
        
    products = query.order_by(Product.created_at.desc()).all()
    
    return {
        "products": [p.to_dict() for p in products],
        "total": len(products)
    }


@router.post("/products")
async def create_product(
    request: ProductCreateRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Create a new product (subscription or game token)"""
    get_current_admin(authorization, db)
    
    try:
        product_type = ProductType(request.product_type)
        category = ProductCategory(request.category)
        validity = ProductValidity(request.validity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {str(e)}")
    
    product = Product(
        product_type=product_type,
        category=category,
        name=request.name,
        description=request.description,
        token_price=request.token_price,
        token_amount=request.token_amount,
        validity=validity,
        banner_url=request.banner_url,
        is_active="active"
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    return {
        "message": "Product created successfully",
        "product": product.to_dict()
    }


@router.get("/products/{product_id}")
async def get_product(
    product_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get a single product by ID"""
    get_current_admin(authorization, db)
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"product": product.to_dict()}


@router.put("/products/{product_id}")
async def update_product(
    product_id: str,
    request: ProductUpdateRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Update a product"""
    get_current_admin(authorization, db)
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if request.name is not None:
        product.name = request.name
    if request.description is not None:
        product.description = request.description
    if request.token_price is not None:
        product.token_price = request.token_price
    if request.token_amount is not None:
        product.token_amount = request.token_amount
    if request.validity is not None:
        try:
            product.validity = ProductValidity(request.validity)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid validity value")
    if request.banner_url is not None:
        product.banner_url = request.banner_url
    if request.is_active is not None:
        product.is_active = request.is_active
    
    db.commit()
    db.refresh(product)
    
    return {
        "message": "Product updated successfully",
        "product": product.to_dict()
    }


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Delete a product"""
    get_current_admin(authorization, db)
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    
    return {"message": "Product deleted successfully"}


# Product categories for frontend reference
PRODUCT_CATEGORIES = {
    "subscriptions": [
        {"value": "pubg_royal_pass", "label": "PUBG Royal Pass", "game": "PUBG Mobile"},
        {"value": "pubg_royal_pass_elite", "label": "Royal Pass Elite", "game": "PUBG Mobile"},
        {"value": "freefire_booyah_pass", "label": "Free Fire Booyah Pass", "game": "Free Fire"},
        {"value": "freefire_booyah_pass_pro", "label": "Free Fire Booyah Pass Pro", "game": "Free Fire"}
    ],
    "game_tokens": [
        {"value": "pubg_uc", "label": "PUBG UC", "game": "PUBG Mobile", "unit": "UC"},
        {"value": "freefire_diamond", "label": "Free Fire Diamond", "game": "Free Fire", "unit": "Diamond"}
    ],
    "validity_options": [
        {"value": "current_season", "label": "Current Season"},
        {"value": "current_event", "label": "Current Event"},
        {"value": "lifetime", "label": "Lifetime"}
    ]
}

@router.get("/products/categories/all")
async def get_product_categories(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get all product categories and options"""
    get_current_admin(authorization, db)
    return PRODUCT_CATEGORIES
