"""WhatsApp Models"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class MessageDirection(str, enum.Enum):
    """Message direction"""
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"


class MessageStatus(str, enum.Enum):
    """Message status"""
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    FAILED = "FAILED"


class MessageType(str, enum.Enum):
    """Message type"""
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"
    TEMPLATE = "TEMPLATE"
    INTERACTIVE = "INTERACTIVE"


class WhatsAppMessage(Base):
    """WhatsApp message model"""
    
    __tablename__ = "whatsapp_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String(255), unique=True, nullable=False, index=True)  # WhatsApp message ID
    direction = Column(SQLEnum(MessageDirection), nullable=False)
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.PENDING, nullable=False)
    message_type = Column(SQLEnum(MessageType), default=MessageType.TEXT, nullable=False)
    
    # Sender/Receiver info
    phone_number = Column(String(50), nullable=False, index=True)  # Customer phone number
    display_name = Column(String(255), nullable=True)
    
    # Message content
    content = Column(Text, nullable=True)  # Text content
    media_url = Column(String(500), nullable=True)  # URL for media files
    template_name = Column(String(255), nullable=True)  # If using template
    
    # Additional data
    extra_data = Column(JSON, nullable=True)  # Additional data
    
    # Timestamps
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", backref="whatsapp_messages")
    
    def __repr__(self):
        return f"<WhatsAppMessage(id={self.id}, message_id={self.message_id}, direction={self.direction})>"


class WhatsAppTemplate(Base):
    """WhatsApp message template model"""
    
    __tablename__ = "whatsapp_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=True)  # MARKETING, UTILITY, AUTHENTICATION
    language = Column(String(10), default="en", nullable=False)
    
    # Template structure
    components = Column(JSON, nullable=True)  # Header, body, footer, buttons
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_approved = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", backref="whatsapp_templates")
    
    def __repr__(self):
        return f"<WhatsAppTemplate(id={self.id}, name={self.name}, category={self.category})>"


class WebhookEvent(Base):
    """Webhook event log model"""
    
    __tablename__ = "webhook_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)  # message, message_status, etc.
    
    # Event data
    payload = Column(JSON, nullable=False)
    
    # Processing status
    processed = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    company = relationship("Company", backref="webhook_events")
    
    def __repr__(self):
        return f"<WebhookEvent(id={self.id}, event_type={self.event_type}, processed={self.processed})>"
