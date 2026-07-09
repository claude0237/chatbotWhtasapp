"""User Repository"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.users.models import User, UserRoleEnum


class UserRepository:
    """Repository for User model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, user: User) -> User:
        """Create a new user"""
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.deleted_at == None)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_company_id(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by company ID with pagination (excludes SUPER_ADMIN)"""
        result = await self.db.execute(
            select(User)
            .where(
                and_(
                    User.company_id == company_id,
                    User.deleted_at == None,
                    User.role != UserRoleEnum.SUPER_ADMIN
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_role(self, role: UserRoleEnum, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by role with pagination"""
        result = await self.db.execute(
            select(User)
            .where(User.role == role)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_company_and_role(self, company_id: UUID, role: UserRoleEnum) -> List[User]:
        """Get users by company ID and role"""
        result = await self.db.execute(
            select(User)
            .where(User.company_id == company_id, User.role == role)
        )
        return result.scalars().all()
    
    async def update(self, user: User) -> User:
        """Update user"""
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def delete(self, user_id: UUID) -> bool:
        """Delete user by ID (soft delete)"""
        user = await self.get_by_id(user_id)
        if user:
            user.deleted_at = datetime.utcnow()
            await self.db.commit()
            return True
        return False
    
    async def get_active_users(self, company_id: UUID) -> List[User]:
        """Get all active users for a company (excludes SUPER_ADMIN)"""
        result = await self.db.execute(
            select(User)
            .where(
                and_(
                    User.company_id == company_id,
                    User.is_active == True,
                    User.role != UserRoleEnum.SUPER_ADMIN
                )
            )
        )
        return result.scalars().all()
    
    async def get_all_non_superadmin(self, skip: int = 0, limit: int = 500) -> List[User]:
        """Get all users across all companies, excluding SUPER_ADMIN accounts"""
        result = await self.db.execute(
            select(User)
            .where(
                and_(
                    User.deleted_at == None,
                    User.role != UserRoleEnum.SUPER_ADMIN
                )
            )
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update_last_login(self, user_id: UUID) -> Optional[User]:
        """Update user last login timestamp"""
        user = await self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(user)
            return user
        return None
