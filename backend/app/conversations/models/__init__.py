"""Conversation Models"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ConversationStatus(str, enum.Enum):
    """Conversation status"""
    OPEN = "OPEN"
    WAITING = "WAITING"
    AI = "AI"
    AGENT = "AGENT"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class ConversationPriority(str, enum.Enum):
    """Conversation priority"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class SenderType(str, enum.Enum):
    """Message sender type"""
    CUSTOMER = "CUSTOMER"
    AGENT = "AGENT"
    BOT = "BOT"


class ConversationMessageType(str, enum.Enum):
    """Message type (conversation messages)"""
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    AUDIO = "AUDIO"


class ConversationMessageStatus(str, enum.Enum):
    """Message status (conversation messages)"""
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    FAILED = "FAILED"


class Conversation(Base):
    """Conversation model"""
    
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id", ondelete="SET NULL"), nullable=True)
    
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.OPEN, nullable=False, index=True)
    priority = Column(SQLEnum(ConversationPriority), default=ConversationPriority.MEDIUM, nullable=False)
    assigned_agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    tags = Column(JSON, nullable=True)  # List of tags
    last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    
    # Composite index for status + company_id
    __table_args__ = (
        Index('ix_conversations_status_company_id', 'status', 'company_id'),
    )
    
    # Relationships
    company = relationship("Company", backref="conversations")
    customer = relationship("Customer", backref="conversations")
    assigned_agent = relationship("User", foreign_keys=[assigned_agent_id], backref="assigned_conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    notes = relationship("ConversationNote", backref="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, status={self.status}, customer_id={self.customer_id})>"


class Message(Base):
    """Message model (conversation messages)"""
    
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_type = Column(SQLEnum(SenderType), nullable=False)
    sender_id = Column(UUID(as_uuid=True), nullable=True)  # User ID if AGENT, Customer ID if CUSTOMER
    
    content = Column(Text, nullable=True)
    message_type = Column(SQLEnum(ConversationMessageType), default=ConversationMessageType.TEXT, nullable=False)
    media_url = Column(String(500), nullable=True)
    external_message_id = Column(String(255), nullable=True, index=True)  # WhatsApp message ID
    
    status = Column(SQLEnum(ConversationMessageStatus), default=ConversationMessageStatus.SENT, nullable=False)
    
    # Timestamps
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, sender_type={self.sender_type}, conversation_id={self.conversation_id})>"


class ConversationNote(Base):
    """Conversation note model (internal notes)"""
    
    __tablename__ = "conversation_notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", backref="conversation_notes")
    
    def __repr__(self):
        return f"<ConversationNote(id={self.id}, conversation_id={self.conversation_id}, user_id={self.user_id})>"
