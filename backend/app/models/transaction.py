"""
Transaction Model - Records all token movements
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base
import enum


class TransactionType(str, enum.Enum):
    PURCHASE = "purchase"          # Bought tokens with real money
    TOURNAMENT_ENTRY = "tournament_entry"  # Spent tokens on tournament
    TOURNAMENT_REWARD = "tournament_reward"  # Won tokens from tournament
    TRANSFER_OUT = "transfer_out"  # Sent tokens to another user
    TRANSFER_IN = "transfer_in"    # Received tokens from another user
    REFUND = "refund"              # Refunded tokens
    BONUS = "bonus"                # Bonus tokens (promotions, etc.)
    SUBSCRIPTION = "subscription"  # Used for app subscription


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, enum.Enum):
    EASYPAISA = "easypaisa"
    JAZZCASH = "jazzcash"
    STRIPE = "stripe"
    INTERNAL = "internal"  # For transfers, rewards, etc.


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Transaction details
    type = Column(String(30), nullable=False)  # purchase, tournament_entry, etc.
    status = Column(String(20), default=TransactionStatus.PENDING.value)
    
    # Token amounts
    token_amount = Column(Integer, nullable=False)  # Number of tokens
    token_type = Column(String(20), default="virtual")  # virtual or reward
    
    # Payment details (for purchases)
    payment_method = Column(String(20), nullable=True)  # easypaisa, jazzcash, stripe
    amount_pkr = Column(Numeric(10, 2), nullable=True)  # Amount in PKR
    amount_usd = Column(Numeric(10, 2), nullable=True)  # Amount in USD
    
    # External references
    payment_reference = Column(String(255), nullable=True)  # Payment gateway reference
    external_transaction_id = Column(String(255), nullable=True, index=True)
    
    # For tournament-related transactions
    tournament_id = Column(UUID(as_uuid=True), nullable=True)
    
    # For transfers
    recipient_user_id = Column(UUID(as_uuid=True), nullable=True)
    sender_user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # For bundles
    bundle_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Additional info
    description = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)  # Admin notes
    extra_data = Column(Text, nullable=True)  # JSON string for additional data
    
    # Wallet snapshot (for audit)
    balance_before = Column(Integer, nullable=True)
    balance_after = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction {self.type} - {self.token_amount} tokens>"
    
    def mark_completed(self):
        """Mark transaction as completed"""
        self.status = TransactionStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
    
    def mark_failed(self, reason: str = None):
        """Mark transaction as failed"""
        self.status = TransactionStatus.FAILED.value
        if reason:
            self.notes = reason
    
    def to_dict(self) -> dict:
        """Convert transaction to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "type": self.type,
            "status": self.status,
            "token_amount": self.token_amount,
            "token_type": self.token_type,
            "payment_method": self.payment_method,
            "amount_pkr": float(self.amount_pkr) if self.amount_pkr else None,
            "amount_usd": float(self.amount_usd) if self.amount_usd else None,
            "payment_reference": self.payment_reference,
            "tournament_id": str(self.tournament_id) if self.tournament_id else None,
            "description": self.description,
            "balance_before": self.balance_before,
            "balance_after": self.balance_after,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
