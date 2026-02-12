import uuid
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import enum

from app.database import Base


class ProductType(str, enum.Enum):
    SUBSCRIPTION = "subscription"
    GAME_TOKEN = "game_token"


class ProductCategory(str, enum.Enum):
    # Subscriptions
    PUBG_ROYAL_PASS = "pubg_royal_pass"
    PUBG_ROYAL_PASS_ELITE = "pubg_royal_pass_elite"
    FREEFIRE_BOOYAH_PASS = "freefire_booyah_pass"
    FREEFIRE_BOOYAH_PASS_PRO = "freefire_booyah_pass_pro"
    # Game Tokens
    PUBG_UC = "pubg_uc"
    FREEFIRE_DIAMOND = "freefire_diamond"


class ProductValidity(str, enum.Enum):
    CURRENT_SEASON = "current_season"
    CURRENT_EVENT = "current_event"
    LIFETIME = "lifetime"


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_type = Column(Enum(ProductType), nullable=False)
    category = Column(Enum(ProductCategory), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # For subscriptions: price in tokens
    # For game tokens: price per unit in tokens
    token_price = Column(Integer, nullable=False, default=0)
    
    # For game tokens: amount of UC/Diamonds
    token_amount = Column(Integer, nullable=True)
    
    validity = Column(Enum(ProductValidity), nullable=False, default=ProductValidity.CURRENT_SEASON)
    banner_url = Column(String(500), nullable=True)
    
    # Status
    is_active = Column(String(20), default="active")  # active, inactive
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "product_type": self.product_type.value,
            "category": self.category.value,
            "name": self.name,
            "description": self.description,
            "token_price": self.token_price,
            "token_amount": self.token_amount,
            "validity": self.validity.value,
            "banner_url": self.banner_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
