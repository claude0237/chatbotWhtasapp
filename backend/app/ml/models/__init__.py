"""ML Models for Document Ingestion and Embeddings"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, JSON, Integer, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class FileType(str, enum.Enum):
    """File type enum"""
    PDF = "PDF"
    WORD = "WORD"
    EXCEL = "EXCEL"
    MARKDOWN = "MARKDOWN"
    TXT = "TXT"
    HTML = "HTML"


class DocumentStatus(str, enum.Enum):
    """Document processing status"""
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class IngestionJobStatus(str, enum.Enum):
    """Ingestion job status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Document(Base):
    """Document model for file ingestion"""
    
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    file_name = Column(String(500), nullable=False)
    file_type = Column(SQLEnum(FileType), nullable=False)
    file_path = Column(String(1000), nullable=True)  # S3/MinIO path
    file_size = Column(Integer, nullable=True)
    
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADING, nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Metadata
    extra_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", backref="documents")
    chunks = relationship("DocumentChunk", backref="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, file_name={self.file_name}, status={self.status})>"


class DocumentChunk(Base):
    """Document chunk model for embedding storage"""
    
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    # Embedding vector (stored as JSON array, pgvector used for similarity search in queries)
    embedding = Column(JSON, nullable=True)
    
    # Metadata
    extra_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"


class IngestionJob(Base):
    """Ingestion job model for tracking document processing"""
    
    __tablename__ = "ingestion_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    source_type = Column(String(100), nullable=False)  # FILE_UPLOAD, DATABASE, WEB_SCRAPER, etc.
    source_config = Column(JSON, nullable=True)  # Configuration for the source
    
    status = Column(SQLEnum(IngestionJobStatus), default=IngestionJobStatus.PENDING, nullable=False)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Job statistics
    total_documents = Column(Integer, default=0, nullable=False)
    processed_documents = Column(Integer, default=0, nullable=False)
    failed_documents = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", backref="ingestion_jobs")
    
    def __repr__(self):
        return f"<IngestionJob(id={self.id}, source_type={self.source_type}, status={self.status})>"
