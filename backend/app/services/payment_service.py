"""
Payment Service - Mobile wallet integrations
"""
import hashlib
import hmac
import json
from datetime import datetime
from typing import Dict, Optional
import httpx

from ..config import settings


class PaymentService:
    """Service for payment processing via mobile wallets"""
    
    # ==================== EASYPAISA ====================
    
    async def initiate_easypaisa_payment(
        self,
        transaction_id: str,
        amount: float,
        mobile_number: str,
        description: str = "GAN Token Purchase"
    ) -> Dict:
        """
        Initiate an Easypaisa OTC (Over The Counter) payment.
        Sends a payment request to user's mobile.
        
        Easypaisa API Documentation:
        - Sandbox: https://easypaisa.com.pk/sandbox
        - Production: https://easypaisa.com.pk/api
        """
        # Format mobile number (remove + and country code if present)
        mobile = mobile_number.replace("+", "").replace("92", "0", 1)
        
        # Prepare request data
        payload = {
            "orderId": transaction_id,
            "storeId": settings.EASYPAISA_STORE_ID,
            "transactionAmount": str(int(amount)),  # Amount in PKR (no decimals)
            "transactionType": "OTC",  # Over The Counter
            "mobileAccountNo": mobile,
            "emailAddress": "",
            "tokenExpiry": "20260101 235959",  # Format: YYYYMMDD HHMMSS
            "merchantPaymentMethod": "",
            "postBackURL": f"{settings.FRONTEND_URL}/api/payments/easypaisa/callback"
        }
        
        # Generate hash
        hash_string = self._generate_easypaisa_hash(payload)
        payload["hashKey"] = hash_string
        
        # For development/sandbox, return mock response
        if settings.DEBUG or not settings.EASYPAISA_STORE_ID:
            return {
                "success": True,
                "external_id": f"EP-{transaction_id[:8]}",
                "message": "Payment request sent (SANDBOX MODE)"
            }
        
        # Make API request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.EASYPAISA_API_URL}/initiate",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("responseCode") == "0000":
                    return {
                        "success": True,
                        "external_id": data.get("transactionId"),
                        "message": "Payment request sent"
                    }
                else:
                    raise Exception(f"Easypaisa error: {data.get('responseDesc')}")
            else:
                raise Exception(f"Easypaisa API error: {response.status_code}")
    
    def _generate_easypaisa_hash(self, payload: Dict) -> str:
        """Generate hash for Easypaisa request"""
        hash_string = ""
        for key in sorted(payload.keys()):
            if payload[key]:
                hash_string += str(payload[key])
        
        hash_string += settings.EASYPAISA_HASH_KEY
        
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def verify_easypaisa_callback(self, data: Dict) -> bool:
        """Verify Easypaisa callback hash"""
        received_hash = data.pop("hashKey", None)
        if not received_hash:
            return False
        
        expected_hash = self._generate_easypaisa_hash(data)
        return hmac.compare_digest(received_hash, expected_hash)
    
    # ==================== JAZZCASH ====================
    
    async def initiate_jazzcash_payment(
        self,
        transaction_id: str,
        amount: float,
        mobile_number: str,
        description: str = "GAN Token Purchase"
    ) -> Dict:
        """
        Initiate a JazzCash Mobile Account payment.
        
        JazzCash API Documentation:
        https://sandbox.jazzcash.com.pk/
        """
        # Format mobile number
        mobile = mobile_number.replace("+", "").replace("92", "0", 1)
        
        # Current date/time in required format
        now = datetime.now()
        txn_datetime = now.strftime("%Y%m%d%H%M%S")
        expiry = (now.replace(hour=23, minute=59, second=59)).strftime("%Y%m%d%H%M%S")
        
        # Prepare request data
        payload = {
            "pp_Version": "1.1",
            "pp_TxnType": "MWALLET",  # Mobile Wallet
            "pp_Language": "EN",
            "pp_MerchantID": settings.JAZZCASH_MERCHANT_ID,
            "pp_Password": settings.JAZZCASH_PASSWORD,
            "pp_TxnRefNo": transaction_id,
            "pp_Amount": str(int(amount * 100)),  # Amount in paisa
            "pp_TxnCurrency": "PKR",
            "pp_TxnDateTime": txn_datetime,
            "pp_TxnExpiryDateTime": expiry,
            "pp_BillReference": "GAN",
            "pp_Description": description,
            "pp_MobileNumber": mobile,
            "pp_CNIC": "",  # Optional
            "ppmpf_1": "",
            "ppmpf_2": "",
            "ppmpf_3": "",
            "ppmpf_4": "",
            "ppmpf_5": ""
        }
        
        # Generate secure hash
        payload["pp_SecureHash"] = self._generate_jazzcash_hash(payload)
        
        # For development/sandbox, return mock response
        if settings.DEBUG or not settings.JAZZCASH_MERCHANT_ID:
            return {
                "success": True,
                "external_id": f"JC-{transaction_id[:8]}",
                "message": "Payment request sent (SANDBOX MODE)"
            }
        
        # Make API request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.JAZZCASH_API_URL,
                data=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("pp_ResponseCode") == "000":
                    return {
                        "success": True,
                        "external_id": data.get("pp_TxnRefNo"),
                        "message": "Payment request sent"
                    }
                else:
                    raise Exception(f"JazzCash error: {data.get('pp_ResponseMessage')}")
            else:
                raise Exception(f"JazzCash API error: {response.status_code}")
    
    def _generate_jazzcash_hash(self, payload: Dict) -> str:
        """Generate HMAC-SHA256 hash for JazzCash"""
        # Sort and concatenate values
        sorted_keys = [
            "pp_Amount", "pp_BillReference", "pp_CNIC", "pp_Description",
            "pp_Language", "pp_MerchantID", "pp_MobileNumber", "pp_Password",
            "pp_TxnCurrency", "pp_TxnDateTime", "pp_TxnExpiryDateTime",
            "pp_TxnRefNo", "pp_TxnType", "pp_Version",
            "ppmpf_1", "ppmpf_2", "ppmpf_3", "ppmpf_4", "ppmpf_5"
        ]
        
        hash_string = settings.JAZZCASH_HASH_KEY
        for key in sorted_keys:
            if key in payload and payload[key]:
                hash_string += "&" + str(payload[key])
        
        return hmac.new(
            settings.JAZZCASH_HASH_KEY.encode(),
            hash_string.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_jazzcash_callback(self, data: Dict) -> bool:
        """Verify JazzCash callback hash"""
        received_hash = data.get("pp_SecureHash")
        if not received_hash:
            return False
        
        expected_hash = self._generate_jazzcash_hash(data)
        return hmac.compare_digest(received_hash.lower(), expected_hash.lower())
    
    # ==================== UTILITIES ====================
    
    @staticmethod
    def format_amount_display(amount_pkr: float) -> str:
        """Format amount for display"""
        return f"Rs. {amount_pkr:,.0f}"
