"""Analytics Models"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Float, Integer, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ReportType(str, enum.Enum):
    """Report type enum"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class AnalyticsMetric(Base):
    """Analytics metric model for tracking events"""
    
    __tablename__ = "analytics_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    metric_name = Column(String(255), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    
    # Dimensions for filtering and grouping (JSONB)
    dimensions = Column(JSON, nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    company = relationship("Company", backref="analytics_metrics")
    
    def __repr__(self):
        return f"<AnalyticsMetric(id={self.id}, metric_name={self.metric_name}, metric_value={self.metric_value})>"


class AnalyticsReport(Base):
    """Analytics report model for generated reports"""
    
    __tablename__ = "analytics_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    report_name = Column(String(255), nullable=False)
    report_type = Column(SQLEnum(ReportType), nullable=False)
    
    # Report data (JSONB)
    data = Column(JSON, nullable=False)
    
    # Timestamp
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", backref="analytics_reports")
    
    def __repr__(self):
        return f"<AnalyticsReport(id={self.id}, report_name={self.report_name}, report_type={self.report_type})>"
