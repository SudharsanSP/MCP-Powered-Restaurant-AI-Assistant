"""
Tests for MCP_Client/src/routers/user_router.py
"""
import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from routers.user_router import router
from services.dependency import get_user_service
from services.user_service import UserService
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode


@pytest.fixture
def mock_user_service():
    return AsyncMock(spec=UserService)


@pytest.fixture
def test_app(mock_user_service):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    return app


class TestUserRouter:
    @pytest.mark.asyncio
    async def test_create_user_success(self, test_app, mock_user_service):
        fake_uuid = str(uuid.uuid4())
        mock_user_service.create_user.return_value = {
            "customer_uuid": fake_uuid,
            "access_token": "token123",
            "refresh_token": "refresh123",
            "expires_in": 1800,
        }

        payload = {
            "name": "Alice",
            "phone_number": "9876543210",
            "email": "alice@example.com",
            "password": "password123",
        }

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            response = await ac.post("/coffee_shop_bot/api/v1/user", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["status_code"] == 201
        assert data["data"]["customer_uuid"] == fake_uuid
        assert data["message"] == "User created successfully"

    @pytest.mark.asyncio
    async def test_create_user_custom_exception(self, test_app, mock_user_service):
        mock_user_service.create_user.side_effect = Custom_Exception(
            message="User already exists",
            code=ErrorCode.CONFLICT,
            status_code=HttpStatusCode.CONFLICT,
        )

        payload = {
            "name": "Alice",
            "phone_number": "9876543210",
            "email": "alice@example.com",
            "password": "password123",
        }

        with pytest.raises(Custom_Exception) as exc_info:
            async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
                await ac.post("/coffee_shop_bot/api/v1/user", json=payload)
        assert exc_info.value.code == ErrorCode.CONFLICT

    @pytest.mark.asyncio
    async def test_create_user_unhandled_exception(self, test_app, mock_user_service):
        mock_user_service.create_user.side_effect = RuntimeError("DB crash")

        payload = {
            "name": "Alice",
            "phone_number": "9876543210",
            "email": "alice@example.com",
            "password": "password123",
        }

        with pytest.raises(Custom_Exception) as exc_info:
            async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
                await ac.post("/coffee_shop_bot/api/v1/user", json=payload)
        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR
