from uuid import UUID

from fastapi import APIRouter, Depends, Path, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from models.APIresponse import APIResponse
from models.admin import CreateItemRequest, UpdateItemRequest
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
    http_request: Request,
    service: AdminService = Depends(get_admin_service),
):
    try:
        logger.info("Get Orders endpoint requested")
        result = await service.get_orders()
        data = APIResponse(
            data=result,
            code=HttpStatusCode.OK,
            message="Orders fetched successfully",
            request_id=http_request.state.request_id,
        )
        return JSONResponse(status_code=HttpStatusCode.OK, content=jsonable_encoder(data.to_dict()))
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Unhandled error in Get Orders endpoint")
        raise Custom_Exception(
            "The order fetching request could not be completed.",
            ErrorCode.INTERNAL_SERVER_ERROR,
            HttpStatusCode.INTERNAL_SERVER_ERROR,
        )


@router.patch("/admin/orders/{order_id}/status")
async def update_order_status(
    http_request: Request,
    order_id: UUID = Path(...),
    service: AdminService = Depends(get_admin_service),
):
    try:
        logger.info("Update Order Status endpoint requested for order_id: %s", order_id)
        result = await service.update_order_status(order_id)
        data = APIResponse(
            data=result,
            code=HttpStatusCode.OK,
            message="Order status updated successfully",
            request_id=http_request.state.request_id,
        )
        return JSONResponse(status_code=HttpStatusCode.OK, content=jsonable_encoder(data.to_dict()))
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Unhandled error in Update Order Status endpoint for order_id: %s", order_id)
        raise Custom_Exception(
            "The order status update request could not be completed.",
            ErrorCode.INTERNAL_SERVER_ERROR,
            HttpStatusCode.INTERNAL_SERVER_ERROR,
        )


@router.post("/admin/items")
async def create_item(
    http_request: Request,
    body: CreateItemRequest,
    service: AdminService = Depends(get_admin_service),
):
    try:
        logger.info("Create Item endpoint requested", body.name)
        result = await service.create_item(body.name, body.price)
        data = APIResponse(
            data=result,
            code=HttpStatusCode.CREATED,
            message="Item created successfully",
            request_id=http_request.state.request_id,
        )
        return JSONResponse(status_code=HttpStatusCode.CREATED, content=jsonable_encoder(data.to_dict()))
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Unhandled error in Create Item endpoint")
        raise Custom_Exception(
            "The item creation request could not be completed.",
            ErrorCode.INTERNAL_SERVER_ERROR,
            HttpStatusCode.INTERNAL_SERVER_ERROR,
        )


@router.patch("/admin/items/{item_id}")
async def update_item(
    http_request: Request,
    item_id: UUID = Path(...),
    body: UpdateItemRequest = None,
    service: AdminService = Depends(get_admin_service),
):
    try:
        logger.info("Update Item endpoint requested")
        result = await service.update_item(item_id, body.name, body.price)
        data = APIResponse(
            data=result,
            code=HttpStatusCode.OK,
            message="Item updated successfully",
            request_id=http_request.state.request_id,
        )
        return JSONResponse(status_code=HttpStatusCode.OK, content=jsonable_encoder(data.to_dict()))
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Unhandled error in Update Item endpoint for item_id: %s", item_id)
        raise Custom_Exception(
            "The item update request could not be completed.",
            ErrorCode.INTERNAL_SERVER_ERROR,
            HttpStatusCode.INTERNAL_SERVER_ERROR,
        )


@router.delete("/admin/items/{item_id}")
async def delete_item(
    http_request: Request,
    item_id: UUID = Path(...),
    service: AdminService = Depends(get_admin_service),
):
    try:
        logger.info("Delete Item endpoint requested")
        await service.delete_item(item_id)
        data = APIResponse(
            data=None,
            code=HttpStatusCode.OK,
            message="Item deleted successfully",
            request_id=http_request.state.request_id,
        )
        return JSONResponse(status_code=HttpStatusCode.OK, content=jsonable_encoder(data.to_dict()))
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Unhandled error in Delete Item endpoint")
        raise Custom_Exception(
            "The item deletion request could not be completed.",
            ErrorCode.INTERNAL_SERVER_ERROR,
            HttpStatusCode.INTERNAL_SERVER_ERROR,
        )
