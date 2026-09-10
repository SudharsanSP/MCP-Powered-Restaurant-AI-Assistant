from __future__ import annotations

from datetime import datetime, timedelta, timezone
import jwt

from settings import config
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger

logger = get_logger(__name__)


def create_access_token(customer_uuid: str, role: str) -> str:
    try:
        now = datetime.now(timezone.utc)
        payload = {
            "user_uuid": customer_uuid,
            "role": role,
            "iat": now,
            "exp": now + timedelta(minutes=config.access_token_expire_minutes),
        }
        return jwt.encode(payload, config.jwt_secret, algorithm="HS256")
    except Exception:
        logger.exception("Failed to create access token")
        raise Custom_Exception(
            "Unable to create access token.",
            ErrorCode.INTERNAL_SERVER_ERROR,
            HttpStatusCode.INTERNAL_SERVER_ERROR,
        )
