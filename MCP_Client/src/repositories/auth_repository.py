from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.schema.coffee_shop_models import Customer, User
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger

logger = get_logger(__name__)


class AuthRepository:
    async def get_customer_by_email(self, session: AsyncSession, email: str):
        try:
            logger.info("Checking customer by email")
            result = await session.execute(
                select(Customer)
                .where(Customer.email == email, Customer.is_active.is_(True))
            )
            return result.scalar_one_or_none()
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to find customer by email")
            raise Custom_Exception(
                "Unable to process login.", ErrorCode.DATABASE_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR
            )

    async def get_user_by_email(self, session: AsyncSession, email: str):
        try:
            logger.info("Checking user by email")
            result = await session.execute(
                select(User)
                .where(User.email == email, User.is_active.is_(True))
            )
            return result.scalar_one_or_none()
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to find user by email")
            raise Custom_Exception(
                "Unable to process login.", 
                ErrorCode.DATABASE_ERROR,
                HttpStatusCode.INTERNAL_SERVER_ERROR
            )


    async def get_customer_by_uuid(self, session: AsyncSession, customer_uuid: str) -> Customer | None:
        try:
            logger.info("Checking customer identity")
            result = await session.execute(
                select(Customer).where(
                    Customer.customer_uuid == customer_uuid,
                    Customer.is_active.is_(True),
                )
            )
            return result.scalar_one_or_none()
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to check customer identity")
            raise Custom_Exception(
                "Unable to validate customer identity.",
                ErrorCode.DATABASE_ERROR,
                HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def get_customer_by_refresh_token(self, session: AsyncSession, refresh_token_hash: str):
        try:
            logger.info("Checking customer by refresh token")
            result = await session.execute(
                select(Customer).where(
                    Customer.refresh_token == refresh_token_hash,
                    Customer.is_active.is_(True),
                )
            )
            return result.scalar_one_or_none()
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to find customer by refresh token")
            raise Custom_Exception(
                "Unable to process refresh token.", ErrorCode.DATABASE_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR
            )

    async def save_refresh_token(
        self,
        session: AsyncSession,
        customer: Customer,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> None:
        try:
            logger.info("Storing refresh token")
            customer.refresh_token = refresh_token_hash
            customer.expires_at = expires_at
            customer.is_revoked = False
            await session.flush()
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to store refresh token")
            raise Custom_Exception(
                "Unable to store refresh token.", ErrorCode.DATABASE_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR
            )

    async def revoke_refresh_token(self, session: AsyncSession, customer: Customer) -> None:
        try:
            logger.info("Revoking refresh token")
            customer.is_revoked = True
            await session.flush()
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to revoke refresh token")
            raise Custom_Exception(
                "Unable to revoke refresh token.", ErrorCode.DATABASE_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR
            )

    @staticmethod
    def is_refresh_token_valid(customer: Customer) -> bool:
        try:
            return (
                not customer.is_revoked
                and customer.expires_at is not None
                and customer.expires_at.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc)
            )
        except Exception:
            logger.exception("Failed to validate refresh token expiry")
            raise Custom_Exception(
                "Unable to validate refresh token.", ErrorCode.DATABASE_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR
            )

    async def get_user_by_uuid(self, session: AsyncSession, user_uuid: str) -> User | None:
        try:
            logger.info("Checking user identity")
            result = await session.execute(
                select(User).where(
                    User.user_uuid == user_uuid,
                    User.is_active.is_(True),
                )
            )
            return result.scalar_one_or_none()
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to check user identity")
            raise Custom_Exception(
                "Unable to validate user identity.",
                ErrorCode.DATABASE_ERROR,
                HttpStatusCode.INTERNAL_SERVER_ERROR,
            )
