"""
Tests for MCP_Client/src/utilities/tokens.py

Functions under test:
  - create_access_token(customer_uuid, role)
"""
import uuid
import pytest
import jwt
from unittest.mock import patch, MagicMock


class TestCreateAccessToken:
    def test_returns_decodable_jwt(self):
        """create_access_token returns a JWT that can be decoded with the same secret."""
        from utilities.tokens import create_access_token

        with patch("utilities.tokens.config") as mock_config:
            mock_config.jwt_secret = "test-secret"
            mock_config.access_token_expire_minutes = 30

            token = create_access_token("some-uuid", "user")

        decoded = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert decoded["user_uuid"] == "some-uuid"
        assert decoded["role"] == "user"

    def test_token_contains_required_claims(self):
        """JWT payload must carry user_uuid, role, iat, and exp."""
        from utilities.tokens import create_access_token

        with patch("utilities.tokens.config") as mock_config:
            mock_config.jwt_secret = "test-secret"
            mock_config.access_token_expire_minutes = 30

            token = create_access_token(str(uuid.uuid4()), "user")

        decoded = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert all(key in decoded for key in ("user_uuid", "role", "iat", "exp"))

    def test_exp_is_in_future(self):
        """The exp claim must be in the future."""
        from utilities.tokens import create_access_token
        from datetime import datetime, timezone

        with patch("utilities.tokens.config") as mock_config:
            mock_config.jwt_secret = "test-secret"
            mock_config.access_token_expire_minutes = 30

            token = create_access_token(str(uuid.uuid4()), "user")

        decoded = jwt.decode(token, "test-secret", algorithms=["HS256"])
        now = int(datetime.now(timezone.utc).timestamp())
        assert decoded["exp"] > now

    def test_jwt_exception_raises_custom_exception(self):
        """If jwt.encode raises, create_access_token wraps it in Custom_Exception."""
        from utilities.tokens import create_access_token
        from utilities.exceptions.custom_exception import Custom_Exception

        with patch("utilities.tokens.config") as mock_config:
            mock_config.jwt_secret = "test-secret"
            mock_config.access_token_expire_minutes = 30
            with patch("utilities.tokens.jwt.encode", side_effect=Exception("jwt exploded")):
                with pytest.raises(Custom_Exception):
                    create_access_token("uuid", "user")
