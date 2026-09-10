from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from settings import config
from utilities.logger import get_logger

logger = get_logger(__name__)


def create_chat_model(max_tokens: int, temperature: float):
    logger.info("Creating shared Gemini model")
    return ChatGoogleGenerativeAI(
        model=config.gemini_model,
        google_api_key=config.google_api_key,
        max_output_tokens=max_tokens,
        temperature=temperature,
    )


def create_mcp_client():
    logger.info("Creating shared MCP client")
    return MultiServerMCPClient(
        {
            "my_server": {
                "transport": "streamable_http",
                "url": config.mcp_url,
            }
        }
    )


def create_checkpointer():
    logger.info("Creating shared PostgreSQL checkpointer")
    db_url = (
        f"postgresql://{config.db_username}:{config.db_password}"
        f"@{config.db_host}:{config.db_port}/{config.db_name}"
    )
    return AsyncPostgresSaver.from_conn_string(db_url)