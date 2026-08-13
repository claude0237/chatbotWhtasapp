"""Auth Service"""
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.config import settings
from app.users.models import User
from app.users.repositories import UserRepository
from app.users.schemas import UserCreate, TokenResponse
from app.logging_config import log_security, log_with_context


class AuthService:
    """Service for authentication operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repository = UserRepository(db)
        self.pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        self.logger = logging.getLogger("app.auth")
    
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[dict]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            return payload
        except JWTError:
            return None
    
    async def register(self, user_data: UserCreate) -> User:
        """Register a new user"""
        # Check if email already exists
        existing_user = await self.user_repository.get_by_email(user_data.email)
        if existing_user:
            log_security(
                self.logger,
                logging.WARNING,
                "AUTH_REGISTER_FAILED",
                email=user_data.email,
                reason="Email already registered"
            )
            raise ValueError("Email already registered")
        
        # Hash password
        hashed_password = self.hash_password(user_data.password)
        
        # Create user
        user = User(
            email=user_data.email,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            company_id=user_data.company_id,
            role=user_data.role,
            phone=user_data.phone,
            avatar_url=user_data.avatar_url
        )
        
        created_user = await self.user_repository.create(user)
        
        log_security(
            self.logger,
            logging.INFO,
            "AUTH_REGISTER_SUCCESS",
            user_id=str(created_user.id),
            email=user_data.email,
            company_id=str(user_data.company_id),
            role=user_data.role.value
        )
        
        return created_user
    
    async def login(self, email: str, password: str) -> TokenResponse:
        """Login user and return tokens"""
        # Get user by email
        user = await self.user_repository.get_by_email(email)
        if not user:
            log_security(
                self.logger,
                logging.WARNING,
                "AUTH_LOGIN_FAILED",
                email=email,
                reason="User not found"
            )
            raise ValueError("Invalid credentials")
        
        # Verify password
        if not self.verify_password(password, user.password_hash):
            log_security(
                self.logger,
                logging.WARNING,
                "AUTH_LOGIN_FAILED",
                email=email,
                user_id=str(user.id),
                reason="Invalid password"
            )
            raise ValueError("Invalid credentials")
        
        # Check if user is active
        if not user.is_active:
            log_security(
                self.logger,
                logging.WARNING,
                "AUTH_LOGIN_FAILED",
                email=email,
                user_id=str(user.id),
                reason="User account is inactive"
            )
            raise ValueError("User account is inactive")
        
        # Update last login
        await self.user_repository.update_last_login(user.id)
        
        # Create tokens
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email, "company_id": str(user.company_id), "role": user.role.value}
        )
        refresh_token = self.create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        log_security(
            self.logger,
            logging.INFO,
            "AUTH_LOGIN_SUCCESS",
            user_id=str(user.id),
            email=email,
            company_id=str(user.company_id),
            role=user.role.value
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token"""
        payload = self.decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            log_security(
                self.logger,
                logging.WARNING,
                "AUTH_TOKEN_REFRESH_FAILED",
                reason="Invalid refresh token type"
            )
            raise ValueError("Invalid refresh token")
        
        user_id = payload.get("sub")
        if not user_id:
            log_security(
                self.logger,
                logging.WARNING,
                "AUTH_TOKEN_REFRESH_FAILED",
                reason="No user_id in token"
            )
            raise ValueError("Invalid refresh token")
        
        user = await self.user_repository.get_by_id(UUID(user_id))
        if not user or not user.is_active:
            log_security(
                self.logger,
                logging.WARNING,
                "AUTH_TOKEN_REFRESH_FAILED",
                user_id=user_id,
                reason="User not found or inactive"
            )
            raise ValueError("Invalid refresh token")
        
        # Create new tokens
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email, "company_id": str(user.company_id), "role": user.role.value}
        )
        new_refresh_token = self.create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        log_security(
            self.logger,
            logging.INFO,
            "AUTH_TOKEN_REFRESH",
            user_id=str(user.id),
            email=user.email,
            company_id=str(user.company_id)
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token
        )
    
    async def verify_token(self, token: str) -> Optional[User]:
        """Verify token and return user"""
        payload = self.decode_token(token)
        if not payload or payload.get("type") != "access":
            log_security(
                self.logger,
                logging.WARNING,
                "AUTH_TOKEN_EXPIRED",
                reason="Invalid or expired token"
            )
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            log_security(
                self.logger,
                logging.WARNING,
                "AUTH_TOKEN_EXPIRED",
                reason="No user_id in token"
            )
            return None
        
        user = await self.user_repository.get_by_id(UUID(user_id))
        if not user or not user.is_active:
            log_security(
                self.logger,
                logging.WARNING,
                "AUTH_TOKEN_EXPIRED",
                user_id=user_id,
                reason="User not found or inactive"
            )
            return None
        
        return user
