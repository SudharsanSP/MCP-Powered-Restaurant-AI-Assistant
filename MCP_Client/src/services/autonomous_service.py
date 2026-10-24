"""
autonomous_service.py
---------------------
Service layer for the autonomous manager agent (/agent endpoint).
Validates input and delegates to ManagerAgent.run().
"""

from __future__ import annotations

from agents.autonomous_agent import ManagerAgent
from models.model import AgentRequest, AgentResponse
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger

logger = get_logger(__name__)


class AutonomousAgentService:
    def __init__(self, agent: ManagerAgent) -> None:
        self._agent = agent

    async def run(self, request: AgentRequest) -> AgentResponse:
        try:
            logger.info("AutonomousAgentService: processing request")
            result = await self._agent.run(request.request)
            logger.info(
                "AutonomousAgentService: completed — document=%s",
                result.document_filename,
            )
            return result
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("AutonomousAgentService: unexpected failure")
            raise Custom_Exception(
                "The agent request could not be completed.",
                ErrorCode.INTERNAL_SERVER_ERROR,
                HttpStatusCode.INTERNAL_SERVER_ERROR,
            )
