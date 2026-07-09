"""Customer Model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Customer(Base):
    """Customer model"""
    
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    phone_number = Column(String(50), nullable=False, index=True)  # Unique per company
    name = Column(String(255), nullable=True)
    profile_picture_url = Column(String(500), nullable=True)
    extra_data = Column(JSON, nullable=True)
    
    # Timestamps
    first_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Composite index for phone_number + company_id
    __table_args__ = (
        Index('ix_customers_phone_number_company_id', 'phone_number', 'company_id'),
    )
    
    # Relationships
    company = relationship("Company", backref="customers")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, phone_number={self.phone_number}, company_id={self.company_id})>"
