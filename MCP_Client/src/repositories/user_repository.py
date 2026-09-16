from datetime import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.schema.coffee_shop_models import Customer
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger

logger = get_logger(__name__)


class UserRepository:
    async def find_by_email_or_phone(
        self,
        session: AsyncSession,
        email: str,
        phone_number: str,
    ) -> Customer | None:
        try:
            logger.info("Checking whether user email or phone number already exists")
            result = await session.execute(
                select(Customer).where(
                    (Customer.email == email) | (Customer.phone_number == "+91 " + phone_number)
                )
            )
            return result.scalar_one_or_none()
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to check existing user credentials")
            raise Custom_Exception(
                "Unable to validate user details.",
                ErrorCode.DATABASE_ERROR,
                HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def create_user(
        self,
        session: AsyncSession,
        customer_uuid: str,
        name: str,
        phone_number: str,
        email: str,
        password_hash: str,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> Customer:
        try:
            logger.info("Creating customer record")
            customer = Customer(
                customer_uuid= customer_uuid,
                name=name,
                phone_number=phone_number,
                email=email,
                password_hash=password_hash,
                role="user",
                refresh_token=refresh_token_hash,
                expires_at=expires_at,
                is_revoked=False,
                is_active=True,
            )
            session.add(customer)
            await session.flush()
            logger.info("Customer record flushed")
            return customer
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to create customer record")
            raise Custom_Exception(
                "Unable to create user.",
                ErrorCode.DATABASE_ERROR,
                HttpStatusCode.INTERNAL_SERVER_ERROR,
            )