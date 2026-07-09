"""Channel Models"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ChannelType(str, enum.Enum):
    """Channel type"""
    WHATSAPP = "WHATSAPP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    INSTAGRAM = "INSTAGRAM"
    MESSENGER = "MESSENGER"
    TELEGRAM = "TELEGRAM"


class ChannelStatus(str, enum.Enum):
    """Channel status"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"
    FAILED = "FAILED"


class Channel(Base):
    """Channel model"""
    
    __tablename__ = "channels"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_type = Column(SQLEnum(ChannelType), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(SQLEnum(ChannelStatus), default=ChannelStatus.PENDING, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", backref="channels")
    configurations = relationship("ChannelConfiguration", back_populates="channel", cascade="all, delete-orphan")
    credentials = relationship("ChannelCredential", back_populates="channel", cascade="all, delete-orphan")
    messages = relationship("ChannelMessage", back_populates="channel", cascade="all, delete-orphan")
    webhook_logs = relationship("ChannelWebhookLog", back_populates="channel", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Channel(id={self.id}, channel_type={self.channel_type}, name={self.name})>"


class ChannelConfiguration(Base):
    """Channel configuration model"""
    
    __tablename__ = "channel_configurations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String(255), nullable=False, index=True)
    value = Column(Text, nullable=True)
    is_encrypted = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    channel = relationship("Channel", back_populates="configurations")
    
    def __repr__(self):
        return f"<ChannelConfiguration(id={self.id}, key={self.key})>"


class ChannelCredential(Base):
    """Channel credential model (encrypted)"""
    
    __tablename__ = "channel_credentials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True)
    credential_type = Column(String(100), nullable=False, index=True)  # API_KEY, ACCESS_TOKEN, WEBHOOK_SECRET, etc.
    encrypted_value = Column(Text, nullable=False)  # Encrypted credential
    iv = Column(String(255), nullable=True)  # Initialization vector for encryption
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    channel = relationship("Channel", back_populates="credentials")
    
    def __repr__(self):
        return f"<ChannelCredential(id={self.id}, credential_type={self.credential_type})>"


class ChannelMessage(Base):
    """Channel message model"""
    
    __tablename__ = "channel_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    external_message_id = Column(String(255), nullable=True, index=True)  # External platform message ID
    direction = Column(String(20), nullable=False)  # INCOMING, OUTGOING
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING, SENT, DELIVERED, READ, FAILED
    message_type = Column(String(50), nullable=False)  # TEXT, IMAGE, VIDEO, DOCUMENT, AUDIO, TEMPLATE
    
    # Message content
    content = Column(Text, nullable=True)
    media_url = Column(String(500), nullable=True)
    media_type = Column(String(100), nullable=True)
    template_name = Column(String(255), nullable=True)
    
    # Recipient/Sender info
    phone_number = Column(String(50), nullable=True, index=True)
    email_address = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    channel = relationship("Channel", back_populates="messages")
    
    def __repr__(self):
        return f"<ChannelMessage(id={self.id}, direction={self.direction}, status={self.status})>"


class ChannelWebhookLog(Base):
    """Channel webhook log model"""
    
    __tablename__ = "channel_webhook_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Webhook info
    event_type = Column(String(100), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    headers = Column(JSON, nullable=True)
    
    # Processing info
    processing_status = Column(String(50), nullable=False, default="PENDING")  # PENDING, PROCESSED, FAILED
    error_message = Column(Text, nullable=True)
    
    # Request info
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Timestamps
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    channel = relationship("Channel", back_populates="webhook_logs")
    
    def __repr__(self):
        return f"<ChannelWebhookLog(id={self.id}, event_type={self.event_type}, processing_status={self.processing_status})>"
