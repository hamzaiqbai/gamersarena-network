"""
Application Configuration
All settings are loaded from environment variables
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache
import os
from pathlib import Path

# Get the directory where this file is located
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "GAN - Gaming Arena Network"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ENVIRONMENT: str = "development"  # development or production
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Frontend URL (for CORS and redirects)
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,https://gamersarena.network,https://www.gamersarena.network,https://api.gamersarena.network"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/gan_db"
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"
    
    # JWT Settings
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Easypaisa Configuration
    EASYPAISA_STORE_ID: str = ""
    EASYPAISA_HASH_KEY: str = ""
    EASYPAISA_API_URL: str = "https://easypaisa.com.pk/api"
    EASYPAISA_RETURN_URL: str = ""
    
    # JazzCash Configuration
    JAZZCASH_MERCHANT_ID: str = ""
    JAZZCASH_PASSWORD: str = ""
    JAZZCASH_HASH_KEY: str = ""
    JAZZCASH_API_URL: str = "https://sandbox.jazzcash.com.pk/ApplicationAPI/API/Payment/DoTransaction"
    
    # WhatsApp Business API
    WHATSAPP_API_URL: str = "https://graph.facebook.com/v17.0"
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "gan-whatsapp-verify"
    
    # Stripe (Future)
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    class Config:
        env_file = str(BASE_DIR / ".env")
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
