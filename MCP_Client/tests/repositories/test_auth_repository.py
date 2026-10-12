"""
Tests for MCP_Client/src/repositories/auth_repository.py

Strategy:
  - The AsyncSession is replaced with an AsyncMock so no DB is needed.
  - session.execute() is configured to return a mock result with
    scalar_one_or_none() set to either a fake Customer or None.
"""
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from repositories.auth_repository import AuthRepository
from utilities.exceptions.custom_exception import Custom_Exception


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #
def _make_session(scalar_result=None):
    """Build a minimal async session mock with a configurable execute result."""
    session = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = scalar_result
    session.execute.return_value = execute_result
    session.flush = AsyncMock()
    return session


# --------------------------------------------------------------------------- #
# get_customer_by_email                                                         #
# --------------------------------------------------------------------------- #
class TestGetCustomerByEmail:
    @pytest.mark.asyncio
    async def test_returns_customer_when_found(self, fake_customer):
        session = _make_session(scalar_result=fake_customer)
        repo = AuthRepository()
        result = await repo.get_customer_by_email(session, "alice@example.com")
        assert result is fake_customer

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        session = _make_session(scalar_result=None)
        repo = AuthRepository()
        result = await repo.get_customer_by_email(session, "nobody@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_db_error_raises_custom_exception(self):
        session = AsyncMock()
        session.execute.side_effect = Exception("DB down")
        repo = AuthRepository()
        with pytest.raises(Custom_Exception):
            await repo.get_customer_by_email(session, "a@b.com")


# --------------------------------------------------------------------------- #
# get_customer_by_uuid                                                          #
# --------------------------------------------------------------------------- #
class TestGetCustomerByUuid:
    @pytest.mark.asyncio
    async def test_found(self, fake_customer):
        session = _make_session(scalar_result=fake_customer)
        repo = AuthRepository()
        result = await repo.get_customer_by_uuid(session, str(fake_customer.customer_uuid))
        assert result is fake_customer

    @pytest.mark.asyncio
    async def test_not_found_returns_none(self):
        session = _make_session(scalar_result=None)
        repo = AuthRepository()
        result = await repo.get_customer_by_uuid(session, str(uuid.uuid4()))
        assert result is None

    @pytest.mark.asyncio
    async def test_db_error_raises_custom_exception(self):
        session = AsyncMock()
        session.execute.side_effect = RuntimeError("database unavailable")

        with pytest.raises(Custom_Exception):
            await AuthRepository().get_customer_by_uuid(session, str(uuid.uuid4()))


# --------------------------------------------------------------------------- #
# get_customer_by_refresh_token                                                 #
# --------------------------------------------------------------------------- #
class TestGetCustomerByRefreshToken:
    @pytest.mark.asyncio
    async def test_found(self, fake_customer):
        session = _make_session(scalar_result=fake_customer)
        repo = AuthRepository()
        result = await repo.get_customer_by_refresh_token(session, "hashed-token")
        assert result is fake_customer

    @pytest.mark.asyncio
    async def test_not_found(self):
        session = _make_session(scalar_result=None)
        repo = AuthRepository()
        result = await repo.get_customer_by_refresh_token(session, "unknown")
        assert result is None

    @pytest.mark.asyncio
    async def test_db_error_raises_custom_exception(self):
        session = AsyncMock()
        session.execute.side_effect = RuntimeError("database unavailable")

        with pytest.raises(Custom_Exception):
            await AuthRepository().get_customer_by_refresh_token(session, "token")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "argument"),
    [
        ("get_user_by_email", "admin@example.com"),
        ("get_user_by_uuid", str(uuid.uuid4())),
    ],
)
async def test_user_lookup_methods_return_user_and_wrap_database_errors(
    fake_admin, method_name, argument
):
    repository = AuthRepository()
    session = _make_session(scalar_result=fake_admin)

    assert await getattr(repository, method_name)(session, argument) is fake_admin

    session.execute.side_effect = RuntimeError("database unavailable")
    with pytest.raises(Custom_Exception):
        await getattr(repository, method_name)(session, argument)


# --------------------------------------------------------------------------- #
# save_refresh_token                                                            #
# --------------------------------------------------------------------------- #
class TestSaveRefreshToken:
    @pytest.mark.asyncio
    async def test_sets_token_and_expiry(self, fake_customer):
        session = _make_session()
        expires = datetime.now(timezone.utc) + timedelta(days=7)
        repo = AuthRepository()
        await repo.save_refresh_token(session, fake_customer, "hashed-tok", expires)
        assert fake_customer.refresh_token == "hashed-tok"
        assert fake_customer.expires_at == expires
        assert fake_customer.is_revoked is False
        session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_flush_error_raises_custom_exception(self, fake_customer):
        session = AsyncMock()
        session.flush.side_effect = Exception("flush failed")
        repo = AuthRepository()
        with pytest.raises(Custom_Exception):
            await repo.save_refresh_token(
                session, fake_customer, "tok",
                datetime.now(timezone.utc) + timedelta(days=1)
            )


# --------------------------------------------------------------------------- #
# revoke_refresh_token                                                          #
# --------------------------------------------------------------------------- #
class TestRevokeRefreshToken:
    @pytest.mark.asyncio
    async def test_sets_is_revoked(self, fake_customer):
        session = _make_session()
        repo = AuthRepository()
        await repo.revoke_refresh_token(session, fake_customer)
        assert fake_customer.is_revoked is True
        session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_flush_error_raises_custom_exception(self, fake_customer):
        session = AsyncMock()
        session.flush.side_effect = RuntimeError("flush failed")

        with pytest.raises(Custom_Exception):
            await AuthRepository().revoke_refresh_token(session, fake_customer)


# --------------------------------------------------------------------------- #
# is_refresh_token_valid                                                        #
# --------------------------------------------------------------------------- #
class TestIsRefreshTokenValid:
    def test_valid_token(self, fake_customer):
        result = AuthRepository.is_refresh_token_valid(fake_customer)
        assert result is True

    def test_revoked_token(self, fake_customer):
        fake_customer.is_revoked = True
        result = AuthRepository.is_refresh_token_valid(fake_customer)
        assert result is False

    def test_expired_token(self, fake_customer):
        fake_customer.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        result = AuthRepository.is_refresh_token_valid(fake_customer)
        assert result is False

    def test_none_expiry(self, fake_customer):
        fake_customer.expires_at = None
        result = AuthRepository.is_refresh_token_valid(fake_customer)
        assert result is False

    def test_malformed_expiry_raises_custom_exception(self, fake_customer):
        fake_customer.expires_at = "not-a-datetime"

        with pytest.raises(Custom_Exception):
            AuthRepository.is_refresh_token_valid(fake_customer)
