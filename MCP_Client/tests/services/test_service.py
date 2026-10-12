"""
Tests for MCP_Client/src/services/service.py (ChatBotService)

Functions under test:
  - ChatBotService.chat_bot_service
  - ChatBotService.chat_bot_hitl_service
"""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.service import ChatBotService
from models.model import UserQuery, HITLRequest
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.http_status import HttpStatusCode


class TestChatBotService:
    @pytest.mark.asyncio
    async def test_successful_chat_returns_agent_result(self):
        mock_agent = AsyncMock()
        mock_agent.call_agent.return_value = "Here is the menu!"

        service = ChatBotService(mock_agent)
        result = await service.chat_bot_service(
            UserQuery(user_query="show me the menu"),
            uuid.uuid4(),
            str(uuid.uuid4()),
        )

        assert result == "Here is the menu!"
        mock_agent.call_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_exception_raises_custom_exception(self):
        mock_agent = AsyncMock()
        mock_agent.call_agent.side_effect = Exception("agent crashed")

        service = ChatBotService(mock_agent)
        with pytest.raises(Custom_Exception) as exc_info:
            await service.chat_bot_service(
                UserQuery(user_query="hello"),
                uuid.uuid4(),
                str(uuid.uuid4()),
            )
        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_custom_exception_propagates(self):
        """A Custom_Exception from the agent must NOT be wrapped again."""
        mock_agent = AsyncMock()
        mock_agent.call_agent.side_effect = Custom_Exception(
            "agent fail", "INTERNAL_SERVER_ERROR", 500
        )

        service = ChatBotService(mock_agent)
        with pytest.raises(Custom_Exception) as exc_info:
            await service.chat_bot_service(
                UserQuery(user_query="hello"), uuid.uuid4(), str(uuid.uuid4())
            )
        assert exc_info.value.message == "agent fail"


class TestChatBotHITLService:
    @pytest.mark.asyncio
    async def test_approve_calls_reinvoke_with_approve_payload(self):
        mock_agent = AsyncMock()
        mock_agent.reinvoke_agent.return_value = "Order placed!"

        service = ChatBotService(mock_agent)
        await service.chat_bot_hitl_service(
            HITLRequest(decision="approve"),
            uuid.uuid4(),
            str(uuid.uuid4()),
        )

        call_args = mock_agent.reinvoke_agent.call_args
        decision_payload = call_args.args[0]
        assert decision_payload["type"] == "approve"

    @pytest.mark.asyncio
    async def test_reject_calls_reinvoke_with_reject_payload(self):
        mock_agent = AsyncMock()
        mock_agent.reinvoke_agent.return_value = "Order cancelled."

        service = ChatBotService(mock_agent)
        await service.chat_bot_hitl_service(
            HITLRequest(decision="reject"),
            uuid.uuid4(),
            str(uuid.uuid4()),
        )

        call_args = mock_agent.reinvoke_agent.call_args
        decision_payload = call_args.args[0]
        assert decision_payload["type"] == "reject"
        assert "message" in decision_payload

    @pytest.mark.asyncio
    async def test_reinvoke_error_raises_custom_exception(self):
        mock_agent = AsyncMock()
        mock_agent.reinvoke_agent.side_effect = Exception("LangGraph exploded")

        service = ChatBotService(mock_agent)
        with pytest.raises(Custom_Exception):
            await service.chat_bot_hitl_service(
                HITLRequest(decision="approve"), uuid.uuid4(), str(uuid.uuid4())
            )
