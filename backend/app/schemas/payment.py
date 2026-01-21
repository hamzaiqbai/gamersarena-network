"""
Payment Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class TokenBundleResponse(BaseModel):
    """Token bundle response"""
    id: UUID
    name: str
    tokens: int
    bonus_tokens: int = 0
    total_tokens: int
    price_pkr: float
    price_usd: float
    description: Optional[str] = None
    badge: Optional[str] = None
    icon: Optional[str] = None
    is_featured: bool = False
    
    class Config:
        from_attributes = True


class TokenBundleListResponse(BaseModel):
    """List of available token bundles"""
    bundles: List[TokenBundleResponse]


class PaymentInitiateRequest(BaseModel):
    """Request to initiate a payment"""
    bundle_id: UUID
    payment_method: str = Field(..., pattern=r'^(easypaisa|jazzcash|stripe)$')
    mobile_number: Optional[str] = Field(None, pattern=r'^\+?[0-9]{10,15}$', 
                                          description="Required for mobile wallet payments")


class PaymentInitiateResponse(BaseModel):
    """Response after initiating payment"""
    success: bool
    message: str
    transaction_id: UUID
    payment_method: str
    amount_pkr: float
    tokens: int
    
    # For mobile wallet
    mobile_number: Optional[str] = None
    payment_request_sent: bool = False
    
    # For redirect-based payments (Stripe)
    redirect_url: Optional[str] = None
    
    # Status
    status: str = "pending"


class PaymentStatusRequest(BaseModel):
    """Request to check payment status"""
    transaction_id: UUID


class PaymentStatusResponse(BaseModel):
    """Payment status response"""
    transaction_id: UUID
    status: str
    payment_method: str
    amount_pkr: float
    tokens: int
    message: Optional[str] = None
    completed_at: Optional[datetime] = None


class EasypaisaCallbackData(BaseModel):
    """Easypaisa payment callback data"""
    orderId: str
    transactionId: str
    storeId: str
    transactionAmount: str
    transactionStatus: str  # 0000 = success
    paymentToken: Optional[str] = None
    transactionDateTime: Optional[str] = None
    msisdn: Optional[str] = None  # Customer mobile number
    hashKey: Optional[str] = None


class JazzCashCallbackData(BaseModel):
    """JazzCash payment callback data"""
    pp_TxnRefNo: str
    pp_Amount: str
    pp_ResponseCode: str  # 000 = success
    pp_ResponseMessage: str
    pp_TxnDateTime: Optional[str] = None
    pp_BillReference: Optional[str] = None
    pp_SecureHash: Optional[str] = None
    pp_MobileNumber: Optional[str] = None


class PaymentReceiptResponse(BaseModel):
    """Payment receipt"""
    transaction_id: UUID
    payment_method: str
    amount_pkr: float
    tokens_purchased: int
    bonus_tokens: int
    total_tokens: int
    payment_reference: Optional[str] = None
    status: str
    purchased_at: datetime
    new_balance: int
