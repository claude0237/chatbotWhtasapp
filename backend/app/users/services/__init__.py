"""User Service"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User, UserRoleEnum
from app.users.repositories import UserRepository
from app.users.schemas import UserCreate, UserUpdate
from app.auth.services import AuthService


class UserService:
    """Service for user operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repository = UserRepository(db)
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        auth_service = AuthService(self.db)
        user = User(
            email=user_data.email,
            password_hash=auth_service.hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            company_id=user_data.company_id,
            role=user_data.role,
            phone=user_data.phone,
            avatar_url=user_data.avatar_url
        )
        return await self.user_repository.create(user)
    
    async def get_user(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        return await self.user_repository.get_by_id(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return await self.user_repository.get_by_email(email)
    
    async def get_company_users(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by company ID"""
        return await self.user_repository.get_by_company_id(company_id, skip, limit)
    
    async def update_user(self, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """Update user"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        # Handle password separately — hash it before saving
        if 'password' in update_data:
            raw_password = update_data.pop('password')
            auth_service = AuthService(self.db)
            user.password_hash = auth_service.hash_password(raw_password)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        return await self.user_repository.update(user)
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user (soft delete)"""
        return await self.user_repository.delete(user_id)
    
    async def get_all_non_superadmin(self, skip: int = 0, limit: int = 500) -> List[User]:
        """Get all users across all companies (SUPER_ADMIN view, excludes SUPER_ADMIN accounts)"""
        users = await self.user_repository.get_all_non_superadmin(skip, limit)
        # Load company names for each user
        for user in users:
            if user.company_id:
                from sqlalchemy import select
                from app.companies.models import Company
                result = await self.db.execute(
                    select(Company.name).where(Company.id == user.company_id)
                )
                company_name = result.scalar_one_or_none()
                # Add company_name as a dynamic attribute (not in model)
                setattr(user, 'company_name', company_name)
        return users

    async def get_active_users(self, company_id: UUID) -> List[User]:
        """Get all active users for a company"""
        return await self.user_repository.get_active_users(company_id)
    
    async def change_user_role(self, user_id: UUID, new_role: UserRoleEnum) -> Optional[User]:
        """Change user role"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None
        
        user.role = new_role
        return await self.user_repository.update(user)
