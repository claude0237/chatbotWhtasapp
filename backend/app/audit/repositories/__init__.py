"""Audit Log Repository"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.audit.models import AuditLog, AuditActionEnum
from uuid import UUID


class AuditLogRepository:
    """Repository for audit log operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        user_id: UUID,
        company_id: UUID,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Create a new audit log entry"""
        audit_log = AuditLog(
            user_id=user_id,
            company_id=company_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )
        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)
        return audit_log
    
    async def get_by_company(
        self,
        company_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get audit logs for a company"""
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.company_id == company_id)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    async def get_by_user(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get audit logs for a user"""
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    async def get_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        company_id: UUID,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a specific resource"""
        result = await self.db.execute(
            select(AuditLog)
            .where(
                and_(
                    AuditLog.company_id == company_id,
                    AuditLog.resource_type == resource_type,
                    AuditLog.resource_id == resource_id
                )
            )
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_recent(
        self,
        company_id: UUID,
        days: int = 7,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get recent audit logs for a company"""
        since_date = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(AuditLog)
            .where(
                and_(
                    AuditLog.company_id == company_id,
                    AuditLog.created_at >= since_date
                )
            )
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )
        return result.scalars().all()
