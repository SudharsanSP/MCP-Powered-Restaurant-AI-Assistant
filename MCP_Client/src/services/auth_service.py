from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets

from models.auth import LoginRequest, LoginResponse, LogoutRequest, LogoutResponse, RefreshRequest, RefreshResponse
from repositories.auth_repository import AuthRepository
from repositories.database import get_db_session
from settings import config
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.hashing import hash_value, verify_value
from utilities.logger import get_logger
from utilities.tokens import create_access_token

logger = get_logger(__name__)


class AuthService:
    def __init__(self) -> None:
        self.repository = AuthRepository()

    async def login(self, payload: LoginRequest) -> LoginResponse:
        async for session in get_db_session():
            try:
                logger.info("Starting login")
                customer = await self.repository.get_customer_by_email(session, payload.email)
                if customer is None or not verify_value(payload.password, customer.password_hash):
                    raise Custom_Exception("Invalid email or password.", ErrorCode.UNAUTHORIZED, HttpStatusCode.UNAUTHORIZED)

                refresh_token = secrets.token_urlsafe(48)
                await self.repository.save_refresh_token(
                    session,
                    customer,
                    hash_value(refresh_token),
                    datetime.now(timezone.utc) + timedelta(days=config.refresh_token_expire_days),
                )
                await session.commit()
                logger.info("Login completed")
                return LoginResponse(
                    access_token=create_access_token(str(customer.customer_uuid), customer.role),
                    refresh_token=refresh_token,
                    expires_in=config.access_token_expire_minutes * 60,
                )
            except Custom_Exception:
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                logger.exception("Login failed")
                raise Custom_Exception("Unable to complete login.", ErrorCode.INTERNAL_SERVER_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR)

    async def refresh(self, payload: RefreshRequest) -> RefreshResponse:
        async for session in get_db_session():
            try:
                logger.info("Starting access-token refresh")
                customer = await self.repository.get_customer_by_refresh_token(session, hash_value(payload.refresh_token))
                if customer is None or not self.repository.is_refresh_token_valid(customer):
                    raise Custom_Exception("Invalid or expired refresh token.", ErrorCode.UNAUTHORIZED, HttpStatusCode.UNAUTHORIZED)
                result = RefreshResponse(
                    access_token=create_access_token(str(customer.customer_uuid), customer.role),
                    token_type="bearer",
                    expires_in=config.access_token_expire_minutes * 60,
                )
                logger.info("Access-token refresh completed")
                return result
            except Custom_Exception:
                raise
            except Exception:
                logger.exception("Access-token refresh failed")
                raise Custom_Exception("Unable to refresh access token.", ErrorCode.INTERNAL_SERVER_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR)

    async def logout(self, payload: LogoutRequest) -> LogoutResponse:
        async for session in get_db_session():
            try:
                logger.info("Starting logout")
                customer = await self.repository.get_customer_by_refresh_token(session, hash_value(payload.refresh_token))
                if customer is not None:
                    await self.repository.revoke_refresh_token(session, customer)
                    await session.commit()
                    logger.info("Logout completed")
                return LogoutResponse(message="Logged out successfully.")
            except Custom_Exception:
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                logger.exception("Logout failed")
                raise Custom_Exception("Unable to complete logout.", ErrorCode.INTERNAL_SERVER_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR)
    