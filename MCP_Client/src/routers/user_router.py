from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from models.APIresponse import APIResponse
from models.user import UserCreateRequest
from services.dependency import get_user_service
from services.user_service import UserService
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/coffee_shop_bot/api/v1", tags=["users"])

@router.post("/user")
async def create_user(
    payload: UserCreateRequest,
    service: UserService = Depends(get_user_service),
):
    try:
        logger.info("User creation endpoint requested")
        result = await service.create_user(payload)
        return JSONResponse(
            status_code=HttpStatusCode.CREATED,
            content=jsonable_encoder(
                APIResponse(
                    data=result,
                    code=HttpStatusCode.CREATED,
                    message="User created successfully",
                ).to_dict()
            ),
        )
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Unhandled error in user creation endpoint")
        raise Custom_Exception(
            "The user creation request could not be completed.",
            ErrorCode.INTERNAL_SERVER_ERROR,
            HttpStatusCode.INTERNAL_SERVER_ERROR,
        )