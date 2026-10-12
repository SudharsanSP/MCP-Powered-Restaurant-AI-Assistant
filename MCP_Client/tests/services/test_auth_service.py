"""
Tests for MCP_Client/src/services/auth_service.py

Strategy:
  - Patch get_db_session to yield a mock session.
  - Inject a mock AuthRepository into the service.
  - Patch hash_value / verify_value / create_access_token as needed.

Functions under test:
  - AuthService.customer_login  (or login, depending on method name)
  - AuthService.refresh
  - AuthService.logout
"""
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager

import pytest

from services.auth_service import AuthService
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from models.auth import LoginRequest, RefreshRequest, LogoutRequest


# --------------------------------------------------------------------------- #
# Helper: make get_db_session yield a mock session                              #
# --------------------------------------------------------------------------- #
def _patch_db(mock_session):
    """Return a context-manager patch that makes get_db_session yield mock_session."""
    async def _gen():
        yield mock_session
    return patch("services.auth_service.get_db_session", return_value=_gen())


# --------------------------------------------------------------------------- #
# customer_login / admin_login                                                  #
# --------------------------------------------------------------------------- #
class TestCustomerLogin:
    @pytest.mark.asyncio
    async def test_successful_login(self, fake_customer):
        from utilities.hashing import hash_value
        fake_customer.password_hash = hash_value("password123")

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        mock_repo = AsyncMock()
        mock_repo.get_customer_by_email.return_value = fake_customer
        mock_repo.save_refresh_token = AsyncMock()

        async def _gen():
            yield mock_session

        service = AuthService()
        service.repository = mock_repo

        with patch("services.auth_service.get_db_session", return_value=_gen()):
            result = await service.customer_login(
                LoginRequest(email="alice@example.com", password="password123")
            )

        assert result.access_token
        assert result.refresh_token
        assert result.expires_in > 0

    @pytest.mark.asyncio
    async def test_wrong_password_raises_unauthorized(self, fake_customer):
        from utilities.hashing import hash_value
        fake_customer.password_hash = hash_value("correct-password")

        mock_session = AsyncMock()
        mock_session.rollback = AsyncMock()

        mock_repo = AsyncMock()
        mock_repo.get_customer_by_email.return_value = fake_customer

        async def _gen():
            yield mock_session

        service = AuthService()
        service.repository = mock_repo

        with patch("services.auth_service.get_db_session", return_value=_gen()):
            with pytest.raises(Custom_Exception) as exc_info:
                await service.customer_login(
                    LoginRequest(email="alice@example.com", password="wrong-password")
                )
        assert exc_info.value.status_code == HttpStatusCode.UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_customer_not_found_raises_unauthorized(self):
        mock_session = AsyncMock()
        mock_session.rollback = AsyncMock()

        mock_repo = AsyncMock()
        mock_repo.get_customer_by_email.return_value = None   # not found

        async def _gen():
            yield mock_session

        service = AuthService()
        service.repository = mock_repo

        with patch("services.auth_service.get_db_session", return_value=_gen()):
            with pytest.raises(Custom_Exception) as exc_info:
                await service.customer_login(
                    LoginRequest(email="nobody@x.com", password="password123")
                )
        assert exc_info.value.status_code == HttpStatusCode.UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_repository_error_is_wrapped(self):
        session = AsyncMock()
        repository = AsyncMock()
        repository.get_customer_by_email.side_effect = RuntimeError("database unavailable")
        service = AuthService()
        service.repository = repository

        with _patch_db(session), pytest.raises(Custom_Exception) as exc_info:
            await service.customer_login(
                LoginRequest(email="alice@example.com", password="password123")
            )

        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR
        session.rollback.assert_awaited_once()


class TestAdminLogin:
    @pytest.mark.asyncio
    async def test_successful_login(self, fake_admin):
        from utilities.hashing import hash_value

        fake_admin.password_hash = hash_value("admin-password")
        session = AsyncMock()
        repository = AsyncMock()
        repository.get_user_by_email.return_value = fake_admin
        service = AuthService()
        service.repository = repository

        with _patch_db(session):
            result = await service.admin_login(
                LoginRequest(email="admin@example.com", password="admin-password")
            )

        assert result.access_token
        assert result.expires_in > 0
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invalid_credentials_roll_back(self, fake_admin):
        from utilities.hashing import hash_value

        fake_admin.password_hash = hash_value("correct-password")
        session = AsyncMock()
        repository = AsyncMock()
        repository.get_user_by_email.return_value = fake_admin
        service = AuthService()
        service.repository = repository

        with _patch_db(session), pytest.raises(Custom_Exception) as exc_info:
            await service.admin_login(
                LoginRequest(email="admin@example.com", password="wrong-password")
            )

        assert exc_info.value.status_code == HttpStatusCode.UNAUTHORIZED
        session.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_repository_error_is_wrapped(self):
        session = AsyncMock()
        repository = AsyncMock()
        repository.get_user_by_email.side_effect = RuntimeError("database unavailable")
        service = AuthService()
        service.repository = repository

        with _patch_db(session), pytest.raises(Custom_Exception) as exc_info:
            await service.admin_login(
                LoginRequest(email="admin@example.com", password="password123")
            )

        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR
        session.rollback.assert_awaited_once()


# --------------------------------------------------------------------------- #
# refresh                                                                       #
# --------------------------------------------------------------------------- #
class TestRefresh:
    @pytest.mark.asyncio
    async def test_valid_token_returns_new_access_token(self, fake_customer):
        mock_session = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_customer_by_refresh_token.return_value = fake_customer

        async def _gen():
            yield mock_session

        service = AuthService()
        service.repository = mock_repo

        with patch("services.auth_service.get_db_session", return_value=_gen()):
            with patch("services.auth_service.AuthRepository.is_refresh_token_valid", return_value=True):
                result = await service.refresh(RefreshRequest(refresh_token="a" * 64))

        assert result.access_token
        assert result.expires_in > 0

    @pytest.mark.asyncio
    async def test_invalid_token_raises_unauthorized(self):
        mock_session = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_customer_by_refresh_token.return_value = None   # token unknown

        async def _gen():
            yield mock_session

        service = AuthService()
        service.repository = mock_repo

        with patch("services.auth_service.get_db_session", return_value=_gen()):
            with pytest.raises(Custom_Exception) as exc_info:
                await service.refresh(RefreshRequest(refresh_token="b" * 64))
        assert exc_info.value.status_code == HttpStatusCode.UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_expired_token_raises_unauthorized(self, fake_customer):
        from repositories.auth_repository import AuthRepository

        fake_customer.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        session = AsyncMock()
        repository = AuthRepository()
        repository.get_customer_by_refresh_token = AsyncMock(
            return_value=fake_customer
        )
        service = AuthService()
        service.repository = repository

        with _patch_db(session), pytest.raises(Custom_Exception) as exc_info:
            await service.refresh(RefreshRequest(refresh_token="e" * 64))

        assert exc_info.value.status_code == HttpStatusCode.UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_repository_error_is_wrapped(self):
        session = AsyncMock()
        repository = AsyncMock()
        repository.get_customer_by_refresh_token.side_effect = RuntimeError(
            "database unavailable"
        )
        service = AuthService()
        service.repository = repository

        with _patch_db(session), pytest.raises(Custom_Exception) as exc_info:
            await service.refresh(RefreshRequest(refresh_token="f" * 64))

        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR


# --------------------------------------------------------------------------- #
# logout                                                                        #
# --------------------------------------------------------------------------- #
class TestLogout:
    @pytest.mark.asyncio
    async def test_existing_token_is_revoked(self, fake_customer):
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_customer_by_refresh_token.return_value = fake_customer
        mock_repo.revoke_refresh_token = AsyncMock()

        async def _gen():
            yield mock_session

        service = AuthService()
        service.repository = mock_repo

        with patch("services.auth_service.get_db_session", return_value=_gen()):
            result = await service.logout(LogoutRequest(refresh_token="c" * 64))

        mock_repo.revoke_refresh_token.assert_called_once()
        assert "success" in result.message.lower() or result.message

    @pytest.mark.asyncio
    async def test_unknown_token_raises_unauthorized(self):
        """Logout with an unknown/already-revoked token raises Custom_Exception."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_customer_by_refresh_token.return_value = None

        async def _gen():
            yield mock_session

        service = AuthService()
        service.repository = mock_repo

        with patch("services.auth_service.get_db_session", return_value=_gen()):
            with pytest.raises(Custom_Exception) as exc_info:
                await service.logout(LogoutRequest(refresh_token="d" * 64))

        assert exc_info.value.status_code == HttpStatusCode.UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_revoked_token_raises_unauthorized(self, fake_customer):
        fake_customer.is_revoked = True
        session = AsyncMock()
        repository = AsyncMock()
        repository.get_customer_by_refresh_token.return_value = fake_customer
        service = AuthService()
        service.repository = repository

        with _patch_db(session), pytest.raises(Custom_Exception) as exc_info:
            await service.logout(LogoutRequest(refresh_token="g" * 64))

        assert exc_info.value.status_code == HttpStatusCode.UNAUTHORIZED
        session.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_repository_error_is_wrapped(self):
        session = AsyncMock()
        repository = AsyncMock()
        repository.get_customer_by_refresh_token.side_effect = RuntimeError(
            "database unavailable"
        )
        service = AuthService()
        service.repository = repository

        with _patch_db(session), pytest.raises(Custom_Exception) as exc_info:
            await service.logout(LogoutRequest(refresh_token="h" * 64))

        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR
        session.rollback.assert_awaited_once()
