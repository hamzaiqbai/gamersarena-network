"""
Tournament and Token Bundle Models
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Numeric, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base
import enum


class TournamentStatus(str, enum.Enum):
    DRAFT = "draft"
    UPCOMING = "upcoming"
    REGISTRATION_OPEN = "registration_open"
    REGISTRATION_CLOSED = "registration_closed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class GameType(str, enum.Enum):
    FREEFIRE = "freefire"
    PUBG = "pubg"
    COUNTER_STRIKE = "counter_strike"
    VALORANT = "valorant"
    COD_MOBILE = "cod_mobile"
    FORTNITE = "fortnite"
    OTHER = "other"


class Tournament(Base):
    __tablename__ = "tournaments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic info
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    game = Column(String(50), nullable=False)  # freefire, pubg, etc.
    description = Column(Text, nullable=True)
    rules = Column(Text, nullable=True)
    
    # Entry and prizes
    entry_fee = Column(Integer, default=0)  # Tokens required to join
    prize_pool = Column(Integer, default=0)  # Total reward tokens
    first_place_reward = Column(Integer, default=0)
    second_place_reward = Column(Integer, default=0)
    third_place_reward = Column(Integer, default=0)
    fourth_place_reward = Column(Integer, default=0)
    fifth_place_reward = Column(Integer, default=0)
    
    # Participants
    max_participants = Column(Integer, default=100)
    min_participants = Column(Integer, default=2)
    current_participants = Column(Integer, default=0)
    
    # Schedule
    registration_start = Column(DateTime, nullable=True)
    registration_end = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(30), default=TournamentStatus.DRAFT.value)
    
    # Media
    banner_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    
    # Room details (for games)
    room_id = Column(String(100), nullable=True)
    room_password = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    registrations = relationship("Registration", back_populates="tournament", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tournament {self.title}>"
    
    @property
    def is_registration_open(self) -> bool:
        """Check if registration is currently open"""
        now = datetime.utcnow()
        if self.status != TournamentStatus.REGISTRATION_OPEN.value:
            return False
        if self.registration_start and now < self.registration_start:
            return False
        if self.registration_end and now > self.registration_end:
            return False
        if self.current_participants >= self.max_participants:
            return False
        return True
    
    @property
    def slots_available(self) -> int:
        """Number of remaining slots"""
        return max(0, self.max_participants - self.current_participants)
    
    def to_dict(self, include_room_info: bool = False) -> dict:
        """Convert tournament to dictionary"""
        data = {
            "id": str(self.id),
            "title": self.title,
            "slug": self.slug,
            "game": self.game,
            "description": self.description,
            "rules": self.rules,
            "entry_fee": self.entry_fee,
            "prize_pool": self.prize_pool,
            "first_place_reward": self.first_place_reward,
            "second_place_reward": self.second_place_reward,
            "third_place_reward": self.third_place_reward,
            "fourth_place_reward": self.fourth_place_reward,
            "fifth_place_reward": self.fifth_place_reward,
            "max_participants": self.max_participants,
            "current_participants": self.current_participants,
            "slots_available": self.slots_available,
            "registration_start": self.registration_start.isoformat() if self.registration_start else None,
            "registration_end": self.registration_end.isoformat() if self.registration_end else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
            "is_registration_open": self.is_registration_open,
            "banner_url": self.banner_url,
            "thumbnail_url": self.thumbnail_url,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
        if include_room_info:
            data["room_id"] = self.room_id
            data["room_password"] = self.room_password
        
        return data


class TokenBundle(Base):
    """Token packages available for purchase"""
    __tablename__ = "token_bundles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Bundle details
    name = Column(String(100), nullable=False)  # e.g., "Starter Pack"
    tokens = Column(Integer, nullable=False)  # Number of tokens
    bonus_tokens = Column(Integer, default=0)  # Extra tokens
    
    # Pricing
    price_pkr = Column(Numeric(10, 2), nullable=False)  # Price in Pakistani Rupees
    price_usd = Column(Numeric(10, 2), nullable=False)  # Price in USD
    
    # Display
    description = Column(String(255), nullable=True)
    badge = Column(String(50), nullable=True)  # e.g., "BEST VALUE", "POPULAR"
    icon = Column(String(100), nullable=True)
    sort_order = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<TokenBundle {self.name} - {self.tokens} tokens>"
    
    @property
    def total_tokens(self) -> int:
        """Total tokens including bonus"""
        return self.tokens + (self.bonus_tokens or 0)
    
    def to_dict(self) -> dict:
        """Convert bundle to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "tokens": self.tokens,
            "bonus_tokens": self.bonus_tokens,
            "total_tokens": self.total_tokens,
            "price_pkr": float(self.price_pkr),
            "price_usd": float(self.price_usd),
            "description": self.description,
            "badge": self.badge,
            "icon": self.icon,
            "is_featured": self.is_featured
        }
