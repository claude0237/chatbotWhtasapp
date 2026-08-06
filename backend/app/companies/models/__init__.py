"""Company Model"""
import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class SubscriptionPlan(str, enum.Enum):
    """Subscription plan for companies"""
    FREE = "FREE"
    BASIC = "BASIC"
    PREMIUM = "PREMIUM"
    ENTERPRISE = "ENTERPRISE"


class Company(Base):
    """Company model for multi-tenant architecture"""
    
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    website = Column(String(500), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_suspended = Column(Boolean, default=False, nullable=False)
    ml_enabled = Column(Boolean, default=False, nullable=False)
    subscription_plan = Column(SQLEnum(SubscriptionPlan), default=SubscriptionPlan.FREE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Company(id={self.id}, name={self.name}, slug={self.slug})>"


class CompanySettings(Base):
    """Company settings model"""
    
    __tablename__ = "company_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    timezone = Column(String(50), default="UTC", nullable=False)
    language = Column(String(10), default="en", nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    theme_color = Column(String(7), default="#3b82f6", nullable=False)
    custom_domain = Column(String(255), nullable=True)
    settings = Column(Text, nullable=True)  # JSON string for additional settings
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", backref="settings")
    
    def __repr__(self):
        return f"<CompanySettings(company_id={self.company_id}, timezone={self.timezone})>"


class MLQuota(Base):
    """ML quota configuration per subscription plan"""
    
    __tablename__ = "ml_quotas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    plan = Column(String(20), unique=True, nullable=False, index=True)
    
    # Quota limits
    monthly_requests = Column(Integer, nullable=False)  # Max requests per month
    daily_requests = Column(Integer, nullable=True)  # Max requests per day (optional)
    max_tokens_per_request = Column(Integer, nullable=True)  # Max tokens per request
    
    # Pricing (optional, for billing)
    price_per_1000_requests = Column(Integer, nullable=True)  # Price in cents
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<MLQuota(plan={self.plan}, monthly_requests={self.monthly_requests})>"


class MLUsage(Base):
    """ML usage tracking per company"""
    
    __tablename__ = "ml_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Usage counters
    monthly_requests = Column(Integer, default=0, nullable=False)
    daily_requests = Column(Integer, default=0, nullable=False)
    total_requests = Column(Integer, default=0, nullable=False)
    
    # Period tracking
    current_month = Column(Integer, nullable=False)  # YYYYMM format
    current_day = Column(DateTime, nullable=False)  # Current day for daily reset
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", backref="ml_usage")
    
    def __repr__(self):
        return f"<MLUsage(company_id={self.company_id}, monthly_requests={self.monthly_requests})>"
