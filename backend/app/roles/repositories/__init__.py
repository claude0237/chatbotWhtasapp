"""Role Repository"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.roles.models import Role


class RoleRepository:
    """Repository for Role model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, role: Role) -> Role:
        """Create a new role"""
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def get_by_id(self, role_id: UUID) -> Optional[Role]:
        """Get role by ID"""
        result = await self.db.execute(
            select(Role).where(Role.id == role_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name"""
        result = await self.db.execute(
            select(Role).where(Role.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Role]:
        """Get all roles with pagination"""
        result = await self.db.execute(
            select(Role).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def update(self, role: Role) -> Role:
        """Update role"""
        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def delete(self, role_id: UUID) -> bool:
        """Delete role by ID (only if not system role)"""
        role = await self.get_by_id(role_id)
        if role and not role.is_system:
            await self.db.delete(role)
            await self.db.commit()
            return True
        return False
