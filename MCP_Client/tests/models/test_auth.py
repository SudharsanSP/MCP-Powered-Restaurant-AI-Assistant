"""
Tests for MCP_Client/src/models/auth.py
"""
import pytest
from pydantic import ValidationError

from models.auth import (
    LoginRequest,
    RefreshRequest,
    LogoutRequest,
    CustomerLoginResponse,
    AdminLoginResponse,
    RefreshResponse,
    LogoutResponse,
)


class TestAuthModels:
    def test_login_request_valid(self):
        req = LoginRequest(email="user@test.com", password="password123")
        assert req.email == "user@test.com"
        assert req.password == "password123"

    def test_login_request_invalid_email(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="invalid_email", password="password123")

    def test_login_request_short_password(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="user@test.com", password="short")

    def test_refresh_request_valid(self):
        req = RefreshRequest(refresh_token="a" * 32)
        assert len(req.refresh_token) == 32

    def test_refresh_request_too_short(self):
        with pytest.raises(ValidationError):
            RefreshRequest(refresh_token="short")

    def test_logout_request_valid(self):
        req = LogoutRequest(refresh_token="b" * 32)
        assert len(req.refresh_token) == 32

    def test_responses_instantiation(self):
        c_resp = CustomerLoginResponse(access_token="tok1", refresh_token="tok2", expires_in=1800)
        assert c_resp.expires_in == 1800

        a_resp = AdminLoginResponse(access_token="tok1", expires_in=1800)
        assert a_resp.access_token == "tok1"

        r_resp = RefreshResponse(access_token="tok1", expires_in=1800)
        assert r_resp.access_token == "tok1"

        l_resp = LogoutResponse(message="Success")
        assert l_resp.message == "Success"
