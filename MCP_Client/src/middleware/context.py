from __future__ import annotations

import logging
from uuid import UUID
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from utilities.logger import get_logger, request_id_context

logger = get_logger(__name__)

class ContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", "")
        request.state.request_id = request_id
        request_id_context.set(request_id)
        logger.info(
            "Request context initialized",
            extra={"request_id": request_id},
        )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "Request completed",
            extra={"request_id": request_id},
        )
        return response
