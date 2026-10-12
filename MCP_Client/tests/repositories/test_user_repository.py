"""
Tests for MCP_Client/src/repositories/user_repository.py

Functions under test:
  - find_by_email_or_phone
  - create_user
"""
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from repositories.user_repository import UserRepository
from utilities.exceptions.custom_exception import Custom_Exception


def _make_session(scalar_result=None):
    session = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = scalar_result
    session.execute.return_value = execute_result
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


class TestFindByEmailOrPhone:
    @pytest.mark.asyncio
    async def test_returns_existing_customer(self, fake_customer):
        session = _make_session(scalar_result=fake_customer)
        repo = UserRepository()
        result = await repo.find_by_email_or_phone(
            session, "alice@example.com", "9876543210"
        )
        assert result is fake_customer

    @pytest.mark.asyncio
    async def test_returns_none_when_no_match(self):
        session = _make_session(scalar_result=None)
        repo = UserRepository()
        result = await repo.find_by_email_or_phone(
            session, "new@example.com", "1234567890"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_db_error_raises_custom_exception(self):
        session = AsyncMock()
        session.execute.side_effect = Exception("DB error")
        repo = UserRepository()
        with pytest.raises(Custom_Exception):
            await repo.find_by_email_or_phone(session, "x@x.com", "9999999999")


class TestCreateUser:
    @pytest.mark.asyncio
    async def test_adds_customer_to_session(self):
        session = _make_session()
        repo = UserRepository()
        expires = datetime.now(timezone.utc) + timedelta(days=7)
        result = await repo.create_user(
            session=session,
            customer_uuid=str(uuid.uuid4()),
            name="Alice",
            phone_number="+91 9876543210",
            email="alice@example.com",
            password_hash="hashed",
            refresh_token_hash="refresh-hashed",
            expires_at=expires,
        )
        # session.add must have been called with a Customer object
        session.add.assert_called_once()
        session.flush.assert_called_once()
        # result is the Customer instance that was added
        assert result is not None

    @pytest.mark.asyncio
    async def test_flush_error_raises_custom_exception(self):
        session = AsyncMock()
        session.add = MagicMock()
        session.flush.side_effect = Exception("flush failed")
        repo = UserRepository()
        with pytest.raises(Custom_Exception):
            await repo.create_user(
                session=session,
                customer_uuid=str(uuid.uuid4()),
                name="Bob",
                phone_number="+91 9876543210",
                email="bob@example.com",
                password_hash="h",
                refresh_token_hash="r",
                expires_at=datetime.now(timezone.utc),
            )
