"""
User Model
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Google OAuth fields
    google_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Profile fields
    full_name = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    
    # WhatsApp verification
    whatsapp_number = Column(String(20), nullable=True)
    whatsapp_verified = Column(Boolean, default=False)
    whatsapp_verification_code = Column(String(6), nullable=True)
    whatsapp_code_expires_at = Column(DateTime, nullable=True)
    
    # Gaming profile
    player_id = Column(String(100), nullable=True)  # FreeFire/PUBG ID
    preferred_game = Column(String(50), nullable=True)  # freefire, pubg, etc.
    
    # Payment preferences
    preferred_payment = Column(String(50), default="easypaisa")  # easypaisa, jazzcash, stripe
    mobile_wallet_number = Column(String(20), nullable=True)
    
    # Status
    profile_completed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    wallet = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    registrations = relationship("Registration", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    @property
    def is_profile_complete(self) -> bool:
        """Check if all required profile fields are filled"""
        required_fields = [
            self.full_name,
            self.age,
            self.city,
            self.country,
            self.whatsapp_number,
            self.whatsapp_verified,
            self.player_id
        ]
        return all(required_fields)
    
    def to_dict(self) -> dict:
        """Convert user to dictionary"""
        return {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "age": self.age,
            "city": self.city,
            "country": self.country,
            "whatsapp_number": self.whatsapp_number,
            "whatsapp_verified": self.whatsapp_verified,
            "player_id": self.player_id,
            "preferred_game": self.preferred_game,
            "preferred_payment": self.preferred_payment,
            "profile_completed": self.profile_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
