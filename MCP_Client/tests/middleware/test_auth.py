"""
Tests for MCP_Client/src/middleware/auth.py (AuthMiddleware + check_user_rbac)

Strategy:
  - Build a minimal FastAPI app, mount AuthMiddleware on it.
  - Patch get_db_session and AuthRepository so no real DB is touched.
  - Drive requests through httpx AsyncClient.
"""
import uuid
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import jwt
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import AsyncClient, ASGITransport

from middleware.auth import AuthMiddleware, check_user_rbac
from middleware.context import ContextMiddleware


# --------------------------------------------------------------------------- #
# Minimal app fixture                                                           #
# --------------------------------------------------------------------------- #
def _build_app(mock_customer=None):
    app = FastAPI()
    app.add_middleware(AuthMiddleware)
    app.add_middleware(ContextMiddleware)

    @app.get("/protected")
    async def protected():
        return JSONResponse({"secret": True})

    @app.get("/health/live")
    async def live():
        return JSONResponse({"status": "ok"})

    return app


def _make_jwt(customer_uuid, role="user", secret="test-secret", expired=False):
    from datetime import timedelta
    import jwt as pyjwt
    now = datetime.now(timezone.utc)
    if expired:
        exp = now - timedelta(minutes=5)
    else:
        exp = now + timedelta(minutes=30)
    return pyjwt.encode(
        {"user_uuid": str(customer_uuid), "role": role, "iat": now, "exp": exp},
        secret,
        algorithm="HS256",
    )


class TestPublicPaths:
    @pytest.mark.asyncio
    async def test_health_live_no_auth_needed(self):
        app = _build_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/health/live")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_options_preflight_bypasses_auth(self):
        app = _build_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.options("/protected")
        # OPTIONS should not be blocked by auth (CORS preflight)
        assert resp.status_code != 401


class TestMissingToken:
    @pytest.mark.asyncio
    async def test_no_authorization_header_returns_401(self):
        app = _build_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/protected")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_malformed_bearer_returns_401(self):
        app = _build_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/protected", headers={"Authorization": "NotBearer token"})
        assert resp.status_code == 401


class TestExpiredToken:
    @pytest.mark.asyncio
    async def test_expired_jwt_returns_401(self):
        app = _build_app()
        token = _make_jwt(uuid.uuid4(), expired=True)

        with patch("middleware.auth.config") as mock_cfg:
            mock_cfg.jwt_secret = "test-secret"
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get(
                    "/protected",
                    headers={"Authorization": f"Bearer {token}"},
                )
        assert resp.status_code == 401


class TestValidToken:
    @pytest.mark.asyncio
    async def test_valid_token_with_valid_customer_returns_200(self, fake_customer):
        app = _build_app()
        customer_uuid = fake_customer.customer_uuid
        token = _make_jwt(customer_uuid)

        async def _db_gen():
            yield AsyncMock()

        with patch("middleware.auth.config") as mock_cfg, \
             patch("middleware.auth.get_db_session", return_value=_db_gen()), \
             patch("middleware.auth.AuthRepository") as MockRepo:

            mock_cfg.jwt_secret = "test-secret"
            instance = MockRepo.return_value
            instance.get_customer_by_uuid = AsyncMock(return_value=fake_customer)

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get(
                    "/protected",
                    headers={"Authorization": f"Bearer {token}"},
                )

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_valid_token_unknown_customer_returns_403(self):
        app = _build_app()
        token = _make_jwt(uuid.uuid4())

        async def _db_gen():
            yield AsyncMock()

        with patch("middleware.auth.config") as mock_cfg, \
             patch("middleware.auth.get_db_session", return_value=_db_gen()), \
             patch("middleware.auth.AuthRepository") as MockRepo:

            mock_cfg.jwt_secret = "test-secret"
            instance = MockRepo.return_value
            instance.get_customer_by_uuid = AsyncMock(return_value=None)   # not found

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get(
                    "/protected",
                    headers={"Authorization": f"Bearer {token}"},
                )

        assert resp.status_code == 403


class TestCheckUserRbac:
    @pytest.mark.asyncio
    async def test_missing_identity_is_rejected(self):
        request = SimpleNamespace(state=SimpleNamespace(request_id="request-1"))

        allowed, message = await check_user_rbac({"role": "user"}, request)

        assert not allowed
        assert "no user identity" in message

    @pytest.mark.asyncio
    async def test_customer_with_wrong_role_is_rejected(self, fake_customer):
        fake_customer.role = "admin"
        request = SimpleNamespace(state=SimpleNamespace(request_id="request-1"))

        async def _db_gen():
            yield AsyncMock()

        with patch("middleware.auth.get_db_session", return_value=_db_gen()), \
             patch("middleware.auth.AuthRepository") as repo_class:
            repo_class.return_value.get_customer_by_uuid = AsyncMock(
                return_value=fake_customer
            )
            allowed, message = await check_user_rbac(
                {"user_uuid": str(fake_customer.customer_uuid), "role": "user"},
                request,
            )

        assert not allowed
        assert "not authorized" in message

    @pytest.mark.asyncio
    async def test_admin_with_valid_role_is_authorized(self, fake_admin):
        request = SimpleNamespace(state=SimpleNamespace(request_id="request-1"))

        async def _db_gen():
            yield AsyncMock()

        with patch("middleware.auth.get_db_session", return_value=_db_gen()), \
             patch("middleware.auth.AuthRepository") as repo_class:
            repo_class.return_value.get_user_by_uuid = AsyncMock(
                return_value=fake_admin
            )
            allowed, message = await check_user_rbac(
                {"user_uuid": str(fake_admin.user_uuid), "role": "admin"},
                request,
            )

        assert allowed
        assert message is None
        assert request.state.user_role == "admin"

    @pytest.mark.asyncio
    async def test_admin_not_found_is_rejected(self):
        request = SimpleNamespace(state=SimpleNamespace(request_id="request-1"))

        async def _db_gen():
            yield AsyncMock()

        with patch("middleware.auth.get_db_session", return_value=_db_gen()), \
             patch("middleware.auth.AuthRepository") as repo_class:
            repo_class.return_value.get_user_by_uuid = AsyncMock(return_value=None)
            allowed, message = await check_user_rbac(
                {"user_uuid": str(uuid.uuid4()), "role": "admin"},
                request,
            )

        assert not allowed
        assert "admin identity" in message

    @pytest.mark.asyncio
    async def test_database_error_is_rejected(self):
        request = SimpleNamespace(state=SimpleNamespace(request_id="request-1"))

        async def _db_gen():
            yield AsyncMock()

        with patch("middleware.auth.get_db_session", return_value=_db_gen()), \
             patch("middleware.auth.AuthRepository") as repo_class:
            repo_class.return_value.get_user_by_uuid = AsyncMock(
                side_effect=RuntimeError("database unavailable")
            )
            allowed, message = await check_user_rbac(
                {"user_uuid": str(uuid.uuid4()), "role": "admin"},
                request,
            )

        assert not allowed
        assert message == "Authorization could not be completed."


class TestInvalidToken:
    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self):
        app = _build_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/protected", headers={"Authorization": "Bearer not-a-jwt"}
            )

        assert response.status_code == 401
        assert response.json()["message"] == "The authentication token is invalid."

    @pytest.mark.asyncio
    async def test_unexpected_rbac_error_returns_500(self):
        app = _build_app()
        token = _make_jwt(uuid.uuid4())

        with patch("middleware.auth.config") as mock_config, \
             patch(
                 "middleware.auth.check_user_rbac",
                 side_effect=RuntimeError("authorization failure"),
             ):
            mock_config.jwt_secret = "test-secret"
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(
                    "/protected",
                    headers={"Authorization": f"Bearer {token}"},
                )

        assert response.status_code == 500
        assert response.json()["message"] == "Authentication could not be completed."
