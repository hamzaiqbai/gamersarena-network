"""
Wallet Service - Token management
"""
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from uuid import UUID

from ..models.user import User
from ..models.wallet import Wallet
from ..models.transaction import Transaction, TransactionType, TransactionStatus


class WalletService:
    """Service for wallet and token operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_wallet(self, user_id: UUID) -> Optional[Wallet]:
        """Get user's wallet"""
        return self.db.query(Wallet).filter(Wallet.user_id == user_id).first()
    
    def get_or_create_wallet(self, user_id: UUID) -> Wallet:
        """Get existing wallet or create a new one"""
        wallet = self.get_wallet(user_id)
        if not wallet:
            wallet = Wallet(user_id=user_id)
            self.db.add(wallet)
            self.db.commit()
            self.db.refresh(wallet)
        return wallet
    
    def add_tokens(
        self,
        user_id: UUID,
        amount: int,
        token_type: str = "virtual",
        amount_pkr: float = 0,
        description: str = None,
        transaction_type: str = TransactionType.PURCHASE.value
    ) -> Tuple[Wallet, Transaction]:
        """Add tokens to user's wallet and create transaction record"""
        wallet = self.get_or_create_wallet(user_id)
        balance_before = wallet.total_balance
        
        if token_type == "virtual":
            wallet.add_virtual_tokens(amount, amount_pkr)
        else:
            wallet.add_reward_tokens(amount)
        
        transaction = Transaction(
            user_id=user_id,
            type=transaction_type,
            status=TransactionStatus.COMPLETED.value,
            token_amount=amount,
            token_type=token_type,
            amount_pkr=amount_pkr if amount_pkr else None,
            description=description,
            balance_before=balance_before,
            balance_after=wallet.total_balance
        )
        transaction.mark_completed()
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(wallet)
        self.db.refresh(transaction)
        
        return wallet, transaction
    
    def deduct_tokens(
        self,
        user_id: UUID,
        amount: int,
        description: str = None,
        transaction_type: str = TransactionType.TOURNAMENT_ENTRY.value,
        tournament_id: UUID = None
    ) -> Tuple[bool, Optional[Transaction]]:
        """Deduct tokens from user's wallet"""
        wallet = self.get_wallet(user_id)
        
        if not wallet or not wallet.has_sufficient_balance(amount):
            return False, None
        
        balance_before = wallet.total_balance
        wallet.deduct_tokens(amount)
        
        transaction = Transaction(
            user_id=user_id,
            type=transaction_type,
            status=TransactionStatus.COMPLETED.value,
            token_amount=amount,
            tournament_id=tournament_id,
            description=description,
            balance_before=balance_before,
            balance_after=wallet.total_balance
        )
        transaction.mark_completed()
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        return True, transaction
    
    def transfer_tokens(
        self,
        sender_id: UUID,
        recipient_id: UUID,
        amount: int,
        token_type: str = "reward"
    ) -> Tuple[bool, str, Optional[Transaction]]:
        """Transfer tokens between users (only reward tokens)"""
        if token_type != "reward":
            return False, "Only reward tokens can be transferred", None
        
        sender_wallet = self.get_wallet(sender_id)
        if not sender_wallet:
            return False, "Sender wallet not found", None
        
        if sender_wallet.reward_tokens < amount:
            return False, "Insufficient reward tokens", None
        
        recipient_wallet = self.get_or_create_wallet(recipient_id)
        
        # Perform transfer
        sender_balance_before = sender_wallet.total_balance
        recipient_balance_before = recipient_wallet.total_balance
        
        sender_wallet.reward_tokens -= amount
        recipient_wallet.reward_tokens += amount
        
        # Create transactions
        sender_tx = Transaction(
            user_id=sender_id,
            type=TransactionType.TRANSFER_OUT.value,
            status=TransactionStatus.COMPLETED.value,
            token_amount=amount,
            token_type="reward",
            recipient_user_id=recipient_id,
            balance_before=sender_balance_before,
            balance_after=sender_wallet.total_balance
        )
        sender_tx.mark_completed()
        
        recipient_tx = Transaction(
            user_id=recipient_id,
            type=TransactionType.TRANSFER_IN.value,
            status=TransactionStatus.COMPLETED.value,
            token_amount=amount,
            token_type="reward",
            sender_user_id=sender_id,
            balance_before=recipient_balance_before,
            balance_after=recipient_wallet.total_balance
        )
        recipient_tx.mark_completed()
        
        self.db.add(sender_tx)
        self.db.add(recipient_tx)
        self.db.commit()
        
        return True, "Transfer successful", sender_tx
    
    def get_balance(self, user_id: UUID) -> dict:
        """Get user's token balance"""
        wallet = self.get_wallet(user_id)
        if not wallet:
            return {
                "virtual_tokens": 0,
                "reward_tokens": 0,
                "total_balance": 0
            }
        
        return {
            "virtual_tokens": wallet.virtual_tokens,
            "reward_tokens": wallet.reward_tokens,
            "total_balance": wallet.total_balance
        }
