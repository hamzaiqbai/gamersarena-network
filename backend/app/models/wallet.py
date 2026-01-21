"""
Wallet Model - Handles user token balances
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base


class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Token balances
    virtual_tokens = Column(Integer, default=0)  # Purchased tokens
    reward_tokens = Column(Integer, default=0)   # Earned tokens from tournaments
    
    # Statistics
    total_spent_pkr = Column(Numeric(10, 2), default=0)  # Total money spent in PKR
    total_tokens_purchased = Column(Integer, default=0)  # Total tokens ever purchased
    total_tokens_earned = Column(Integer, default=0)     # Total reward tokens ever earned
    total_tokens_spent = Column(Integer, default=0)      # Total tokens spent on tournaments
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="wallet")
    
    def __repr__(self):
        return f"<Wallet user_id={self.user_id} tokens={self.total_balance}>"
    
    @property
    def total_balance(self) -> int:
        """Total available balance (virtual + reward tokens)"""
        return (self.virtual_tokens or 0) + (self.reward_tokens or 0)
    
    def has_sufficient_balance(self, amount: int) -> bool:
        """Check if wallet has enough tokens"""
        return self.total_balance >= amount
    
    def deduct_tokens(self, amount: int, use_reward_first: bool = False) -> bool:
        """
        Deduct tokens from wallet.
        By default, uses virtual tokens first, then reward tokens.
        Returns True if successful, False if insufficient balance.
        """
        if not self.has_sufficient_balance(amount):
            return False
        
        if use_reward_first:
            # Use reward tokens first
            if self.reward_tokens >= amount:
                self.reward_tokens -= amount
            else:
                remaining = amount - self.reward_tokens
                self.reward_tokens = 0
                self.virtual_tokens -= remaining
        else:
            # Use virtual tokens first
            if self.virtual_tokens >= amount:
                self.virtual_tokens -= amount
            else:
                remaining = amount - self.virtual_tokens
                self.virtual_tokens = 0
                self.reward_tokens -= remaining
        
        self.total_tokens_spent += amount
        return True
    
    def add_virtual_tokens(self, amount: int, amount_pkr: float = 0):
        """Add purchased tokens to wallet"""
        self.virtual_tokens += amount
        self.total_tokens_purchased += amount
        self.total_spent_pkr += amount_pkr
    
    def add_reward_tokens(self, amount: int):
        """Add reward tokens (from tournament wins)"""
        self.reward_tokens += amount
        self.total_tokens_earned += amount
    
    def to_dict(self) -> dict:
        """Convert wallet to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "virtual_tokens": self.virtual_tokens,
            "reward_tokens": self.reward_tokens,
            "total_balance": self.total_balance,
            "total_spent_pkr": float(self.total_spent_pkr or 0),
            "total_tokens_purchased": self.total_tokens_purchased,
            "total_tokens_earned": self.total_tokens_earned,
            "total_tokens_spent": self.total_tokens_spent
        }
