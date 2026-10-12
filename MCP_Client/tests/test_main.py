"""
Tests for MCP_Client/src/main.py
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from main import app, lifespan, custom_exception_handler, validation_exception_handler
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode


class TestMainLifespan:
    @pytest.mark.asyncio
    async def test_lifespan_startup_and_shutdown(self):
        fake_app = MagicMock()
        fake_app.state = MagicMock()

        mock_deps = {"agent": MagicMock()}

        async def fake_lifespan_dependencies():
            yield mock_deps

        with patch("main.lifespan_dependencies", side_effect=fake_lifespan_dependencies), \
             patch("main.Database") as mock_db_cls:
            mock_db = MagicMock()
            mock_db.close = AsyncMock()
            mock_db_cls.return_value = mock_db

            async for _ in lifespan(fake_app):
                assert fake_app.state.dependencies == mock_deps

            mock_db.close.assert_awaited_once()


class TestExceptionHandlers:
    @pytest.mark.asyncio
    async def test_custom_exception_handler(self):
        mock_request = MagicMock(spec=Request)
        mock_request.state.request_id = "req-12345"

        exc = Custom_Exception(
            message="Test custom exception",
            code=ErrorCode.VALIDATION_ERROR,
            status_code=HttpStatusCode.BAD_REQUEST,
        )

        response = await custom_exception_handler(mock_request, exc)
        assert response.status_code == HttpStatusCode.BAD_REQUEST
        assert exc.request_id == "req-12345"

    @pytest.mark.asyncio
    async def test_validation_exception_handler(self):
        mock_request = MagicMock(spec=Request)
        mock_request.state.request_id = "req-67890"

        raw_errors = [
            {"loc": ("body", "email"), "msg": "value is not a valid email address", "type": "value_error"}
        ]
        val_error = RequestValidationError(errors=raw_errors)

        response = await validation_exception_handler(mock_request, val_error)
        assert response.status_code == HttpStatusCode.UNPROCESSABLE_ENTITY


class TestAppConfiguration:
    def test_app_metadata(self):
        assert app.title == "MCP-Powered Restaurant AI Assistant"
        assert app.version == "1.0.0"

    def test_app_routes_registered(self):
        paths = app.openapi()["paths"]
        assert "/health/live" in paths
        assert "/health/ready" in paths
        assert "/coffee_shop_bot/api/v1/auth/customer/login" in paths
        assert "/coffee_shop_bot/api/v1/user" in paths
        assert "/coffee_shop_bot/api/v1/admin/orders" in paths
