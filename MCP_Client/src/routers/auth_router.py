from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from models.APIresponse import APIResponse
from models.auth import LoginRequest, LogoutRequest, RefreshRequest
from services.auth_service import AuthService
from services.dependency import get_auth_service
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/coffee_shop_bot/api/v1")

@router.post("/auth/login")
async def login(
        payload: LoginRequest, 
        service: AuthService = Depends(get_auth_service)
    ):
        try:
            logger.info("Login endpoint requested")
            result = await service.login(payload)
            return JSONResponse(status_code=HttpStatusCode.OK, content=jsonable_encoder(APIResponse(data=result, code=HttpStatusCode.OK, message="Login successful").to_dict()))
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Unhandled error in login endpoint")
            raise Custom_Exception("The login request could not be completed.", ErrorCode.INTERNAL_SERVER_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR)

@router.post("/auth/refresh")
async def refresh(
        payload: RefreshRequest,
        service: AuthService = Depends(get_auth_service)
    ):
        try:
            logger.info("Refresh endpoint requested")
            result = await service.refresh(payload)
            return JSONResponse(status_code=HttpStatusCode.OK, content=jsonable_encoder(APIResponse(data=result, code=HttpStatusCode.OK, message="Token refreshed").to_dict()))
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Unhandled error in refresh endpoint")
            raise Custom_Exception("The refresh request could not be completed.", ErrorCode.INTERNAL_SERVER_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR)


@router.post("/auth/logout")
async def logout(
        payload: LogoutRequest, 
        service: AuthService = Depends(get_auth_service)
    ):
        try:
            logger.info("Logout endpoint requested")
            result = await service.logout(payload)
            return JSONResponse(status_code=HttpStatusCode.OK, content=jsonable_encoder(APIResponse(data=result, code=HttpStatusCode.OK, message="Logout successful").to_dict()))
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Unhandled error in logout endpoint")
            raise Custom_Exception("The logout request could not be completed.", ErrorCode.INTERNAL_SERVER_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR)
