"""Global pytest configuration and shared fixtures"""
import asyncio
import uuid
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.users.models import User, UserRole
from app.companies.models import Company


# ─── Test DB engine (SQLite in-memory) ───────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ─── Shared model factories ───────────────────────────────────────────────────

@pytest_asyncio.fixture
async def test_company(db: AsyncSession) -> Company:
    company = Company(
        id=uuid.uuid4(),
        name="Test Company",
        email="company@test.com",
        is_active=True,
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company


@pytest_asyncio.fixture
async def test_user(db: AsyncSession, test_company: Company) -> User:
    from app.auth.utils import get_password_hash
    user = User(
        id=uuid.uuid4(),
        company_id=test_company.id,
        email="agent@test.com",
        password_hash=get_password_hash("password123"),
        first_name="Test",
        last_name="Agent",
        role=UserRole.AGENT,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db: AsyncSession, test_company: Company) -> User:
    from app.auth.utils import get_password_hash
    admin = User(
        id=uuid.uuid4(),
        company_id=test_company.id,
        email="admin@test.com",
        password_hash=get_password_hash("password123"),
        first_name="Test",
        last_name="Admin",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get auth headers for test_user"""
    response = await client.post("/api/v1/auth/login", json={
        "email": "agent@test.com",
        "password": "password123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient, test_admin: User) -> dict:
    """Get auth headers for test_admin"""
    response = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "password123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
