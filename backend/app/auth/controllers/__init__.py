"""Auth Controller"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.services import AuthService
from app.auth.dependencies import get_auth_service, get_current_active_user
from app.users.schemas import UserLogin, UserRegister, TokenResponse
from app.users.models import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user"""
    try:
        await auth_service.register(user_data)
        # Auto-login after registration
        tokens = await auth_service.login(user_data.email, user_data.password)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user and return tokens"""
    try:
        tokens = await auth_service.login(login_data.email, login_data.password)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token using refresh token"""
    try:
        tokens = await auth_service.refresh_token(refresh_token)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout")
async def logout():
    """Logout user (client-side token invalidation)"""
    # In a production app, you might want to invalidate the refresh token
    # by storing it in a blacklist or using a token store
    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_current_user(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Get current authenticated user"""
    from sqlalchemy import select
    from app.companies.models import Company
    
    company_name = None
    if current_user.company_id:
        result = await db.execute(select(Company.name).where(Company.id == current_user.company_id))
        company_name = result.scalar_one_or_none()
    
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role.value,
        "company_id": str(current_user.company_id),
        "company_name": company_name,
        "is_active": current_user.is_active
    }
