"""
Tests for MCP_Client/src/routers/auth_router.py
"""
from unittest.mock import AsyncMock, MagicMock
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from routers.auth_router import router
from services.dependency import get_auth_service
from services.auth_service import AuthService
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode


@pytest.fixture
def mock_auth_service():
    return AsyncMock(spec=AuthService)


@pytest.fixture
def test_app(mock_auth_service):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    return app


class TestAuthRouter:
    @pytest.mark.asyncio
    async def test_customer_login_success(self, test_app, mock_auth_service):
        mock_auth_service.customer_login.return_value = {
            "access_token": "token1",
            "refresh_token": "token2",
            "expires_in": 1800,
        }
        payload = {"email": "cust@test.com", "password": "password123"}
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            res = await ac.post("/coffee_shop_bot/api/v1/auth/customer/login", json=payload)
        assert res.status_code == 200
        assert res.json()["data"]["access_token"] == "token1"

    @pytest.mark.asyncio
    async def test_admin_login_success(self, test_app, mock_auth_service):
        mock_auth_service.admin_login.return_value = {
            "access_token": "admintoken",
            "expires_in": 1800,
        }
        payload = {"email": "admin@test.com", "password": "password123"}
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            res = await ac.post("/coffee_shop_bot/api/v1/auth/admin/login", json=payload)
        assert res.status_code == 200
        assert res.json()["data"]["access_token"] == "admintoken"

    @pytest.mark.asyncio
    async def test_refresh_success(self, test_app, mock_auth_service):
        mock_auth_service.refresh.return_value = {
            "access_token": "newtoken",
            "expires_in": 1800,
        }
        payload = {"refresh_token": "a" * 32}
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            res = await ac.post("/coffee_shop_bot/api/v1/auth/refresh", json=payload)
        assert res.status_code == 200
        assert res.json()["data"]["access_token"] == "newtoken"

    @pytest.mark.asyncio
    async def test_logout_success(self, test_app, mock_auth_service):
        mock_auth_service.logout.return_value = {"message": "Logged out successfully"}
        payload = {"refresh_token": "b" * 32}
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            res = await ac.post("/coffee_shop_bot/api/v1/auth/logout", json=payload)
        assert res.status_code == 200
        assert res.json()["data"]["message"] == "Logged out successfully"

    @pytest.mark.asyncio
    async def test_customer_login_failure(self, test_app, mock_auth_service):
        mock_auth_service.customer_login.side_effect = Custom_Exception(
            message="Invalid credentials",
            code=ErrorCode.UNAUTHORIZED,
            status_code=HttpStatusCode.UNAUTHORIZED,
        )
        payload = {"email": "wrong@test.com", "password": "password123"}
        with pytest.raises(Custom_Exception) as exc_info:
            async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
                await ac.post("/coffee_shop_bot/api/v1/auth/customer/login", json=payload)
        assert exc_info.value.code == ErrorCode.UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_admin_login_unhandled_exception(self, test_app, mock_auth_service):
        mock_auth_service.admin_login.side_effect = RuntimeError("Crash")
        payload = {"email": "admin@test.com", "password": "password123"}
        with pytest.raises(Custom_Exception) as exc_info:
            async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
                await ac.post("/coffee_shop_bot/api/v1/auth/admin/login", json=payload)
        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("method", "path", "payload"),
        [
            (
                "customer_login",
                "/coffee_shop_bot/api/v1/auth/customer/login",
                {"email": "customer@example.com", "password": "password123"},
            ),
            (
                "refresh",
                "/coffee_shop_bot/api/v1/auth/refresh",
                {"refresh_token": "a" * 32},
            ),
            (
                "logout",
                "/coffee_shop_bot/api/v1/auth/logout",
                {"refresh_token": "b" * 32},
            ),
        ],
    )
    async def test_unexpected_service_errors_are_wrapped(
        self, test_app, mock_auth_service, method, path, payload
    ):
        getattr(mock_auth_service, method).side_effect = RuntimeError("service failure")

        with pytest.raises(Custom_Exception) as exc_info:
            async with AsyncClient(
                transport=ASGITransport(app=test_app), base_url="http://test"
            ) as client:
                await client.post(path, json=payload)

        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR
