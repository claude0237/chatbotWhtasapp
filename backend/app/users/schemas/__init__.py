"""User Schemas"""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from app.users.models import UserRoleEnum
import re


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name format"""
        if not re.match(r'^[a-zA-ZÀ-ÿ\s\-]+$', v):
            raise ValueError('Name must contain only letters, spaces, and hyphens')
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format"""
        if v and not re.match(r'^\+?[\d\s\-()]+$', v):
            raise ValueError('Invalid phone number format')
        return v


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=8)
    company_id: UUID
    role: UserRoleEnum = UserRoleEnum.AGENT
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[UserRoleEnum] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)
    company_id: Optional[UUID] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: UUID
    company_id: UUID
    company_name: Optional[str] = None
    role: UserRoleEnum
    is_active: bool
    is_verified: bool
    two_factor_enabled: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserRegister(UserCreate):
    """Schema for user registration"""


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
