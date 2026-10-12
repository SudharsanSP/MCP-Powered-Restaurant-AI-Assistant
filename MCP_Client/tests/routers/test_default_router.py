"""
Tests for MCP_Client/src/routers/default_router.py
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from routers.default_router import router


@pytest.fixture
def test_app():
    app = FastAPI()
    app.include_router(router)
    return app


class TestDefaultRouter:
    @pytest.mark.asyncio
    async def test_liveness_endpoint(self, test_app):
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            response = await ac.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_readiness_endpoint_ready(self, test_app):
        test_app.state.dependencies = {"ready": True}
        with patch("routers.default_router.test_connection", new_callable=AsyncMock) as mock_conn:
            mock_conn.return_value = True
            async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
                response = await ac.get("/health/ready")
            assert response.status_code == 200
            assert response.json() == {"status": "ready"}

    @pytest.mark.asyncio
    async def test_readiness_endpoint_not_ready_when_no_dependencies(self, test_app):
        test_app.state.dependencies = None
        with patch("routers.default_router.test_connection", new_callable=AsyncMock) as mock_conn:
            mock_conn.return_value = True
            async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
                response = await ac.get("/health/ready")
            assert response.status_code == 503
            assert response.json() == {"status": "not_ready"}
