import json
import logging
from contextvars import ContextVar
from pathlib import Path

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_context.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "exception": getattr(record, "exception", None),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    project_root = Path(__file__).resolve().parents[2]
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_dir / "mcp_client_app.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    formatter = JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S%z")
    request_filter = RequestContextFilter()
    file_handler.setFormatter(formatter)
    file_handler.addFilter(request_filter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(request_filter)
    logger.addHandler(stream_handler)

    return logger
