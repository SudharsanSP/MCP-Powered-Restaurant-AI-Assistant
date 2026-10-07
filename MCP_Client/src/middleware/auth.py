from __future__ import annotations
from contextvars import ContextVar

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from repositories.auth_repository import AuthRepository
from repositories.admin_repository import AdminRepository
from repositories.database import get_db_session
from settings import config
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger

logger = get_logger(__name__)

PUBLIC_API_PATHS = frozenset(
    {
        "/health/live",
        "/health/ready",
        "/coffee_shop_bot/api/v1/auth/customer/login",
        "/coffee_shop_bot/api/v1/auth/admin/login",
        "/coffee_shop_bot/api/v1/auth/refresh",
        "/coffee_shop_bot/api/v1/user",
    }
)

customer_id_context: ContextVar[str] = ContextVar("customer_id", default="-")

def _normalized_path(request: Request) -> str:
    return request.url.path.rstrip("/") or "/"

def error_response(
    request_id: str,
    message: str,
    code: str,
    status_code: int,
) -> JSONResponse:
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

async def check_user_rbac(claims: dict, request: Request) -> tuple[bool, str | None]:
    """Verify JWT identity and role against the active customer record."""
    user_uuid = claims.get("user_uuid")
    customer_id_context.set(user_uuid)
    token_role = claims.get("role")
    if not user_uuid:
        logger.warning(
            "Authorization rejected because JWT identity is missing",
            extra={"request_id": request.state.request_id},
        )
        return False, "The authentication token has no user identity."
    if token_role == "user":
        try:
            customer = None
            async for session in get_db_session():
                customer = await AuthRepository().get_customer_by_uuid(session, user_uuid)
                break

            if customer is None:
                logger.warning(
                    "Authorization rejected because customer identity was not found",
                    extra={"request_id": request.state.request_id},
                )
                return False, "The customer identity is not authorized."

            if customer.role != token_role or customer.role != "user":
                logger.warning(
                    "Authorization rejected because customer role is not authorized",
                    extra={"request_id": request.state.request_id},
                )
                return False, "You are not authorized to access this resource."

            request.state.user_uuid = user_uuid
            request.state.user_role = customer.role
            logger.info(
                "Customer identity and role authorization passed",
                extra={"request_id": request.state.request_id},
            )
            return True, None
        except Exception:
            logger.exception(
                "Authorization database check failed",
                extra={"request_id": request.state.request_id},
            )
            return False, "Authorization could not be completed."
    
    elif token_role == "admin":
        try:
            user = None
            async for session in get_db_session():
                user = await AuthRepository().get_user_by_uuid(session, user_uuid)
                break

            if user is None:
                logger.warning(
                    "Authorization rejected because admin identity was not found",
                    extra={"request_id": request.state.request_id},
                )
                return False, "The admin identity is not authorized."

            if user.role != token_role or user.role != "admin":
                logger.warning(
                    "Authorization rejected because user role is not authorized",
                    extra={"request_id": request.state.request_id},
                )
                return False, "You are not authorized to access this resource."

            request.state.user_uuid = user_uuid
            request.state.user_role = user.role
            logger.info(
                "Admin identity and role authorization passed",
                extra={"request_id": request.state.request_id},
            )
            return True, None
        except Exception:
            logger.exception(
                "Authorization database check failed",
                extra={"request_id": request.state.request_id},
            )
            return False, "Authorization could not be completed."

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(
            "X-Request-ID",
            getattr(request.state, "request_id", ""),
        )
        request.state.request_id = request_id

        path = _normalized_path(request)

        if request.method == "OPTIONS" or path in PUBLIC_API_PATHS:
            logger.info(
                "Public request bypassed authentication",
                extra={"request_id": request_id},
            )
            try:
                response = await call_next(request)
                response.headers["X-Request-ID"] = request_id
                logger.info(
                    "Public request's response passed AuthMiddleware",
                    extra={"request_id": request_id},
                )
                return response
            except Exception:
                logger.exception(
                    "Public request failed",
                    extra={"request_id": request_id},
                )
                raise

        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            logger.warning(
                "Private request rejected because bearer authorization is missing or malformed",
                extra={"request_id": request_id},
            )
            return error_response(
                request_id,
                "Authentication is required.",
                ErrorCode.UNAUTHORIZED,
                HttpStatusCode.UNAUTHORIZED,
            )

        try:
            claims = jwt.decode(
                token.strip(),
                config.jwt_secret,
                algorithms=["HS256"],
                options={"require": ["user_uuid", "role", "exp"]},
            )
            request.state.jwt_claims = claims
            allowed, message = await check_user_rbac(claims, request)
            if not allowed:
                return error_response(
                    request_id,
                    message or "You are not authorized to access this resource.",
                    ErrorCode.UNAUTHORIZED,
                    HttpStatusCode.FORBIDDEN,
                )

            logger.info(
                "Private request authenticated successfully",
                extra={"request_id": request_id},
            )
        except jwt.ExpiredSignatureError:
            logger.warning(
                "Private request rejected because access token expired",
                extra={"request_id": request_id},
            )
            return error_response(
                request_id,
                "The authentication token has expired.",
                ErrorCode.UNAUTHORIZED,
                HttpStatusCode.UNAUTHORIZED,
            )
        except jwt.InvalidTokenError:
            logger.warning(
                "Private request rejected because access token is invalid",
                extra={"request_id": request_id},
            )
            return error_response(
                request_id,
                "The authentication token is invalid.",
                ErrorCode.UNAUTHORIZED,
                HttpStatusCode.UNAUTHORIZED,
            )
        except Exception:
            logger.exception(
                "Unexpected authentication middleware failure",
                extra={"request_id": request_id},
            )
            return error_response(
                request_id,
                "Authentication could not be completed.",
                ErrorCode.INTERNAL_SERVER_ERROR,
                HttpStatusCode.INTERNAL_SERVER_ERROR,
            )
        
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            logger.info(
                "Private request's response passed AuthMiddleware",
                extra={"request_id": request_id},
            )
            return response
        except Exception:
            logger.exception(
                "Private request failed after authentication",
                extra={"request_id": request_id},
            )
            raise