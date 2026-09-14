from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger

logger = get_logger(__name__)

class ChatBotService:
    def __init__(self, agent):
        self.agent = agent

    async def chat_bot_service(self, request, thread_id, customer_id):
        try:
            logger.info("Processing chat request")
            result = await self.agent.call_agent(request, thread_id, customer_id)
            logger.info("Chat request handled successfully")
            return result
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Chat service failed")
            raise Custom_Exception(
                message="The chat request could not be completed.",
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def chat_bot_hitl_service(self, request, thread_id, customer_id):
            try:
                logger.info("Processing chat request")
                if request.decision == "approve":
                    decision_payload = {"type": "approve"}
                elif request.decision == "reject":
                    decision_payload = {"type": "reject", "message": "Order cancelled by user"}
                result = await self.agent.reinvoke_agent(decision_payload, thread_id, customer_id)
                logger.info("Chat re-invoking request handled successfully")
                return result
            except Custom_Exception:
                raise
            except Exception:
                logger.exception("Chat re-invoking service failed")
                raise Custom_Exception(
                    message="The chat request could not be completed.",
                    code=ErrorCode.INTERNAL_SERVER_ERROR,
                    status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
                )
        