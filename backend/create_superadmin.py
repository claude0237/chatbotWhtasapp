import asyncio
from app.database import AsyncSessionLocal
from app.users.models import User, UserRoleEnum
from app.users.repositories import UserRepository
from app.companies.models import Company
from app.companies.repositories import CompanyRepository
from datetime import datetime
from uuid import uuid4
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

async def create_superadmin():
    async with AsyncSessionLocal() as db:
        # Create or get system company for superadmin
        company_repo = CompanyRepository(db)
        company = await company_repo.get_by_slug('system')
        if not company:
            company = Company(
                id=uuid4(),
                name='System',
                slug='system',
                description='System company for superadmin',
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            company = await company_repo.create(company)
            print(f'Created system company: {company.id}')
        else:
            print(f'Using existing system company: {company.id}')
        
        # Create superadmin user
        user_repo = UserRepository(db)
        existing_user = await user_repo.get_by_email('superadmin@system.com')
        
        if existing_user:
            # Update existing user password with correct hash
            hashed_password = pwd_context.hash('superadmin123')
            existing_user.password_hash = hashed_password
            existing_user.role = UserRoleEnum.SUPER_ADMIN
            existing_user.is_active = True
            existing_user.company_id = company.id
            await user_repo.update(existing_user)
            print(f'Updated existing superadmin: superadmin@system.com')
            print(f'Company ID: {company.id}')
            print(f'User ID: {existing_user.id}')
            return
        
        hashed_password = pwd_context.hash('superadmin123')
        user = User(
            id=uuid4(),
            company_id=company.id,
            email='superadmin@system.com',
            password_hash=hashed_password,
            first_name='Super',
            last_name='Admin',
            role=UserRoleEnum.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        user = await user_repo.create(user)
        print(f'Created superadmin user: {user.id}')
        print(f'Email: superadmin@system.com')
        print(f'Password: superadmin123')
        print(f'Company ID: {company.id}')

if __name__ == '__main__':
    asyncio.run(create_superadmin())
