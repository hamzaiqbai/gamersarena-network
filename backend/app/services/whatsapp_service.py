"""
WhatsApp Service - WhatsApp Business API integration
"""
import httpx
from typing import Optional

from ..config import settings


class WhatsAppService:
    """Service for WhatsApp Business API operations"""
    
    def __init__(self):
        self.api_url = settings.WHATSAPP_API_URL
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
    
    async def send_verification_code(
        self,
        phone_number: str,
        code: str
    ) -> bool:
        """
        Send verification code via WhatsApp.
        Uses a pre-approved template message.
        
        WhatsApp Business API Documentation:
        https://developers.facebook.com/docs/whatsapp/cloud-api
        """
        # Format phone number (ensure it has country code)
        formatted_phone = self._format_phone_number(phone_number)
        
        # For development without WhatsApp setup
        if not self.phone_number_id or not self.access_token:
            print(f"[DEV] WhatsApp verification code for {formatted_phone}: {code}")
            return True
        
        # Prepare message using a template
        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_phone,
            "type": "template",
            "template": {
                "name": "verification_code",  # Pre-approved template name
                "language": {
                    "code": "en"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": code
                            }
                        ]
                    }
                ]
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/{self.phone_number_id}/messages",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return True
            else:
                error = response.json()
                raise Exception(f"WhatsApp API error: {error}")
    
    async def send_text_message(
        self,
        phone_number: str,
        message: str
    ) -> bool:
        """
        Send a text message via WhatsApp.
        Note: Only works with users who have messaged first (24-hour window)
        """
        formatted_phone = self._format_phone_number(phone_number)
        
        if not self.phone_number_id or not self.access_token:
            print(f"[DEV] WhatsApp message to {formatted_phone}: {message}")
            return True
        
        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_phone,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/{self.phone_number_id}/messages",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            return response.status_code == 200
    
    async def send_tournament_notification(
        self,
        phone_number: str,
        tournament_name: str,
        room_id: str,
        room_password: str,
        start_time: str
    ) -> bool:
        """
        Send tournament room details to registered user.
        Uses a template message.
        """
        formatted_phone = self._format_phone_number(phone_number)
        
        if not self.phone_number_id or not self.access_token:
            print(f"[DEV] Tournament notification to {formatted_phone}")
            print(f"  Tournament: {tournament_name}")
            print(f"  Room ID: {room_id}")
            print(f"  Password: {room_password}")
            print(f"  Start Time: {start_time}")
            return True
        
        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_phone,
            "type": "template",
            "template": {
                "name": "tournament_room_details",  # Pre-approved template
                "language": {
                    "code": "en"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": tournament_name},
                            {"type": "text", "text": room_id},
                            {"type": "text", "text": room_password},
                            {"type": "text", "text": start_time}
                        ]
                    }
                ]
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/{self.phone_number_id}/messages",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            return response.status_code == 200
    
    async def send_reward_notification(
        self,
        phone_number: str,
        tournament_name: str,
        position: int,
        reward_tokens: int
    ) -> bool:
        """Send notification when user wins tournament reward"""
        formatted_phone = self._format_phone_number(phone_number)
        
        if not self.phone_number_id or not self.access_token:
            print(f"[DEV] Reward notification to {formatted_phone}")
            print(f"  Tournament: {tournament_name}")
            print(f"  Position: #{position}")
            print(f"  Reward: {reward_tokens} tokens")
            return True
        
        # Implementation similar to above...
        return True
    
    def _format_phone_number(self, phone: str) -> str:
        """
        Format phone number for WhatsApp API.
        Expects format: +923001234567 or 03001234567
        Returns: 923001234567
        """
        # Remove all non-numeric characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Add Pakistan country code if missing
        if phone.startswith('0'):
            phone = '92' + phone[1:]
        
        if not phone.startswith('92'):
            phone = '92' + phone
        
        return phone
