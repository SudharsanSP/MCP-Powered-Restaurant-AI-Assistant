from __future__ import annotations

import logging
import re
from time import perf_counter
from uuid import UUID

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from settings import config
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger, request_id_context

logger = get_logger(__name__)


def error_response(request_id: str, message: str, code: str, status_code: int):
    return JSONResponse(
        status_code=status_code,
        content={
            "data": None,
            "errors": [{"code": code, "message": message}],
            "status_code": status_code,
            "request_id": request_id,
            "message": message,
        },
        headers={"X-Request-ID": request_id},
    )


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", "")
        request.state.request_id = request_id
        request_id_context.set(request_id)
        started_at = perf_counter()

        # if request.url.path.startswith("/coffee_shop_bot/api/v1/"):
        #     authorization = request.headers.get("Authorization", "")
            # if not authorization.startswith("Bearer "):
            #     logger.warning(
            #         "Authentication rejected because the bearer token is missing",
            #         extra={"request_id": request_id},
            #     )
            #     return error_response(request_id, "Authentication is required.", ErrorCode.UNAUTHORIZED, HttpStatusCode.UNAUTHORIZED)
            # try:
            #     claims = jwt.decode(
            #         authorization.removeprefix("Bearer ").strip(),
            #         config.jwt_secret,
            #         algorithms=[config.jwt_algorithm],
            #     )
            #     request.state.jwt_claims = claims
                
            #     customer_match = re.search(r"/chat_bot/([^/]+)$", request.url.path)
            #     customer_id = customer_match.group(1) if customer_match else None
            #     claim_customer_id = claims.get("customer_id", claims.get("sub"))
            #     if not claim_customer_id:
            #         logger.warning(
            #             "Authorization rejected because the token has no customer identity",
            #             extra={"request_id": request_id},
            #         )
            #         return error_response(request_id, "The authentication token has no customer identity.", ErrorCode.UNAUTHORIZED, HttpStatusCode.FORBIDDEN)
            #     if customer_id and UUID(customer_id) != UUID(str(claim_customer_id)):
            #         logger.warning(
            #             "Authorization rejected because the token customer does not match the requested customer",
            #             extra={"request_id": request_id},
            #         )
            #         return error_response(request_id, "You are not authorized to access this customer.", ErrorCode.UNAUTHORIZED, HttpStatusCode.FORBIDDEN)
            # except (jwt.InvalidTokenError, ValueError, TypeError):
            #     logger.warning(
            #         "Authentication rejected because the token is invalid",
            #         extra={"request_id": request_id},
            #     )
            #     return error_response(request_id, "The authentication token is invalid.", ErrorCode.UNAUTHORIZED, HttpStatusCode.UNAUTHORIZED)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "Request completed method=%s path=%s status_code=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            (perf_counter() - started_at) * 1000,
            extra={"request_id": request_id},
        )
        return response
