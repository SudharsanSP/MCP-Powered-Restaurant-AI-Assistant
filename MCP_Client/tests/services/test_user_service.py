"""
Tests for MCP_Client/src/services/user_service.py

Functions under test:
  - UserService.create_user
"""
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.user_service import UserService
from models.user import UserCreateRequest
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.http_status import HttpStatusCode


VALID_PAYLOAD = UserCreateRequest(
    name="Alice",
    phone_number="9876543210",
    email="alice@example.com",
    password="password123",
)


def _build_service(existing_customer=None, created_customer=None):
    """Helper: wires a UserService with a mocked repository."""
    if created_customer is None:
        created_customer = MagicMock()
        created_customer.customer_uuid = uuid.uuid4()
        created_customer.role = "user"

    mock_repo = AsyncMock()
    mock_repo.find_by_email_or_phone.return_value = existing_customer
    mock_repo.create_user.return_value = created_customer

    service = UserService()
    service.repository = mock_repo
    return service, mock_repo


class TestCreateUser:
    @pytest.mark.asyncio
    async def test_successful_creation_returns_response(self):
        mock_customer = MagicMock()
        mock_customer.customer_uuid = uuid.uuid4()
        mock_customer.role = "user"

        service, _ = _build_service(existing_customer=None, created_customer=mock_customer)

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        async def _gen():
            yield mock_session

        with patch("services.user_service.get_db_session", return_value=_gen()):
            result = await service.create_user(VALID_PAYLOAD)

        assert result.customer_uuid == str(mock_customer.customer_uuid)
        assert result.access_token
        assert result.refresh_token
        assert result.expires_in > 0

    @pytest.mark.asyncio
    async def test_duplicate_email_raises_conflict(self, fake_customer):
        """If find_by_email_or_phone returns an existing user, raise 409."""
        service, _ = _build_service(existing_customer=fake_customer)

        mock_session = AsyncMock()
        mock_session.rollback = AsyncMock()

        async def _gen():
            yield mock_session

        with patch("services.user_service.get_db_session", return_value=_gen()):
            with pytest.raises(Custom_Exception) as exc_info:
                await service.create_user(VALID_PAYLOAD)

        assert exc_info.value.status_code == HttpStatusCode.CONFLICT

    @pytest.mark.asyncio
    async def test_db_error_during_creation_raises_500(self):
        mock_session = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_repo = AsyncMock()
        mock_repo.find_by_email_or_phone.return_value = None
        mock_repo.create_user.side_effect = Exception("unexpected DB error")

        service = UserService()
        service.repository = mock_repo

        async def _gen():
            yield mock_session

        with patch("services.user_service.get_db_session", return_value=_gen()):
            with pytest.raises(Custom_Exception) as exc_info:
                await service.create_user(VALID_PAYLOAD)

        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_email_stored_as_lowercase(self):
        """Email in payload should be lowercased before saving."""
        mock_customer = MagicMock()
        mock_customer.customer_uuid = uuid.uuid4()
        mock_customer.role = "user"

        service, mock_repo = _build_service(
            existing_customer=None, created_customer=mock_customer
        )

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        async def _gen():
            yield mock_session

        payload = UserCreateRequest(
            name="Alice", phone_number="9876543210",
            email="Alice@EXAMPLE.COM", password="password123"
        )

        with patch("services.user_service.get_db_session", return_value=_gen()):
            await service.create_user(payload)

        call_kwargs = mock_repo.create_user.call_args.kwargs
        assert call_kwargs["email"] == "alice@example.com"
