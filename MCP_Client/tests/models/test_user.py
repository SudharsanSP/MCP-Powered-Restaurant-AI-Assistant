"""
Tests for MCP_Client/src/models/user.py
"""
import pytest
from pydantic import ValidationError

from models.user import UserCreateRequest, UserCreateResponse


class TestUserModels:
    def test_user_create_request_valid(self):
        req = UserCreateRequest(
            name="Alice",
            phone_number="9876543210",
            email="alice@example.com",
            password="password123",
        )
        assert req.name == "Alice"
        assert req.phone_number == "9876543210"

    def test_user_create_request_invalid_phone_letters(self):
        with pytest.raises(ValidationError):
            UserCreateRequest(
                name="Alice",
                phone_number="987654321a",
                email="alice@example.com",
                password="password123",
            )

    def test_user_create_request_short_phone(self):
        with pytest.raises(ValidationError):
            UserCreateRequest(
                name="Alice",
                phone_number="12345",
                email="alice@example.com",
                password="password123",
            )

    def test_user_create_request_short_password(self):
        with pytest.raises(ValidationError):
            UserCreateRequest(
                name="Alice",
                phone_number="9876543210",
                email="alice@example.com",
                password="short",
            )

    def test_user_create_response(self):
        resp = UserCreateResponse(
            customer_uuid="cust-uuid",
            access_token="tok1",
            refresh_token="tok2",
            expires_in=1800,
        )
        assert resp.customer_uuid == "cust-uuid"
        assert resp.expires_in == 1800
