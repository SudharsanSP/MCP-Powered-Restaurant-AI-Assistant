"""
Tests for MCP_Server/src/utilities/logger.py

Because the MCP_Client src is already on sys.path (via the Client conftest),
"utilities.logger" would normally resolve to the client's logger.
We load the server logger explicitly from its file path to avoid the conflict.

Covers:
  - get_logger: returns a configured Logger, is idempotent
  - JsonFormatter: output is valid JSON with required keys
  - RequestIdFilter: injects request_id from ContextVar
  - with_async_request_id decorator
"""
import sys
import os
import json
import logging
import importlib.util
import importlib.machinery

import pytest

_SERVER_LOGGER_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..", "..", "MCP_Server", "src", "utilities", "logger.py",
    )
)

# Load the server logger as a uniquely-named module to avoid caching conflicts
_spec = importlib.util.spec_from_file_location(
    "mcp_server_utilities_logger", _SERVER_LOGGER_PATH
)
_server_logger_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_server_logger_mod)

get_logger = _server_logger_mod.get_logger
JsonFormatter = _server_logger_mod.JsonFormatter
RequestIdFilter = _server_logger_mod.RequestIdFilter
_request_id = _server_logger_mod._request_id
with_async_request_id = _server_logger_mod.with_async_request_id


class TestGetLogger:
    def test_returns_logger_instance(self):
        logger = get_logger("srv.test.module")
        assert isinstance(logger, logging.Logger)

    def test_logger_name_matches(self):
        logger = get_logger("srv.my.service")
        assert logger.name == "srv.my.service"

    def test_idempotent_multiple_calls(self):
        """Calling get_logger twice with same name must not duplicate handlers."""
        logger1 = get_logger("srv.idempotent")
        count = len(logger1.handlers)
        logger2 = get_logger("srv.idempotent")
        assert logger1 is logger2
        assert len(logger2.handlers) == count


class TestJsonFormatter:
    def test_output_is_valid_json(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hello world", args=(), exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["message"] == "hello world"
        assert parsed["level"] == "INFO"

    def test_output_contains_required_keys(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="svc", level=logging.WARNING, pathname="", lineno=0,
            msg="warn", args=(), exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        for key in ("timestamp", "level", "logger", "message", "request_id"):
            assert key in parsed

    def test_exception_info_serialized(self):
        formatter = JsonFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="svc", level=logging.ERROR, pathname="", lineno=0,
            msg="crash", args=(), exc_info=exc_info,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]["type"]


class TestRequestIdFilter:
    def test_injects_request_id_from_context_var(self):
        token = _request_id.set("req-server-123")
        try:
            f = RequestIdFilter()
            record = logging.LogRecord(
                name="test", level=logging.INFO, pathname="", lineno=0,
                msg="hi", args=(), exc_info=None,
            )
            result = f.filter(record)
            assert result is True
            assert record.request_id == "req-server-123"
        finally:
            _request_id.reset(token)

    def test_filter_always_returns_true(self):
        f = RequestIdFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hi", args=(), exc_info=None,
        )
        assert f.filter(record) is True

    def test_request_id_attr_set_on_record(self):
        f = RequestIdFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hi", args=(), exc_info=None,
        )
        f.filter(record)
        assert hasattr(record, "request_id")


class TestWithAsyncRequestId:
    @pytest.mark.asyncio
    async def test_decorated_function_executes(self):
        @with_async_request_id
        async def my_func(x):
            return x * 2

        assert await my_func(5) == 10

    @pytest.mark.asyncio
    async def test_preserves_function_name(self):
        @with_async_request_id
        async def named_func():
            pass

        assert named_func.__name__ == "named_func"

    @pytest.mark.asyncio
    async def test_request_id_set_during_execution(self):
        captured = []

        @with_async_request_id
        async def capture():
            captured.append(_request_id.get())

        await capture()
        assert len(captured) == 1
        assert captured[0] is not None and captured[0] != ""
