"""
Site Settings Model - For maintenance mode and other site-wide settings
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class SiteSettings(Base):
    """Site-wide settings including maintenance mode"""
    __tablename__ = "site_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Setting key-value
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    
    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SiteSettings {self.key}={self.value}>"


# Default settings keys
MAINTENANCE_ENABLED = "maintenance_enabled"
MAINTENANCE_END_TIME = "maintenance_end_time"
MAINTENANCE_MESSAGE = "maintenance_message"
MAINTENANCE_TITLE = "maintenance_title"
