"""Notification Models"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class NotificationType(str, enum.Enum):
    """Notification type enum"""
    NEW_CONVERSATION = "NEW_CONVERSATION"
    MENTION = "MENTION"
    RESERVATION = "RESERVATION"
    PAYMENT = "PAYMENT"
    SYSTEM = "SYSTEM"
    ALERT = "ALERT"


class NotificationChannel(str, enum.Enum):
    """Notification channel enum"""
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"


class Notification(Base):
    """Notification model for internal notifications"""
    
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    notification_type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(String(2000), nullable=False)
    
    # Additional data (JSONB)
    data = Column(JSON, nullable=True)
    
    # Read status
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", backref="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.notification_type}, title={self.title})>"


class NotificationPreference(Base):
    """Notification preference model for user notification settings"""
    
    __tablename__ = "notification_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    
    # Channel preferences
    channel = Column(SQLEnum(NotificationChannel), default=NotificationChannel.IN_APP, nullable=False)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", backref="notification_preferences")
    
    def __repr__(self):
        return f"<NotificationPreference(id={self.id}, type={self.notification_type}, enabled={self.enabled})>"
