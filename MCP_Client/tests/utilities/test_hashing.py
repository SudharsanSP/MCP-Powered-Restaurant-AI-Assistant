"""
Tests for MCP_Client/src/utilities/hashing.py

Functions under test:
  - hash_value(value)  → deterministic PBKDF2 hex digest
  - verify_value(value, expected_hash)  → timing-safe comparison
"""
import pytest
from unittest.mock import patch


# --------------------------------------------------------------------------- #
# hash_value                                                                    #
# --------------------------------------------------------------------------- #
class TestHashValue:
    def test_returns_hex_string(self):
        """hash_value must return a non-empty hex string."""
        from utilities.hashing import hash_value
        result = hash_value("mypassword")
        assert isinstance(result, str)
        assert len(result) == 64          # SHA-256 digest = 32 bytes = 64 hex chars

    def test_same_input_same_output(self):
        """Hashing is deterministic: same value → same hash."""
        from utilities.hashing import hash_value
        assert hash_value("hello") == hash_value("hello")

    def test_different_inputs_different_hashes(self):
        """Different values must produce different hashes."""
        from utilities.hashing import hash_value
        assert hash_value("abc") != hash_value("xyz")

    def test_empty_secret_raises_value_error(self):
        """If JWT_SECRET is empty, hash_value should raise ValueError."""
        from utilities.hashing import hash_value
        with patch("utilities.hashing.config") as mock_config:
            mock_config.jwt_secret = ""
            with pytest.raises(ValueError, match="JWT_SECRET must be configured"):
                hash_value("any_value")


# --------------------------------------------------------------------------- #
# verify_value                                                                  #
# --------------------------------------------------------------------------- #
class TestVerifyValue:
    def test_correct_value_returns_true(self):
        """verify_value returns True when value matches the stored hash."""
        from utilities.hashing import hash_value, verify_value
        h = hash_value("secret")
        assert verify_value("secret", h) is True

    def test_wrong_value_returns_false(self):
        """verify_value returns False for a mismatched value."""
        from utilities.hashing import hash_value, verify_value
        h = hash_value("secret")
        assert verify_value("wrong", h) is False

    def test_none_hash_returns_false(self):
        """verify_value must safely return False when hash is None."""
        from utilities.hashing import verify_value
        assert verify_value("anything", None) is False

    def test_empty_hash_returns_false(self):
        """verify_value must safely return False when hash is empty string."""
        from utilities.hashing import verify_value
        assert verify_value("anything", "") is False
