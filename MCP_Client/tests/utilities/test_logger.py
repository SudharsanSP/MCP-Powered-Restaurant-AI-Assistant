"""
Tests for MCP_Client/src/utilities/logger.py

Covers:
  - get_logger returns a configured Logger
  - RequestContextFilter injects request_id
  - JsonFormatter produces valid JSON
  - Calling get_logger twice with same name returns same instance (idempotent)
"""
import json
import logging
from utilities.logger import get_logger, RequestContextFilter, JsonFormatter, request_id_context


class TestGetLogger:
    def test_returns_logger_instance(self):
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)

    def test_idempotent_multiple_calls(self):
        """Calling get_logger twice with the same name must not duplicate handlers."""
        logger1 = get_logger("test.idempotent")
        handler_count = len(logger1.handlers)
        logger2 = get_logger("test.idempotent")
        assert logger1 is logger2
        assert len(logger2.handlers) == handler_count

    def test_logger_name_matches(self):
        logger = get_logger("my.service")
        assert logger.name == "my.service"


class TestRequestContextFilter:
    def test_injects_request_id_from_context_var(self):
        """Filter should stamp request_id from the ContextVar onto the log record."""
        token = request_id_context.set("req-abc-123")
        try:
            f = RequestContextFilter()
            record = logging.LogRecord(
                name="test", level=logging.INFO, pathname="", lineno=0,
                msg="hello", args=(), exc_info=None
            )
            result = f.filter(record)
            assert result is True
            assert record.request_id == "req-abc-123"
        finally:
            request_id_context.reset(token)

    def test_uses_existing_request_id_if_set(self):
        """If record already has request_id, the filter must not overwrite it."""
        f = RequestContextFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hello", args=(), exc_info=None
        )
        record.request_id = "already-set"
        f.filter(record)
        assert record.request_id == "already-set"


class TestJsonFormatter:
    def test_output_is_valid_json(self):
        formatter = JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )
        record.request_id = "req-1"
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["message"] == "test message"
        assert parsed["level"] == "INFO"

    def test_output_contains_required_keys(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="svc", level=logging.WARNING, pathname="", lineno=0,
            msg="warn", args=(), exc_info=None
        )
        record.request_id = "-"
        output = formatter.format(record)
        parsed = json.loads(output)
        for key in ("timestamp", "level", "logger", "message", "request_id"):
            assert key in parsed
