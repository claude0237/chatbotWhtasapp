"""User Controller"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.users.services import UserService
from app.users.schemas import UserCreate, UserUpdate, UserResponse
from app.auth.dependencies import (
    get_current_active_user, get_current_company_id,
    require_company_admin
)
from app.users.models import User, UserRoleEnum


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    user_company_id: str = Depends(get_current_company_id)
):
    """Create a new user (company admin only)"""
    user_service = UserService(db)
    
    # Multi-tenant check: can only create users for own company
    if str(user_data.company_id) != user_company_id and current_user.role.value != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only create users for your own company"
        )
    
    try:
        user = await user_service.create_user(user_data)
        return user
    except IntegrityError as e:
        await db.rollback()
        if 'ix_users_email' in str(e.orig) or 'unique' in str(e.orig).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Un utilisateur avec l'email '{user_data.email}' existe déjà."
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    user_company_id: str = Depends(get_current_company_id)
):
    """Get user by ID"""
    user_service = UserService(db)
    user = await user_service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Multi-tenant check: can only access users from own company
    if str(user.company_id) != user_company_id and current_user.role.value != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return user


@router.get("", response_model=List[UserResponse])
@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    user_company_id: str = Depends(get_current_company_id)
):
    """Get users from current user's company"""
    user_service = UserService(db)
    
    if current_user.role.value == "SUPER_ADMIN":
        return await user_service.get_all_non_superadmin(skip, limit)

    return await user_service.get_company_users(user_company_id, skip, limit)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    user_company_id: str = Depends(get_current_company_id)
):
    """Update user"""
    user_service = UserService(db)
    
    # Check if user exists and belongs to company
    target_user = await user_service.get_user(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Multi-tenant check
    if str(target_user.company_id) != user_company_id and current_user.role.value != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Role change requires company admin or super admin
    if user_data.role and current_user.role.value not in ["COMPANY_ADMIN", "SUPER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can change user roles"
        )
    
    user = await user_service.update_user(user_id, user_data)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    user_company_id: str = Depends(get_current_company_id)
):
    """Delete user (company admin only)"""
    user_service = UserService(db)
    
    # Check if user exists and belongs to company
    target_user = await user_service.get_user(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Multi-tenant check
    if str(target_user.company_id) != user_company_id and current_user.role.value != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Cannot delete a super admin
    if target_user.role.value == "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete a super admin account"
        )

    # Cannot delete yourself
    if str(target_user.id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    success = await user_service.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.get("/company/{company_id}", response_model=List[UserResponse])
async def get_company_users_endpoint(
    company_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    user_company_id: str = Depends(get_current_company_id)
):
    """Get users by company ID"""
    user_service = UserService(db)
    
    # Multi-tenant check
    if company_id != user_company_id and current_user.role.value != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return await user_service.get_company_users(company_id, skip, limit)


@router.put("/{user_id}/role/{new_role}", response_model=UserResponse)
async def change_user_role(
    user_id: str,
    new_role: UserRoleEnum,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    user_company_id: str = Depends(get_current_company_id)
):
    """Change user role (company admin only)"""
    user_service = UserService(db)
    
    # Check if user exists and belongs to company
    target_user = await user_service.get_user(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Multi-tenant check
    if str(target_user.company_id) != user_company_id and current_user.role.value != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Cannot change your own role
    if str(target_user.id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    # Only super admin can assign super admin role
    if new_role == UserRoleEnum.SUPER_ADMIN and current_user.role.value != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can assign super admin role"
        )
    
    user = await user_service.change_user_role(user_id, new_role)
    return user
