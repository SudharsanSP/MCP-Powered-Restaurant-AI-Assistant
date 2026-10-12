"""
Tests for MCP_Client/src/utilities/exceptions/error_codes.py

Covers: ErrorCode string constants — existence and type.
"""
import sys
import os

CLIENT_SRC = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "MCP_Client", "src"
)
if CLIENT_SRC not in sys.path:
    sys.path.insert(0, CLIENT_SRC)

from utilities.exceptions.error_codes import ErrorCode


class TestErrorCode:
    def test_all_constants_are_strings(self):
        for attr in vars(ErrorCode):
            if not attr.startswith("_"):
                assert isinstance(getattr(ErrorCode, attr), str), (
                    f"ErrorCode.{attr} is not a string"
                )

    def test_required_codes_exist(self):
        required = [
            "INTERNAL_SERVER_ERROR",
            "DATABASE_ERROR",
            "VALIDATION_ERROR",
            "UNAUTHORIZED",
            "CONFLICT",
            "DATA_NOT_FOUND",
            "INVALID_AUTHORIZATION_HEADER",
        ]
        for code in required:
            assert hasattr(ErrorCode, code), f"ErrorCode.{code} is missing"

    def test_codes_are_non_empty(self):
        for attr in vars(ErrorCode):
            if not attr.startswith("_"):
                assert getattr(ErrorCode, attr).strip() != "", (
                    f"ErrorCode.{attr} is an empty string"
                )
