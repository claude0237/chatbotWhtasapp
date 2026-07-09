"""Auth Dependencies"""
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.auth.services import AuthService
from app.users.models import User, UserRoleEnum


security = HTTPBearer()


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Get auth service instance"""
    return AuthService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    user = await auth_service.verify_token(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    # Super admins bypass company checks
    if current_user.role != UserRoleEnum.SUPER_ADMIN:
        from app.companies.models import Company
        result = await db.execute(
            select(Company).where(Company.id == current_user.company_id)
        )
        company = result.scalar_one_or_none()
        if company and (not company.is_active or company.is_suspended):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Company account is disabled or suspended"
            )
    return current_user


async def get_current_company_id(
    current_user: User = Depends(get_current_user)
) -> str:
    """Get current user's company ID for multi-tenant isolation"""
    return str(current_user.company_id)


# RBAC Dependencies
def require_roles(allowed_roles: List[UserRoleEnum]):
    """Dependency factory to require specific roles"""
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


def require_role(role: UserRoleEnum):
    """Dependency to require a specific role"""
    return require_roles([role])


async def require_company_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require user to be a company admin or super admin"""
    if current_user.role not in [UserRoleEnum.COMPANY_ADMIN, UserRoleEnum.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company admin or super admin required"
        )
    return current_user


async def require_super_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require user to be a super admin"""
    if current_user.role != UserRoleEnum.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin required"
        )
    return current_user
