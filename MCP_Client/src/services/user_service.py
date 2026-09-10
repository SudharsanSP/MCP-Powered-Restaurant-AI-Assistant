from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
import uuid

from models.user import UserCreateRequest, UserCreateResponse
from repositories.database import get_db_session
from repositories.user_repository import UserRepository
from settings import config
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.hashing import hash_value
from utilities.logger import get_logger
from utilities.tokens import create_access_token

logger = get_logger(__name__)


class UserService:
    def __init__(self) -> None:
        self.repository = UserRepository()

    async def create_user(self, payload: UserCreateRequest) -> UserCreateResponse:
        async for session in get_db_session():
            try:
                logger.info("Starting user creation")
                email = str(payload.email).lower()
                existing_customer = await self.repository.find_by_email_or_phone(
                    session,
                    email,
                    payload.phone_number,
                )
                if existing_customer is not None:
                    raise Custom_Exception(
                        "A user with this email or phone number already exists.",
                        ErrorCode.CONFLICT,
                        HttpStatusCode.CONFLICT,
                    )

                refresh_token = secrets.token_urlsafe(48)
                customer = await self.repository.create_user(
                    session=session,
                    customer_uuid=str(uuid.uuid4()),
                    name=payload.name,
                    phone_number="+91 " + payload.phone_number,
                    email=email,
                    password_hash=hash_value(payload.password),
                    refresh_token_hash=hash_value(refresh_token),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=config.refresh_token_expire_days),
                )
                await session.commit()
                logger.info("User creation completed")
                return UserCreateResponse(
                    customer_uuid=str(customer.customer_uuid),
                    access_token=create_access_token(str(customer.customer_uuid), customer.role),
                    refresh_token=refresh_token,
                    expires_in=config.access_token_expire_minutes * 60,
                )
            except Custom_Exception:
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                logger.exception("User creation failed")
                raise Custom_Exception(
                    "Unable to create user.",
                    ErrorCode.INTERNAL_SERVER_ERROR,
                    HttpStatusCode.INTERNAL_SERVER_ERROR,
                )