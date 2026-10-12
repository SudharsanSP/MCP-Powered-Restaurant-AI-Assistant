"""
Tests for MCP_Client/src/middleware/context.py (ContextMiddleware)

Uses FastAPI's TestClient with httpx to fire requests through the middleware.
"""
import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import AsyncClient, ASGITransport

from middleware.context import ContextMiddleware


def _app_with_middleware():
    app = FastAPI()
    app.add_middleware(ContextMiddleware)

    @app.get("/ping")
    async def ping():
        return JSONResponse({"ok": True})

    return app


class TestContextMiddleware:
    @pytest.mark.asyncio
    async def test_echoes_request_id_header(self):
        app = _app_with_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/ping", headers={"X-Request-ID": "req-abc"})
        assert resp.headers.get("x-request-id") == "req-abc"

    @pytest.mark.asyncio
    async def test_empty_request_id_forwarded_as_empty(self):
        app = _app_with_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/ping")
        # Header should still be present (possibly empty)
        assert "x-request-id" in resp.headers

    @pytest.mark.asyncio
    async def test_request_returns_200(self):
        app = _app_with_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/ping", headers={"X-Request-ID": "id-1"})
        assert resp.status_code == 200
