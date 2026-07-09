"""Audit Log Service"""
from typing import Optional
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.audit.repositories import AuditLogRepository
from app.audit.models import AuditActionEnum
from uuid import UUID


class AuditService:
    """Service for audit logging"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = AuditLogRepository(db)
    
    async def log_action(
        self,
        user_id: UUID,
        company_id: UUID,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        request: Optional[Request] = None
    ):
        """Log an action to the audit trail"""
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
        
        await self.repository.create(
            user_id=user_id,
            company_id=company_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_login(self, user_id: UUID, company_id: UUID, request: Optional[Request] = None):
        """Log a user login"""
        await self.log_action(
            user_id=user_id,
            company_id=company_id,
            action=AuditActionEnum.LOGIN,
            resource_type="User",
            resource_id=str(user_id),
            request=request
        )
    
    async def log_logout(self, user_id: UUID, company_id: UUID, request: Optional[Request] = None):
        """Log a user logout"""
        await self.log_action(
            user_id=user_id,
            company_id=company_id,
            action=AuditActionEnum.LOGOUT,
            resource_type="User",
            resource_id=str(user_id),
            request=request
        )
    
    async def log_create(
        self,
        user_id: UUID,
        company_id: UUID,
        resource_type: str,
        resource_id: str,
        details: Optional[dict] = None,
        request: Optional[Request] = None
    ):
        """Log a resource creation"""
        await self.log_action(
            user_id=user_id,
            company_id=company_id,
            action=AuditActionEnum.CREATE,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            request=request
        )
    
    async def log_update(
        self,
        user_id: UUID,
        company_id: UUID,
        resource_type: str,
        resource_id: str,
        details: Optional[dict] = None,
        request: Optional[Request] = None
    ):
        """Log a resource update"""
        await self.log_action(
            user_id=user_id,
            company_id=company_id,
            action=AuditActionEnum.UPDATE,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            request=request
        )
    
    async def log_delete(
        self,
        user_id: UUID,
        company_id: UUID,
        resource_type: str,
        resource_id: str,
        details: Optional[dict] = None,
        request: Optional[Request] = None
    ):
        """Log a resource deletion"""
        await self.log_action(
            user_id=user_id,
            company_id=company_id,
            action=AuditActionEnum.DELETE,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            request=request
        )
