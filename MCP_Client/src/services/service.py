from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger

logger = get_logger(__name__)

class ChatBotService:
    def __init__(self, agent):
        self.agent = agent

    async def chat_bot_service(self, request, customer_id):
        try:
            logger.info("Processing chat request for customer_id=%s", customer_id)
            result = await self.agent.call_agent(request, customer_id)
            logger.info("Chat request handled successfully for customer_id=%s", customer_id)
            return result
        except Custom_Exception:
            raise
        except Exception as e:
            logger.exception("Chat service failed for customer_id=%s", customer_id)
            raise Custom_Exception(
                message=f"Unexpected service error: {str(e)}",
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )