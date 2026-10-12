"""
Tests for MCP_Client/src/agents/agent.py

Classes / functions under test:
  - Agent.__init__
  - Agent.get_tools
  - Agent.call_agent_factory
  - Agent.call_agent
  - Agent.reinvoke_agent
  - custom_error_handler (module-level function)
"""
import sys
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

CLIENT_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "..", "MCP_Client", "src")
if CLIENT_SRC not in sys.path:
    sys.path.insert(0, CLIENT_SRC)

from agents.agent import Agent, custom_error_handler
from langchain.agents.structured_output import (
    MultipleStructuredOutputsError,
    StructuredOutputValidationError,
)
from langchain_core.messages import AIMessage
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.http_status import HttpStatusCode
from models.model import UserQuery


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #
def _make_agent(agent_mock=None, mcp_client_mock=None):
    if agent_mock is None:
        agent_mock = AsyncMock()
    if mcp_client_mock is None:
        mcp_client_mock = AsyncMock()
    return Agent(agent_mock, mcp_client_mock)


# --------------------------------------------------------------------------- #
# custom_error_handler                                                          #
# --------------------------------------------------------------------------- #
class TestCustomErrorHandler:
    def test_returns_string_for_any_exception(self):
        result = custom_error_handler(Exception("oops"))
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generic_exception_message_included(self):
        result = custom_error_handler(Exception("exploded"))
        assert "exploded" in result

    def test_structured_output_validation_error(self):
        error = StructuredOutputValidationError(
            "MenuResponse", Exception("invalid schema"), AIMessage(content="retry")
        )

        assert "Schema validation failed" in custom_error_handler(error)

    def test_multiple_structured_outputs_error(self):
        error = MultipleStructuredOutputsError(["MenuResponse", "OrderResponse"], AIMessage(content="retry"))

        assert "Multiple outputs were returned" in custom_error_handler(error)


# --------------------------------------------------------------------------- #
# Agent.__init__                                                                #
# --------------------------------------------------------------------------- #
class TestAgentInit:
    def test_stores_agent_and_mcp_client(self):
        mock_agent = MagicMock()
        mock_mcp = MagicMock()
        a = Agent(mock_agent, mock_mcp)
        assert a.agent is mock_agent
        assert a.mcp_client is mock_mcp


# --------------------------------------------------------------------------- #
# Agent.get_tools                                                               #
# --------------------------------------------------------------------------- #
class TestGetTools:
    @pytest.mark.asyncio
    async def test_returns_tools_from_mcp_client(self):
        mock_mcp = AsyncMock()
        mock_mcp.get_tools.return_value = ["tool_a", "tool_b"]

        a = _make_agent(mcp_client_mock=mock_mcp)
        tools = await a.get_tools()

        mock_mcp.get_tools.assert_called_once()
        assert tools == ["tool_a", "tool_b"]

    @pytest.mark.asyncio
    async def test_mcp_error_propagates(self):
        mock_mcp = AsyncMock()
        mock_mcp.get_tools.side_effect = Exception("MCP connection refused")

        a = _make_agent(mcp_client_mock=mock_mcp)
        with pytest.raises(Exception, match="MCP connection refused"):
            await a.get_tools()


# --------------------------------------------------------------------------- #
# Agent.call_agent_factory                                                      #
# --------------------------------------------------------------------------- #
class TestCallAgentFactory:
    def test_returns_agent_object(self):
        """call_agent_factory calls langchain's create_agent and returns its result."""
        mock_created_agent = MagicMock()

        with patch("agents.agent.create_agent", return_value=mock_created_agent) as mock_create, \
             patch("agents.agent.Prompt") as MockPrompt, \
             patch("agents.agent.SummarizationMiddleware", return_value=MagicMock()), \
             patch("agents.agent.PIIMiddleware", return_value=MagicMock()), \
             patch("agents.agent.HumanInTheLoopMiddleware", return_value=MagicMock()):
            mock_prompt_instance = MockPrompt.return_value
            mock_prompt_instance.get_system_prompt.return_value = "system prompt"
            mock_prompt_instance.summary_system_prompt.return_value = "summary prompt"

            a = _make_agent()
            result = a.call_agent_factory(
                model=MagicMock(),
                summary_model=MagicMock(),
                tools=["tool1"],
                checkpointer=MagicMock(),
            )

        mock_create.assert_called_once()
        assert result is mock_created_agent

    def test_passes_tools_and_checkpointer(self):
        """Verify tools and checkpointer are forwarded to create_agent."""
        mock_tools = ["tool_x"]
        mock_checkpointer = MagicMock()

        with patch("agents.agent.create_agent") as mock_create, \
             patch("agents.agent.Prompt"), \
             patch("agents.agent.SummarizationMiddleware", return_value=MagicMock()), \
             patch("agents.agent.PIIMiddleware", return_value=MagicMock()), \
             patch("agents.agent.HumanInTheLoopMiddleware", return_value=MagicMock()):
            a = _make_agent()
            a.call_agent_factory(
                model=MagicMock(),
                summary_model=MagicMock(),
                tools=mock_tools,
                checkpointer=mock_checkpointer,
            )
            kwargs = mock_create.call_args.kwargs
            assert kwargs["tools"] == mock_tools
            assert kwargs["checkpointer"] is mock_checkpointer


# --------------------------------------------------------------------------- #
# Agent.call_agent                                                              #
# --------------------------------------------------------------------------- #
class TestCallAgent:
    @pytest.mark.asyncio
    async def test_returns_last_message_content(self):
        """Normal flow: agent.ainvoke returns messages; last message content returned."""
        mock_message = MagicMock()
        mock_message.content = [{"text": "Here is the menu!"}]

        mock_inner_agent = AsyncMock()
        mock_inner_agent.ainvoke.return_value = {"messages": [mock_message]}

        a = _make_agent(agent_mock=mock_inner_agent)
        result = await a.call_agent(
            UserQuery(user_query="show me the menu"),
            uuid.uuid4(),
            uuid.uuid4(),
        )

        assert result == "Here is the menu!"

    @pytest.mark.asyncio
    async def test_interrupt_returns_description(self):
        """HITL: when __interrupt__ is in the result, return the description string."""
        interrupt_value = {
            "action_requests": [{"description": "Approve order placement?"}]
        }
        mock_inner_agent = AsyncMock()
        mock_inner_agent.ainvoke.return_value = {
            "__interrupt__": [MagicMock(value=interrupt_value)],
            "messages": [],
        }

        a = _make_agent(agent_mock=mock_inner_agent)
        result = await a.call_agent(
            UserQuery(user_query="place order"),
            uuid.uuid4(),
            uuid.uuid4(),
        )

        assert result == "Approve order placement?"

    @pytest.mark.asyncio
    async def test_exception_raises_custom_exception(self):
        mock_inner_agent = AsyncMock()
        mock_inner_agent.ainvoke.side_effect = Exception("LangGraph exploded")

        a = _make_agent(agent_mock=mock_inner_agent)
        with pytest.raises(Custom_Exception) as exc_info:
            await a.call_agent(
                UserQuery(user_query="hello"),
                uuid.uuid4(),
                uuid.uuid4(),
            )
        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_custom_exception_propagates_unchanged(self):
        """A Custom_Exception from the agent must NOT be re-wrapped."""
        original = Custom_Exception("agent fail", "ERR", 500)
        mock_inner_agent = AsyncMock()
        mock_inner_agent.ainvoke.side_effect = original

        a = _make_agent(agent_mock=mock_inner_agent)
        with pytest.raises(Custom_Exception) as exc_info:
            await a.call_agent(UserQuery(user_query="x"), uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.message == "agent fail"


# --------------------------------------------------------------------------- #
# Agent.reinvoke_agent                                                          #
# --------------------------------------------------------------------------- #
class TestReinvokeAgent:
    @pytest.mark.asyncio
    async def test_returns_last_message_content(self):
        mock_message = MagicMock()
        mock_message.content = [{"text": "Order placed!"}]

        mock_inner_agent = AsyncMock()
        mock_inner_agent.ainvoke.return_value = {"messages": [mock_message]}

        a = _make_agent(agent_mock=mock_inner_agent)
        result = await a.reinvoke_agent(
            {"type": "approve"},
            uuid.uuid4(),
            uuid.uuid4(),
        )

        assert result == "Order placed!"

    @pytest.mark.asyncio
    async def test_passes_command_resume_to_ainvoke(self):
        """reinvoke_agent must call ainvoke with a Command(resume=...) object."""
        mock_message = MagicMock()
        mock_message.content = [{"text": "done"}]

        mock_inner_agent = AsyncMock()
        mock_inner_agent.ainvoke.return_value = {"messages": [mock_message]}

        a = _make_agent(agent_mock=mock_inner_agent)
        decision = {"type": "reject", "message": "cancelled"}

        with patch("agents.agent.Command") as MockCommand:
            mock_command_instance = MagicMock()
            MockCommand.return_value = mock_command_instance
            await a.reinvoke_agent(decision, uuid.uuid4(), uuid.uuid4())

        MockCommand.assert_called_once_with(resume={"decisions": [decision]})

    @pytest.mark.asyncio
    async def test_exception_raises_custom_exception(self):
        mock_inner_agent = AsyncMock()
        mock_inner_agent.ainvoke.side_effect = Exception("network error")

        a = _make_agent(agent_mock=mock_inner_agent)
        with pytest.raises(Custom_Exception) as exc_info:
            await a.reinvoke_agent({"type": "approve"}, uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR
