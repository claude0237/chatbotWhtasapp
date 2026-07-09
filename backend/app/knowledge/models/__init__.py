"""Knowledge Base Models"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, JSON, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class SourceType(str, enum.Enum):
    """Knowledge source type"""
    FAQ = "FAQ"
    MANUAL = "MANUAL"
    IMPORTED = "IMPORTED"


class KnowledgeCategory(Base):
    """Knowledge category model"""
    
    __tablename__ = "knowledge_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    icon = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", backref="knowledge_categories")
    parent = relationship("KnowledgeCategory", remote_side=[id], backref="children")
    entries = relationship("KnowledgeBase", backref="category", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KnowledgeCategory(id={self.id}, name={self.name}, parent_id={self.parent_id})>"


class KnowledgeBase(Base):
    """Knowledge base entry model"""
    
    __tablename__ = "knowledge_base"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    
    source_type = Column(SQLEnum(SourceType), default=SourceType.MANUAL, nullable=False)
    source_id = Column(String(255), nullable=True)  # Reference to external source
    
    extra_data = Column(JSON, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Composite index for category + company_id
    __table_args__ = (
        Index('ix_knowledge_base_category_company_id', 'category_id', 'company_id'),
    )
    
    # Relationships
    company = relationship("Company", backref="knowledge_entries")
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, title={self.title}, source_type={self.source_type})>"
