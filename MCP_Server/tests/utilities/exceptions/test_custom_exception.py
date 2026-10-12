"""
Tests for MCP_Server/src/utilities/exceptions/custom_exception.py

Class under test: Custom_Exception (server version)

Key differences from the client version:
  - request_id is auto-generated via uuid.uuid4() — never None
  - Provides a classmethod from_errors() for building from a list of Error objects
"""
import sys
import os

SERVER_SRC = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "MCP_Server", "src"
)
if SERVER_SRC not in sys.path:
    sys.path.insert(0, SERVER_SRC)

import uuid
import pytest

from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from models.APIresponse import Error


class TestCustomException:
    def test_inherits_from_exception(self):
        exc = Custom_Exception("fail", ErrorCode.INTERNAL_SERVER_ERROR, 500)
        assert isinstance(exc, Exception)

    def test_message_stored(self):
        exc = Custom_Exception("something broke", ErrorCode.VALIDATION_ERROR, 400)
        assert exc.message == "something broke"

    def test_code_stored(self):
        exc = Custom_Exception("bad", ErrorCode.UNAUTHORIZED, 401)
        assert exc.code == ErrorCode.UNAUTHORIZED

    def test_status_code_stored(self):
        exc = Custom_Exception("bad", ErrorCode.UNAUTHORIZED, HttpStatusCode.UNAUTHORIZED)
        assert exc.status_code == HttpStatusCode.UNAUTHORIZED

    def test_request_id_auto_generated(self):
        """Server version always generates a UUID — it is never None."""
        exc = Custom_Exception("err", ErrorCode.DATABASE_ERROR, 500)
        assert exc.request_id is not None
        # Must be a valid UUID string
        uuid.UUID(exc.request_id)

    def test_request_id_unique_per_instance(self):
        """Each exception instance should have a distinct request_id."""
        exc1 = Custom_Exception("a", ErrorCode.INTERNAL_SERVER_ERROR, 500)
        exc2 = Custom_Exception("b", ErrorCode.INTERNAL_SERVER_ERROR, 500)
        assert exc1.request_id != exc2.request_id

    def test_auto_creates_error_list(self):
        """When no errors list passed, one Error is created from code+message."""
        exc = Custom_Exception("oops", ErrorCode.DATABASE_ERROR, 500)
        assert len(exc.errors) == 1
        assert exc.errors[0].message == "oops"
        assert exc.errors[0].code == ErrorCode.DATABASE_ERROR

    def test_custom_errors_list_used(self):
        errors = [Error(code="E1", message="err one"), Error(code="E2", message="err two")]
        exc = Custom_Exception("multi", ErrorCode.VALIDATION_ERROR, 400, errors=errors)
        assert len(exc.errors) == 2
        assert exc.errors[0].code == "E1"

    def test_to_api_response_no_data(self):
        exc = Custom_Exception("fail", ErrorCode.INTERNAL_SERVER_ERROR, 500)
        response = exc.to_api_response()
        assert response.data == [] or response.data is None

    def test_to_api_response_status_code(self):
        exc = Custom_Exception("fail", ErrorCode.INTERNAL_SERVER_ERROR, 500)
        response = exc.to_api_response()
        assert response.code == 500

    def test_str_representation_includes_message_and_status(self):
        exc = Custom_Exception("test msg", ErrorCode.VALIDATION_ERROR, 422)
        result = str(exc)
        assert "test msg" in result
        assert "422" in result


class TestFromErrors:
    def test_creates_exception_from_error_list(self):
        errors = [
            Error(code=ErrorCode.VALIDATION_ERROR, message="field required"),
            Error(code=ErrorCode.VALIDATION_ERROR, message="must be positive"),
        ]
        exc = Custom_Exception.from_errors(errors, 400)
        assert exc.message == "field required"
        assert exc.status_code == 400
        assert len(exc.errors) == 2

    def test_first_error_used_for_top_level_code(self):
        errors = [Error(code="CODE_A", message="first"), Error(code="CODE_B", message="second")]
        exc = Custom_Exception.from_errors(errors, 422)
        assert exc.code == "CODE_A"

    def test_empty_errors_list_returns_unknown_error(self):
        exc = Custom_Exception.from_errors([], 500)
        assert exc.message == "Unknown error occurred"
        assert exc.status_code == 500
