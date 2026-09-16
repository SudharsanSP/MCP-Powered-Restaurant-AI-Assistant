from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from models.APIresponse import APIResponse
from services.admin_service import AdminService
from services.dependency import get_admin_service
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/coffee_shop_bot/api/v1")

@router.get("/admin/orders")
async def get_orders(
        service: AdminService = Depends(get_admin_service)
    ):
        try:
            logger.info("Get Orders admin endpoint requested")
            result = await service.get_orders()
            return JSONResponse(status_code=HttpStatusCode.OK, content=jsonable_encoder(APIResponse(data=result, code=HttpStatusCode.OK, message="Orders fetched successfully").to_dict()))
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Unhandled error in Get Orders endpoint")
            raise Custom_Exception("The order fetching request could not be completed.", ErrorCode.INTERNAL_SERVER_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR)
