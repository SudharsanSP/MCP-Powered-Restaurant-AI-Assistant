from __future__ import annotations

import contextvars
import functools
import json
import logging
import traceback
import uuid
from pathlib import Path
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any, ParamSpec, TypeVar


_request_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id",
    default="system",
)
P = ParamSpec("P")
R = TypeVar("R")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", _request_id.get()),
        }

        if record.exc_info:
            entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": "".join(traceback.format_exception(*record.exc_info)),
            }

        return json.dumps(entry, default=str)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id.get()
        return True


@contextmanager
def request_context(function: Callable[P, R], request_id: str | None = None) -> Iterator[str]:
    active_request_id = request_id or str(uuid.uuid4())
    token = _request_id.set(active_request_id)
    try:
        yield active_request_id
    finally:
        _request_id.reset(token)

    @functools.wraps(function)
    def wrapped(*args: P.args, **kwargs: P.kwargs):
        with request_context():
            return function(*args, **kwargs)

    return wrapped


def with_async_request_id(function: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(function)
    async def wrapped(*args: P.args, **kwargs: P.kwargs):
        with request_context(function):
            return await function(*args, **kwargs)  # type: ignore[misc]

    return wrapped

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    project_root = Path(__file__).resolve().parents[2]
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_dir / "mcp_server_app.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    formatter = JsonFormatter()
    file_handler.setFormatter(formatter)
    file_handler.addFilter(RequestIdFilter())
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(RequestIdFilter())
    logger.addHandler(stream_handler)

    return logger
