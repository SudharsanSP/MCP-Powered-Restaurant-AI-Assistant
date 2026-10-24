from __future__ import annotations

from contextlib import AsyncExitStack
from typing import AsyncIterator
from fastapi import Request
from services.auth_service import AuthService
from services.user_service import UserService
from services.admin_service import AdminService
from agents.agent import Agent
from agents.autonomous_agent import ManagerAgent
from client.client import (
    create_chat_model,
    create_checkpointer,
    create_mcp_client,
)
from repositories.database import get_db_session
from services.service import ChatBotService
from services.autonomous_service import AutonomousAgentService
from settings import config
from utilities.logger import get_logger

logger = get_logger(__name__)


class ApplicationDependencies:
    """Owns resources that are expensive to create and safe to share."""

    def __init__(self) -> None:
        self._exit_stack = AsyncExitStack()
        self.llm_model = None
        self.summary_model = None
        self.mcp_client = None
        self.checkpointer = None
        self.agent = None
        self.chatbot_service = None
        self.autonomous_service = None

    async def initialize(self) -> None:
        logger.info("Initializing shared application dependencies")
        try:
            self.llm_model = create_chat_model(config.max_token, config.temperature)
            self.summary_model = create_chat_model(150, 0.5)
            self.mcp_client = create_mcp_client()
            agent_factory = Agent(None, self.mcp_client)
            tools = await agent_factory.get_tools()
            self.checkpointer = await self._exit_stack.enter_async_context(
                create_checkpointer()
            )
            await self.checkpointer.setup()
            self.agent = agent_factory.call_agent_factory(
                self.llm_model,
                self.summary_model,
                tools,
                self.checkpointer,
            )
            self.chatbot_service = ChatBotService(
                Agent(self.agent, self.mcp_client)
            )

            # ── Autonomous manager agent ──────────────────────────────────
            logger.info("Initializing autonomous manager agent")
            # Phase 1 data-collection agent: moderate tokens (tool calls only)
            manager_model = create_chat_model(1000, config.temperature)
            manager_summary_model = create_chat_model(300, 0.2)
            # Phase 2 composition model: higher tokens to write sections JSON
            composition_model = create_chat_model(4000, 0.4)
            manager_agent = await ManagerAgent.create(
                model=manager_model,
                summary_model=manager_summary_model,
                composition_model=composition_model,
                mcp_client=self.mcp_client,
            )
            self.autonomous_service = AutonomousAgentService(manager_agent)

            logger.info("Shared application dependencies initialized successfully")
        except Exception:
            logger.exception("Failed to initialize shared application dependencies")
            await self.close()
            raise

    async def close(self) -> None:
        logger.info("Closing shared application dependencies")
        await self._exit_stack.aclose()
        logger.info("Shared application dependencies closed")


async def lifespan_dependencies() -> AsyncIterator[ApplicationDependencies]:
    dependencies = ApplicationDependencies()
    await dependencies.initialize()
    try:
        yield dependencies
    finally:
        await dependencies.close()


def get_chatbot_service(request: Request):
    dependencies: ApplicationDependencies = request.app.state.dependencies
    logger.info("Resolved shared ChatBotService dependency")
    return dependencies.chatbot_service

def get_autonomous_service(request: Request):
    dependencies: ApplicationDependencies = request.app.state.dependencies
    logger.info("Resolved shared AutonomousAgentService dependency")
    return service.autonomous_service

def get_auth_service():
    return AuthService()

def get_user_service():
    return UserService()

def get_admin_service():
    return AdminService()
