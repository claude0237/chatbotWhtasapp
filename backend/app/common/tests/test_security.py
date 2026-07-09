"""Security tests - SQL injection, XSS, CSRF, tenant isolation"""
import pytest
from httpx import AsyncClient


SQLI_PAYLOADS = [
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "1 UNION SELECT * FROM users--",
    "admin'--",
    "' OR 1=1--",
]

XSS_PAYLOADS = [
    "<script>alert('xss')</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert(1)",
    "<svg onload=alert(1)>",
    "';alert(String.fromCharCode(88,83,83))//",
]


class TestSQLInjection:

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", SQLI_PAYLOADS)
    async def test_login_sql_injection(self, client: AsyncClient, payload: str):
        """Login endpoint must not be vulnerable to SQL injection"""
        response = await client.post("/api/v1/auth/login", json={
            "email": payload,
            "password": payload,
        })
        # Must never return 200 with a valid token on injection payloads
        assert response.status_code in (400, 401, 422), (
            f"Possible SQLi vulnerability with payload: {payload!r}"
        )
        if response.status_code == 200:
            data = response.json()
            assert "access_token" not in data

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", SQLI_PAYLOADS)
    async def test_search_sql_injection(self, client: AsyncClient, auth_headers: dict, test_company, payload: str):
        """Search endpoints must sanitize input"""
        response = await client.get(
            f"/api/v1/companies/{test_company.id}/products",
            params={"search": payload},
            headers=auth_headers,
        )
        # Should return 200 (empty results) or 4xx, never 500
        assert response.status_code != 500, (
            f"Server error with SQLi payload: {payload!r}"
        )


class TestXSSPrevention:

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    async def test_registration_xss(self, client: AsyncClient, payload: str):
        """Registration should not reflect XSS payloads"""
        response = await client.post("/api/v1/auth/register", json={
            "email": "xss@test.com",
            "password": "ValidPass123!",
            "first_name": payload,
            "last_name": "Test",
            "company_name": "Test Co",
        })
        # If 200, check the response body doesn't contain raw script tags
        if response.status_code == 201:
            body = response.text
            assert "<script>" not in body
            assert "onerror=" not in body

    @pytest.mark.asyncio
    async def test_content_type_json(self, client: AsyncClient):
        """API responses must be JSON, not HTML"""
        response = await client.get("/api/v1/auth/me")
        assert response.headers.get("content-type", "").startswith("application/json")


class TestCSRFProtection:

    @pytest.mark.asyncio
    async def test_state_changing_requires_auth(self, client: AsyncClient):
        """POST/PUT/DELETE endpoints require authentication"""
        endpoints = [
            ("POST",   "/notifications/read-all"),
            ("DELETE", "/notifications/fake-id"),
            ("PUT",    "/notifications/preferences"),
        ]
        for method, path in endpoints:
            response = await client.request(method, path)
            assert response.status_code in (401, 403, 422), (
                f"{method} {path} should require authentication"
            )


class TestTenantIsolation:

    @pytest.mark.asyncio
    async def test_cannot_access_other_company_notifications(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db,
    ):
        """User must not see notifications from another company"""
        import uuid
        from app.notifications.models import Notification, NotificationType
        from app.companies.models import Company
        from app.users.models import User, UserRoleEnum as UserRole
        from app.auth.utils import get_password_hash

        # Create second company + user
        other_company = Company(id=uuid.uuid4(), name="Other Co", email="other@co.com", is_active=True)
        db.add(other_company)
        other_user = User(
            id=uuid.uuid4(),
            company_id=other_company.id,
            email="other@test.com",
            password_hash=get_password_hash("password123"),
            first_name="Other",
            last_name="User",
            role=UserRole.AGENT,
            is_active=True,
            is_verified=True,
        )
        db.add(other_user)

        # Create notification for other user
        notif = Notification(
            id=uuid.uuid4(),
            user_id=other_user.id,
            notification_type=NotificationType.SYSTEM,
            title="Secret",
            message="Should not see this",
            is_read=False,
        )
        db.add(notif)
        await db.commit()

        # Authenticated user fetches notifications — must not see other user's
        response = await client.get("/notifications", headers=auth_headers)
        assert response.status_code == 200
        ids = [n["id"] for n in response.json()]
        assert str(notif.id) not in ids
