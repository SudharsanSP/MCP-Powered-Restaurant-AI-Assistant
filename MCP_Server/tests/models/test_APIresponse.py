"""
Tests for MCP_Server/src/models/APIresponse.py
"""
import uuid
import pytest
from models.APIresponse import APIResponse, Error


class TestError:
    def test_stores_code_and_message(self):
        e = Error(code="E001", message="something failed")
        assert e.code == "E001"
        assert e.message == "something failed"

    def test_to_dict_returns_correct_keys(self):
        e = Error(code="E002", message="bad request")
        d = e.to_dict()
        assert d["code"] == "E002"
        assert d["message"] == "bad request"

    def test_optional_error_code_id_ignored_in_dict(self):
        e = Error(code="E003", message="err", error_code_id="FINS_001")
        d = e.to_dict()
        assert "error_code_id" not in d


class TestAPIResponse:
    def test_default_message_is_success(self):
        r = APIResponse(data={"key": "val"}, code=200)
        assert r.message == "Success"

    def test_single_error_message_used(self):
        err = Error(code="ERR", message="Something broke")
        r = APIResponse(errors=[err], code=400)
        assert r.message == "Something broke"

    def test_multiple_errors_generic_message(self):
        errors = [Error("E1", "first"), Error("E2", "second")]
        r = APIResponse(errors=errors, code=400)
        assert r.message == "Something went wrong."

    def test_custom_message_overrides_auto(self):
        r = APIResponse(message="Custom message", code=200)
        assert r.message == "Custom message"

    def test_request_id_auto_generated_as_uuid(self):
        r = APIResponse(data="ok", code=200)
        assert r.request_id is not None
        uuid.UUID(r.request_id)

    def test_request_id_unique_per_instance(self):
        r1 = APIResponse(code=200)
        r2 = APIResponse(code=200)
        assert r1.request_id != r2.request_id

    def test_to_dict_has_required_keys(self):
        r = APIResponse(data="ok", code=200)
        d = r.to_dict()
        for key in ("data", "errors", "status_code", "request_id", "message"):
            assert key in d

    def test_to_dict_errors_serialized(self):
        err = Error(code="ERR", message="fail")
        r = APIResponse(errors=[err], code=400)
        d = r.to_dict()
        assert d["errors"][0]["code"] == "ERR"

    def test_empty_data_defaults_to_empty_list(self):
        r = APIResponse(code=200)
        assert r.data == []

    def test_code_defaults_to_200(self):
        r = APIResponse()
        assert r.code == 200
