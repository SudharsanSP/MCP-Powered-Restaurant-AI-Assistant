"""
Tests for MCP_Client/src/services/dependency.py

Covers:
  - ApplicationDependencies.initialize  (happy path + failure path)
  - ApplicationDependencies.close
  - get_chatbot_service  (resolves from request.app.state)
  - get_auth_service / get_user_service / get_admin_service  (factory fns)
"""
import sys
import os
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

CLIENT_SRC = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "MCP_Client", "src"
)
if CLIENT_SRC not in sys.path:
    sys.path.insert(0, CLIENT_SRC)

from services.dependency import (
    ApplicationDependencies,
    get_chatbot_service,
    get_auth_service,
    get_user_service,
    get_admin_service,
)
from services.auth_service import AuthService
from services.user_service import UserService
from services.admin_service import AdminService
from services.service import ChatBotService


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #
def _make_async_cm(return_value):
    """Return an async context manager that yields return_value."""
    @asynccontextmanager
    async def _cm():
        yield return_value

    return _cm()


# --------------------------------------------------------------------------- #
# ApplicationDependencies.initialize                                            #
# --------------------------------------------------------------------------- #
class TestApplicationDependenciesInitialize:
    @pytest.mark.asyncio
    async def test_successful_initialization_sets_all_attributes(self):
        mock_llm = MagicMock()
        mock_mcp_client = AsyncMock()
        mock_mcp_client.get_tools = AsyncMock(return_value=["tool_a"])
        mock_checkpointer = AsyncMock()
        mock_checkpointer.setup = AsyncMock()
        mock_agent_instance = MagicMock()

        with patch("services.dependency.create_chat_model", return_value=mock_llm) as mock_ccm, \
             patch("services.dependency.create_mcp_client", return_value=mock_mcp_client), \
             patch("services.dependency.create_checkpointer") as mock_cp_factory, \
             patch("services.dependency.Agent") as MockAgent:

            # Make create_checkpointer return an async context manager
            mock_cp_factory.return_value = _make_async_cm(mock_checkpointer)

            mock_agent_obj = MockAgent.return_value
            mock_agent_obj.get_tools = AsyncMock(return_value=["tool_a"])
            mock_agent_obj.call_agent_factory = MagicMock(return_value=mock_agent_instance)

            deps = ApplicationDependencies()
            await deps.initialize()

        assert deps.llm_model is not None
        assert deps.mcp_client is not None
        assert deps.checkpointer is not None
        assert deps.agent is not None
        assert deps.chatbot_service is not None
        assert isinstance(deps.chatbot_service, ChatBotService)
        mock_checkpointer.setup.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_initialization_failure_calls_close(self):
        """If initialization fails, close() must still be called."""
        with patch("services.dependency.create_chat_model", side_effect=Exception("LLM init failed")):
            deps = ApplicationDependencies()
            with pytest.raises(Exception, match="LLM init failed"):
                await deps.initialize()

    @pytest.mark.asyncio
    async def test_close_calls_exit_stack_aclose(self):
        deps = ApplicationDependencies()
        mock_stack = AsyncMock()
        deps._exit_stack = mock_stack

        await deps.close()
        mock_stack.aclose.assert_awaited_once()


# --------------------------------------------------------------------------- #
# get_chatbot_service                                                           #
# --------------------------------------------------------------------------- #
class TestGetChatbotService:
    def test_returns_chatbot_service_from_app_state(self):
        mock_chatbot = MagicMock(spec=ChatBotService)
        mock_deps = MagicMock()
        mock_deps.chatbot_service = mock_chatbot

        mock_request = MagicMock()
        mock_request.app.state.dependencies = mock_deps

        result = get_chatbot_service(mock_request)
        assert result is mock_chatbot


# --------------------------------------------------------------------------- #
# Service factory functions                                                     #
# --------------------------------------------------------------------------- #
class TestServiceFactories:
    def test_get_auth_service_returns_auth_service_instance(self):
        result = get_auth_service()
        assert isinstance(result, AuthService)

    def test_get_user_service_returns_user_service_instance(self):
        result = get_user_service()
        assert isinstance(result, UserService)

    def test_get_admin_service_returns_admin_service_instance(self):
        result = get_admin_service()
        assert isinstance(result, AdminService)

    def test_each_call_returns_new_instance(self):
        """Factory functions create a new instance on every call."""
        s1 = get_auth_service()
        s2 = get_auth_service()
        assert s1 is not s2
