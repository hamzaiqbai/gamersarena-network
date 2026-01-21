"""
Wallets Router - Balance and transactions
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.user import User
from ..models.wallet import Wallet
from ..models.transaction import Transaction, TransactionType, TransactionStatus
from ..schemas.wallet import (
    WalletResponse, 
    TokenTransferRequest, 
    TokenTransferResponse,
    TransactionResponse,
    TransactionListResponse
)
from ..utils.security import get_current_user

router = APIRouter(prefix="/api/wallets", tags=["Wallets"])


@router.get("/balance", response_model=WalletResponse)
async def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's wallet balance"""
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    
    if not wallet:
        # Create wallet if doesn't exist (shouldn't happen normally)
        wallet = Wallet(user_id=current_user.id)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    
    return wallet


@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions(
    page: int = 1,
    per_page: int = 20,
    transaction_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's transaction history"""
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    
    if transaction_type:
        query = query.filter(Transaction.type == transaction_type)
    
    total = query.count()
    
    transactions = query.order_by(Transaction.created_at.desc())\
        .offset((page - 1) * per_page)\
        .limit(per_page)\
        .all()
    
    return TransactionListResponse(
        transactions=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total
    )


@router.post("/transfer", response_model=TokenTransferResponse)
async def transfer_tokens(
    transfer_data: TokenTransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Transfer reward tokens to another user.
    Only reward tokens can be transferred, not purchased tokens.
    """
    # Find recipient
    recipient = db.query(User).filter(User.email == transfer_data.recipient_email).first()
    
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    
    if recipient.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer tokens to yourself"
        )
    
    # Get sender's wallet
    sender_wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    
    if not sender_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    # Check if only transferring reward tokens
    if transfer_data.token_type != "reward":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only reward tokens can be transferred"
        )
    
    # Check balance
    if sender_wallet.reward_tokens < transfer_data.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient reward tokens. Available: {sender_wallet.reward_tokens}"
        )
    
    # Get or create recipient's wallet
    recipient_wallet = db.query(Wallet).filter(Wallet.user_id == recipient.id).first()
    if not recipient_wallet:
        recipient_wallet = Wallet(user_id=recipient.id)
        db.add(recipient_wallet)
    
    # Record balances before transfer
    sender_balance_before = sender_wallet.total_balance
    recipient_balance_before = recipient_wallet.total_balance
    
    # Perform transfer
    sender_wallet.reward_tokens -= transfer_data.amount
    recipient_wallet.reward_tokens += transfer_data.amount
    
    # Create transactions for both parties
    sender_transaction = Transaction(
        user_id=current_user.id,
        type=TransactionType.TRANSFER_OUT.value,
        status=TransactionStatus.COMPLETED.value,
        token_amount=transfer_data.amount,
        token_type="reward",
        recipient_user_id=recipient.id,
        description=f"Transferred to {recipient.email}",
        balance_before=sender_balance_before,
        balance_after=sender_wallet.total_balance
    )
    sender_transaction.mark_completed()
    
    recipient_transaction = Transaction(
        user_id=recipient.id,
        type=TransactionType.TRANSFER_IN.value,
        status=TransactionStatus.COMPLETED.value,
        token_amount=transfer_data.amount,
        token_type="reward",
        sender_user_id=current_user.id,
        description=f"Received from {current_user.email}",
        balance_before=recipient_balance_before,
        balance_after=recipient_wallet.total_balance
    )
    recipient_transaction.mark_completed()
    
    db.add(sender_transaction)
    db.add(recipient_transaction)
    db.commit()
    
    return TokenTransferResponse(
        success=True,
        message=f"Successfully transferred {transfer_data.amount} tokens to {recipient.email}",
        transaction_id=sender_transaction.id,
        tokens_transferred=transfer_data.amount,
        new_balance=sender_wallet.total_balance,
        recipient_email=recipient.email
    )
