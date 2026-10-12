"""
Tests for MCP_Server/src/utilities/exceptions/error_codes.py

Covers: ErrorCode constants and ErrorCodeStatus mapping completeness.
"""
import sys
import os

SERVER_SRC = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "MCP_Server", "src"
)
if SERVER_SRC not in sys.path:
    sys.path.insert(0, SERVER_SRC)

from utilities.exceptions.error_codes import ErrorCode, ErrorCodeStatus


class TestErrorCode:
    def test_all_constants_are_strings(self):
        for attr in vars(ErrorCode):
            if not attr.startswith("_"):
                assert isinstance(getattr(ErrorCode, attr), str)

    def test_required_codes_exist(self):
        required = [
            "INTERNAL_SERVER_ERROR",
            "DATABASE_ERROR",
            "VALIDATION_ERROR",
            "UNAUTHORIZED",
            "USER_NOT_FOUND",
            "MISSING_ENV_VARS",
        ]
        for code in required:
            assert hasattr(ErrorCode, code), f"ErrorCode.{code} is missing"

    def test_codes_are_non_empty(self):
        for attr in vars(ErrorCode):
            if not attr.startswith("_"):
                assert getattr(ErrorCode, attr).strip() != ""


class TestErrorCodeStatus:
    def test_is_a_dict(self):
        assert isinstance(ErrorCodeStatus, dict)

    def test_all_error_codes_are_mapped(self):
        """Every ErrorCode constant should have a mapping in ErrorCodeStatus."""
        for attr in vars(ErrorCode):
            if not attr.startswith("_"):
                code_value = getattr(ErrorCode, attr)
                assert code_value in ErrorCodeStatus, (
                    f"ErrorCode.{attr} ({code_value!r}) has no mapping in ErrorCodeStatus"
                )

    def test_all_values_are_non_empty_strings(self):
        for key, val in ErrorCodeStatus.items():
            assert isinstance(val, str) and val.strip() != "", (
                f"ErrorCodeStatus[{key!r}] is empty or not a string"
            )
