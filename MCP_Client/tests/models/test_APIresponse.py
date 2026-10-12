"""
Tests for MCP_Client/src/models/APIresponse.py
"""
import pytest
from models.APIresponse import APIResponse, Error


class TestClientError:
    def test_stores_code_and_message(self):
        e = Error(code="E100", message="Something broke")
        assert e.code == "E100"
        assert e.message == "Something broke"

    def test_to_dict(self):
        e = Error(code="E101", message="Invalid input")
        d = e.to_dict()
        assert d == {"code": "E101", "message": "Invalid input"}


class TestClientAPIResponse:
    def test_default_message_success(self):
        r = APIResponse(data={"key": "value"}, code=200, request_id="req-1")
        assert r.message == "Success"
        assert r.request_id == "req-1"

    def test_single_error_message(self):
        err = Error(code="E1", message="Only one error")
        r = APIResponse(errors=[err], code=400)
        assert r.message == "Only one error"

    def test_multiple_errors_generic_message(self):
        errors = [Error("E1", "first"), Error("E2", "second")]
        r = APIResponse(errors=errors, code=400)
        assert r.message == "Something went wrong."

    def test_custom_message(self):
        r = APIResponse(message="Custom message", code=200)
        assert r.message == "Custom message"

    def test_to_dict(self):
        err = Error(code="E1", message="Fail")
        r = APIResponse(data="sample", errors=[err], code=400, request_id="id-1")
        d = r.to_dict()
        assert d["data"] == "sample"
        assert d["status_code"] == 400
        assert d["request_id"] == "id-1"
        assert len(d["errors"]) == 1
        assert d["errors"][0]["code"] == "E1"
