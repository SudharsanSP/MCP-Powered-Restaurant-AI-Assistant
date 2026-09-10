from uuid import UUID
from fastapi import APIRouter, Body, Depends, Path, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from models.APIresponse import APIResponse
from services.dependency import get_chatbot_service, get_db_session
from services.service import ChatBotService
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from models.model import UserQuery
from utilities.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/coffee_shop_bot/api/v1")
@router.post("/chat_bot/{customer_id}")
async def chat_bot_router(
    http_request: Request,
    request: UserQuery = Body(...),
    customer_id: UUID = Path(...),
    service: ChatBotService = Depends(get_chatbot_service),
):
    try:
        logger.info("Chat request received")
        result = await service.chat_bot_service(request, customer_id)
        data = APIResponse(
            data=result,
            code=HttpStatusCode.OK,
            message="Success",
            request_id=http_request.state.request_id,
        )
        return JSONResponse(
            content=jsonable_encoder(data.to_dict()),
            status_code=data.code,
        )
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Unhandled error in chat request")
        raise Custom_Exception(
            message="The request could not be completed.",
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
        )
        
