"""
Tests for MCP_Client/src/client/client.py

Functions under test:
  - create_chat_model(max_tokens, temperature)
  - create_mcp_client()
  - create_checkpointer()

Strategy:
  - Patch the third-party constructors (ChatGoogleGenerativeAI,
    MultiServerMCPClient, AsyncPostgresSaver.from_conn_string) so no network
    connections or API keys are needed.
  - Verify that correct arguments are forwarded and that exceptions are wrapped
    in Custom_Exception.
"""
import sys
import os
from unittest.mock import MagicMock, patch

import pytest

CLIENT_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "..", "MCP_Client", "src")
if CLIENT_SRC not in sys.path:
    sys.path.insert(0, CLIENT_SRC)

from utilities.exceptions.custom_exception import Custom_Exception


# --------------------------------------------------------------------------- #
# create_chat_model                                                             #
# --------------------------------------------------------------------------- #
class TestCreateChatModel:
    def test_returns_model_instance(self):
        mock_model = MagicMock()

        with patch("client.client.ChatGoogleGenerativeAI", return_value=mock_model) as MockLLM, \
             patch("client.client.config") as mock_cfg:
            mock_cfg.gemini_model = "gemini-2.5-flash"
            mock_cfg.google_api_key = "fake-key"

            from client.client import create_chat_model
            result = create_chat_model(500, 0.1)

        MockLLM.assert_called_once()
        assert result is mock_model

    def test_passes_max_tokens_and_temperature(self):
        with patch("client.client.ChatGoogleGenerativeAI") as MockLLM, \
             patch("client.client.config") as mock_cfg:
            mock_cfg.gemini_model = "gemini-2.5-flash"
            mock_cfg.google_api_key = "key"

            from client.client import create_chat_model
            create_chat_model(200, 0.7)

        kwargs = MockLLM.call_args.kwargs
        assert kwargs["max_output_tokens"] == 200
        assert kwargs["temperature"] == 0.7

    def test_exception_wrapped_in_custom_exception(self):
        with patch("client.client.ChatGoogleGenerativeAI", side_effect=Exception("API error")), \
             patch("client.client.config") as mock_cfg:
            mock_cfg.gemini_model = "gemini"
            mock_cfg.google_api_key = "key"

            from client.client import create_chat_model
            with pytest.raises(Custom_Exception):
                create_chat_model(100, 0.1)


# --------------------------------------------------------------------------- #
# create_mcp_client                                                             #
# --------------------------------------------------------------------------- #
class TestCreateMcpClient:
    def test_returns_mcp_client_instance(self):
        mock_client = MagicMock()

        with patch("client.client.MultiServerMCPClient", return_value=mock_client) as MockMCP, \
             patch("client.client.config") as mock_cfg:
            mock_cfg.mcp_url = "http://localhost:8081"

            from client.client import create_mcp_client
            result = create_mcp_client()

        MockMCP.assert_called_once()
        assert result is mock_client

    def test_uses_config_mcp_url(self):
        with patch("client.client.MultiServerMCPClient") as MockMCP, \
             patch("client.client.config") as mock_cfg:
            mock_cfg.mcp_url = "http://mcp-server:9000/mcp"

            from client.client import create_mcp_client
            create_mcp_client()

        args = MockMCP.call_args[0][0]          # first positional arg = config dict
        assert args["my_server"]["url"] == "http://mcp-server:9000/mcp"
        assert args["my_server"]["transport"] == "streamable_http"

    def test_exception_wrapped_in_custom_exception(self):
        with patch("client.client.MultiServerMCPClient", side_effect=Exception("connection refused")), \
             patch("client.client.config") as mock_cfg:
            mock_cfg.mcp_url = "http://x"

            from client.client import create_mcp_client
            with pytest.raises(Custom_Exception):
                create_mcp_client()


# --------------------------------------------------------------------------- #
# create_checkpointer                                                           #
# --------------------------------------------------------------------------- #
class TestCreateCheckpointer:
    def test_returns_checkpointer_instance(self):
        mock_cp = MagicMock()

        with patch("client.client.AsyncPostgresSaver") as MockSaver, \
             patch("client.client.config") as mock_cfg:
            mock_cfg.db_username = "user"
            mock_cfg.db_password = "pass"
            mock_cfg.db_host = "localhost"
            mock_cfg.db_port = "5432"
            mock_cfg.db_name = "testdb"
            MockSaver.from_conn_string.return_value = mock_cp

            from client.client import create_checkpointer
            result = create_checkpointer()

        MockSaver.from_conn_string.assert_called_once()
        assert result is mock_cp

    def test_db_url_uses_config_values(self):
        with patch("client.client.AsyncPostgresSaver") as MockSaver, \
             patch("client.client.config") as mock_cfg:
            mock_cfg.db_username = "admin"
            mock_cfg.db_password = "secret"
            mock_cfg.db_host = "db-host"
            mock_cfg.db_port = "5433"
            mock_cfg.db_name = "coffeedb"

            from client.client import create_checkpointer
            create_checkpointer()

        conn_string = MockSaver.from_conn_string.call_args[0][0]
        assert "admin" in conn_string
        assert "db-host" in conn_string
        assert "5433" in conn_string
        assert "coffeedb" in conn_string

    def test_exception_wrapped_in_custom_exception(self):
        with patch("client.client.AsyncPostgresSaver") as MockSaver, \
             patch("client.client.config") as mock_cfg:
            mock_cfg.db_username = "u"
            mock_cfg.db_password = "p"
            mock_cfg.db_host = "h"
            mock_cfg.db_port = "5432"
            mock_cfg.db_name = "d"
            MockSaver.from_conn_string.side_effect = Exception("DB unavailable")

            from client.client import create_checkpointer
            with pytest.raises(Custom_Exception):
                create_checkpointer()
