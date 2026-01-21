"""
Wallet Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class WalletResponse(BaseModel):
    """Wallet balance response"""
    id: UUID
    user_id: UUID
    virtual_tokens: int = 0
    reward_tokens: int = 0
    total_balance: int = 0
    total_spent_pkr: float = 0
    total_tokens_purchased: int = 0
    total_tokens_earned: int = 0
    total_tokens_spent: int = 0
    
    class Config:
        from_attributes = True


class TokenTransferRequest(BaseModel):
    """Request to transfer tokens to another user"""
    recipient_email: str = Field(..., description="Email of recipient user")
    amount: int = Field(..., ge=1, description="Number of tokens to transfer")
    token_type: str = Field(default="reward", pattern=r'^(virtual|reward)$', 
                            description="Type of tokens to transfer (only reward tokens can be transferred)")
    message: Optional[str] = Field(None, max_length=200, description="Optional message to recipient")


class TokenTransferResponse(BaseModel):
    """Response after token transfer"""
    success: bool
    message: str
    transaction_id: Optional[UUID] = None
    tokens_transferred: int
    new_balance: int
    recipient_email: str


class TransactionResponse(BaseModel):
    """Transaction history item"""
    id: UUID
    type: str
    status: str
    token_amount: int
    token_type: str
    payment_method: Optional[str] = None
    amount_pkr: Optional[float] = None
    description: Optional[str] = None
    balance_before: Optional[int] = None
    balance_after: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """List of transactions with pagination"""
    transactions: List[TransactionResponse]
    total: int
    page: int
    per_page: int
    has_more: bool
