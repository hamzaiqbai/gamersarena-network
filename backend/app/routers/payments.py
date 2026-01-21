"""
Payments Router - Token purchase via mobile wallets
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import hashlib
import hmac
import json

from ..database import get_db
from ..config import settings
from ..models.user import User
from ..models.wallet import Wallet
from ..models.tournament import TokenBundle
from ..models.transaction import Transaction, TransactionType, TransactionStatus, PaymentMethod
from ..schemas.payment import (
    TokenBundleResponse,
    TokenBundleListResponse,
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    PaymentStatusResponse,
    EasypaisaCallbackData,
    JazzCashCallbackData,
    PaymentReceiptResponse
)
from ..services.payment_service import PaymentService
from ..utils.security import get_current_user

router = APIRouter(prefix="/api/payments", tags=["Payments"])


@router.get("/bundles", response_model=TokenBundleListResponse)
async def get_token_bundles(
    db: Session = Depends(get_db)
):
    """Get available token bundles for purchase"""
    bundles = db.query(TokenBundle)\
        .filter(TokenBundle.is_active == True)\
        .order_by(TokenBundle.sort_order.asc())\
        .all()
    
    return TokenBundleListResponse(
        bundles=[TokenBundleResponse.model_validate(b.to_dict()) for b in bundles]
    )


@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    payment_data: PaymentInitiateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initiate a token purchase.
    For mobile wallets, sends a payment request to user's phone.
    """
    # Get bundle
    bundle = db.query(TokenBundle).filter(TokenBundle.id == payment_data.bundle_id).first()
    
    if not bundle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token bundle not found"
        )
    
    if not bundle.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This bundle is no longer available"
        )
    
    # Get mobile number
    mobile_number = payment_data.mobile_number or current_user.mobile_wallet_number
    
    if payment_data.payment_method in ["easypaisa", "jazzcash"] and not mobile_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mobile number is required for mobile wallet payments"
        )
    
    # Get wallet
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    
    # Create pending transaction
    transaction = Transaction(
        user_id=current_user.id,
        type=TransactionType.PURCHASE.value,
        status=TransactionStatus.PENDING.value,
        token_amount=bundle.total_tokens,
        token_type="virtual",
        payment_method=payment_data.payment_method,
        amount_pkr=bundle.price_pkr,
        amount_usd=bundle.price_usd,
        bundle_id=bundle.id,
        description=f"Purchase: {bundle.name}",
        balance_before=wallet.total_balance if wallet else 0
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    # Initiate payment with provider
    payment_service = PaymentService()
    
    try:
        if payment_data.payment_method == "easypaisa":
            result = await payment_service.initiate_easypaisa_payment(
                transaction_id=str(transaction.id),
                amount=float(bundle.price_pkr),
                mobile_number=mobile_number,
                description=f"GAN - {bundle.name}"
            )
        elif payment_data.payment_method == "jazzcash":
            result = await payment_service.initiate_jazzcash_payment(
                transaction_id=str(transaction.id),
                amount=float(bundle.price_pkr),
                mobile_number=mobile_number,
                description=f"GAN - {bundle.name}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported payment method"
            )
        
        # Update transaction with external reference
        transaction.external_transaction_id = result.get("external_id")
        transaction.status = TransactionStatus.PROCESSING.value
        db.commit()
        
        return PaymentInitiateResponse(
            success=True,
            message="Payment request sent to your mobile wallet",
            transaction_id=transaction.id,
            payment_method=payment_data.payment_method,
            amount_pkr=float(bundle.price_pkr),
            tokens=bundle.total_tokens,
            mobile_number=mobile_number,
            payment_request_sent=True,
            status="processing"
        )
        
    except Exception as e:
        # Mark transaction as failed
        transaction.status = TransactionStatus.FAILED.value
        transaction.notes = str(e)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate payment: {str(e)}"
        )


@router.get("/status/{transaction_id}", response_model=PaymentStatusResponse)
async def check_payment_status(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check the status of a payment"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return PaymentStatusResponse(
        transaction_id=transaction.id,
        status=transaction.status,
        payment_method=transaction.payment_method,
        amount_pkr=float(transaction.amount_pkr) if transaction.amount_pkr else 0,
        tokens=transaction.token_amount,
        completed_at=transaction.completed_at
    )


@router.post("/easypaisa/callback")
async def easypaisa_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Easypaisa payment callback webhook.
    Called by Easypaisa when payment is completed.
    """
    try:
        data = await request.json()
        callback_data = EasypaisaCallbackData(**data)
        
        # Verify hash (implement based on Easypaisa docs)
        # payment_service = PaymentService()
        # if not payment_service.verify_easypaisa_hash(data):
        #     raise HTTPException(status_code=400, detail="Invalid hash")
        
        # Find transaction
        transaction = db.query(Transaction).filter(
            Transaction.id == callback_data.orderId
        ).first()
        
        if not transaction:
            return {"status": "error", "message": "Transaction not found"}
        
        if callback_data.transactionStatus == "0000":
            # Payment successful
            transaction.status = TransactionStatus.COMPLETED.value
            transaction.payment_reference = callback_data.transactionId
            transaction.completed_at = datetime.utcnow()
            
            # Credit tokens to wallet
            wallet = db.query(Wallet).filter(
                Wallet.user_id == transaction.user_id
            ).first()
            
            if wallet:
                wallet.add_virtual_tokens(
                    transaction.token_amount,
                    float(transaction.amount_pkr or 0)
                )
                transaction.balance_after = wallet.total_balance
            
            db.commit()
            return {"status": "success"}
        else:
            # Payment failed
            transaction.status = TransactionStatus.FAILED.value
            transaction.notes = f"Easypaisa status: {callback_data.transactionStatus}"
            db.commit()
            return {"status": "failed"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/jazzcash/callback")
async def jazzcash_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    JazzCash payment callback webhook.
    Called by JazzCash when payment is completed.
    """
    try:
        data = await request.form()
        callback_data = JazzCashCallbackData(**dict(data))
        
        # Find transaction
        transaction = db.query(Transaction).filter(
            Transaction.id == callback_data.pp_TxnRefNo
        ).first()
        
        if not transaction:
            return {"status": "error", "message": "Transaction not found"}
        
        if callback_data.pp_ResponseCode == "000":
            # Payment successful
            transaction.status = TransactionStatus.COMPLETED.value
            transaction.payment_reference = callback_data.pp_TxnRefNo
            transaction.completed_at = datetime.utcnow()
            
            # Credit tokens to wallet
            wallet = db.query(Wallet).filter(
                Wallet.user_id == transaction.user_id
            ).first()
            
            if wallet:
                wallet.add_virtual_tokens(
                    transaction.token_amount,
                    float(transaction.amount_pkr or 0)
                )
                transaction.balance_after = wallet.total_balance
            
            db.commit()
            return {"status": "success"}
        else:
            # Payment failed
            transaction.status = TransactionStatus.FAILED.value
            transaction.notes = f"JazzCash: {callback_data.pp_ResponseMessage}"
            db.commit()
            return {"status": "failed"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/receipt/{transaction_id}", response_model=PaymentReceiptResponse)
async def get_receipt(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get payment receipt for a completed transaction"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
        Transaction.type == TransactionType.PURCHASE.value
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Get bundle info
    bundle = db.query(TokenBundle).filter(
        TokenBundle.id == transaction.bundle_id
    ).first()
    
    wallet = db.query(Wallet).filter(
        Wallet.user_id == current_user.id
    ).first()
    
    return PaymentReceiptResponse(
        transaction_id=transaction.id,
        payment_method=transaction.payment_method,
        amount_pkr=float(transaction.amount_pkr) if transaction.amount_pkr else 0,
        tokens_purchased=bundle.tokens if bundle else transaction.token_amount,
        bonus_tokens=bundle.bonus_tokens if bundle else 0,
        total_tokens=transaction.token_amount,
        payment_reference=transaction.payment_reference,
        status=transaction.status,
        purchased_at=transaction.completed_at or transaction.created_at,
        new_balance=wallet.total_balance if wallet else 0
    )
