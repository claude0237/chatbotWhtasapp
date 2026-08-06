"""Company Schemas"""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re
from app.companies.models import SubscriptionPlan


class CompanyBase(BaseModel):
    """Base company schema"""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format"""
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v
    
    @field_validator('website')
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        """Validate website URL format"""
        if v and not re.match(r'^https?://', v):
            raise ValueError('Website must start with http:// or https://')
        return v


class CompanyCreate(CompanyBase):
    """Schema for creating a company (super admin) — includes optional settings"""
    is_active: bool = True
    is_suspended: bool = False
    ml_enabled: bool = False
    subscription_plan: SubscriptionPlan = SubscriptionPlan.FREE
    # Inline company settings (created automatically with the company)
    timezone: str = "UTC"
    language: str = "en"
    currency: str = "USD"
    theme_color: str = "#3b82f6"
    custom_domain: Optional[str] = None
    settings: Optional[str] = None  # JSON string for additional settings


class CompanyUpdate(BaseModel):
    """Schema for updating a company"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None
    ml_enabled: Optional[bool] = None
    subscription_plan: Optional[str] = None
    
    @field_validator('subscription_plan')
    @classmethod
    def validate_subscription_plan(cls, v: Optional[str]) -> Optional[SubscriptionPlan]:
        """Validate subscription plan"""
        if v is None:
            return None
        try:
            return SubscriptionPlan(v)
        except ValueError:
            raise ValueError(f'Invalid subscription plan. Must be one of: {[p.value for p in SubscriptionPlan]}')


class CompanyResponse(CompanyBase):
    """Schema for company response"""
    id: UUID
    is_active: bool
    is_suspended: bool
    ml_enabled: bool
    subscription_plan: SubscriptionPlan
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CompanySettingsBase(BaseModel):
    """Base company settings schema"""
    timezone: str = "UTC"
    language: str = "en"
    currency: str = "USD"
    theme_color: str = "#3b82f6"
    logo_url: Optional[str] = None
    custom_domain: Optional[str] = None
    settings: Optional[str] = None


class CompanySettingsCreate(CompanySettingsBase):
    """Schema for creating company settings"""
    company_id: UUID


class CompanySettingsUpdate(BaseModel):
    """Schema for updating company settings"""
    timezone: Optional[str] = None
    language: Optional[str] = None
    currency: Optional[str] = None
    theme_color: Optional[str] = None
    logo_url: Optional[str] = None
    custom_domain: Optional[str] = None
    settings: Optional[str] = None


class CompanySettingsResponse(CompanySettingsBase):
    """Schema for company settings response"""
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
