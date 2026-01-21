"""
Authentication Service
"""
from datetime import datetime, timedelta
from typing import Optional
import jwt
from sqlalchemy.orm import Session

from ..config import settings
from ..models.user import User
from ..models.wallet import Wallet


class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    def create_user_from_google(
        db: Session,
        google_id: str,
        email: str,
        full_name: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> User:
        """Create a new user from Google OAuth data"""
        user = User(
            google_id=google_id,
            email=email,
            full_name=full_name,
            avatar_url=avatar_url,
            profile_completed=False
        )
        db.add(user)
        db.flush()
        
        # Create wallet for user
        wallet = Wallet(user_id=user.id)
        db.add(wallet)
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def get_user_by_google_id(db: Session, google_id: str) -> Optional[User]:
        """Get user by Google ID"""
        return db.query(User).filter(User.google_id == google_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def update_last_login(db: Session, user: User) -> None:
        """Update user's last login timestamp"""
        user.last_login = datetime.utcnow()
        db.commit()
