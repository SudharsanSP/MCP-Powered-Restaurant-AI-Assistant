import json

from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from models.APIresponse import APIResponse
from services.service import ChatBotService
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.error_log import error_logger
from models.model import UserQuery
from repositories.database import get_db_session
from utilities.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/coffee_shop_bot/api")
service = ChatBotService()

@router.post("/v1/chat_bot/{customer_id}")
async def chat_bot_router(
    request: UserQuery = Body(...),
    customer_id: int = Path(...),
    db_session: AsyncSession = Depends(get_db_session),
):
    try:
        logger.info("Incoming chat request for customer_id=%s query=%s", customer_id, request.user_query)
        result = await service.chat_bot_service(request, customer_id)
        data = APIResponse(
            data=result,
            code=HttpStatusCode.OK,
            message="Success",
        )
        return JSONResponse(
            content=data.to_dict(),
            status_code=data.code,
        )
    except Custom_Exception:
        raise
    except Exception as e:
        logger.exception("Unhandled error in chat_bot_router for customer_id=%s", customer_id)
        error_logger(
            file_name='router.py',
            function_name='chat_bot_router',
            error_message=str(e),
        )
        raise Custom_Exception(
            message=f"Router error: {str(e)}",
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
        )
        
