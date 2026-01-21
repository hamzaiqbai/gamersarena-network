"""
Registration Model - Tournament registrations
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base
import enum


class RegistrationStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    CHECKED_IN = "checked_in"
    NO_SHOW = "no_show"
    DISQUALIFIED = "disqualified"


class Registration(Base):
    __tablename__ = "registrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Registration details
    status = Column(String(20), default=RegistrationStatus.CONFIRMED.value)
    tokens_paid = Column(Integer, nullable=False)  # Entry fee paid
    transaction_id = Column(UUID(as_uuid=True), nullable=True)  # Link to transaction
    
    # Game details
    player_id = Column(String(100), nullable=True)  # Player's in-game ID
    team_name = Column(String(100), nullable=True)  # For team tournaments
    
    # Results
    position = Column(Integer, nullable=True)  # Final position (1st, 2nd, etc.)
    reward_earned = Column(Integer, default=0)  # Tokens won
    reward_transaction_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Statistics
    kills = Column(Integer, nullable=True)
    score = Column(Integer, nullable=True)
    
    # Check-in
    checked_in = Column(Boolean, default=False)
    checked_in_at = Column(DateTime, nullable=True)
    
    # Timestamps
    registered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="registrations")
    tournament = relationship("Tournament", back_populates="registrations")
    
    def __repr__(self):
        return f"<Registration user={self.user_id} tournament={self.tournament_id}>"
    
    def check_in(self):
        """Mark player as checked in"""
        self.checked_in = True
        self.checked_in_at = datetime.utcnow()
        self.status = RegistrationStatus.CHECKED_IN.value
    
    def set_result(self, position: int, reward: int = 0):
        """Set tournament result"""
        self.position = position
        self.reward_earned = reward
    
    def to_dict(self, include_tournament: bool = False, include_user: bool = False) -> dict:
        """Convert registration to dictionary"""
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "tournament_id": str(self.tournament_id),
            "status": self.status,
            "tokens_paid": self.tokens_paid,
            "player_id": self.player_id,
            "team_name": self.team_name,
            "position": self.position,
            "reward_earned": self.reward_earned,
            "checked_in": self.checked_in,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None
        }
        
        if include_tournament and self.tournament:
            data["tournament"] = self.tournament.to_dict()
        
        if include_user and self.user:
            data["user"] = {
                "id": str(self.user.id),
                "full_name": self.user.full_name,
                "player_id": self.user.player_id,
                "avatar_url": self.user.avatar_url
            }
        
        return data
