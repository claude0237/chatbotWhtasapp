"""Permission Repository"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.permissions.models import Permission


class PermissionRepository:
    """Repository for Permission model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, permission: Permission) -> Permission:
        """Create a new permission"""
        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)
        return permission
    
    async def get_by_id(self, permission_id: UUID) -> Optional[Permission]:
        """Get permission by ID"""
        result = await self.db.execute(
            select(Permission).where(Permission.id == permission_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Permission]:
        """Get permission by name"""
        result = await self.db.execute(
            select(Permission).where(Permission.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_by_resource(self, resource: str) -> List[Permission]:
        """Get permissions by resource"""
        result = await self.db.execute(
            select(Permission).where(Permission.resource == resource)
        )
        return result.scalars().all()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Permission]:
        """Get all permissions with pagination"""
        result = await self.db.execute(
            select(Permission).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def update(self, permission: Permission) -> Permission:
        """Update permission"""
        await self.db.commit()
        await self.db.refresh(permission)
        return permission
    
    async def delete(self, permission_id: UUID) -> bool:
        """Delete permission by ID"""
        permission = await self.get_by_id(permission_id)
        if permission:
            await self.db.delete(permission)
            await self.db.commit()
            return True
        return False
