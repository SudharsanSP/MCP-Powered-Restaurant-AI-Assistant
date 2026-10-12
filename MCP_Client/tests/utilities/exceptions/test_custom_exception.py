"""
Tests for MCP_Client/src/utilities/exceptions/custom_exception.py

Class under test: Custom_Exception
"""
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode


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

    def test_auto_creates_error_list(self):
        """When no errors list is passed, one Error is auto-created from code+message."""
        exc = Custom_Exception("oops", ErrorCode.DATABASE_ERROR, 500)
        assert len(exc.errors) == 1
        assert exc.errors[0].message == "oops"
        assert exc.errors[0].code == ErrorCode.DATABASE_ERROR

    def test_to_api_response_data_is_none(self):
        exc = Custom_Exception("fail", ErrorCode.INTERNAL_SERVER_ERROR, 500)
        response = exc.to_api_response()
        assert response.data == [] or response.data is None

    def test_to_api_response_status_code(self):
        exc = Custom_Exception("fail", ErrorCode.INTERNAL_SERVER_ERROR, 500)
        response = exc.to_api_response()
        assert response.code == 500

    def test_str_representation(self):
        exc = Custom_Exception("test msg", ErrorCode.VALIDATION_ERROR, 422)
        exc.request_id = "req-123"
        result = str(exc)
        assert "test msg" in result
        assert "422" in result

    def test_request_id_defaults_to_none(self):
        exc = Custom_Exception("x", ErrorCode.CONFLICT, 409)
        assert exc.request_id is None
