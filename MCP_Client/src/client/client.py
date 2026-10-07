from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from settings import config
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger

logger = get_logger(__name__)


def create_chat_model(max_tokens: int, temperature: float):
    try:
        logger.info("Creating shared Gemini model")
        return ChatGoogleGenerativeAI(
            model=config.gemini_model,
            google_api_key=config.google_api_key,
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Failed to create Gemini model")
        raise Custom_Exception(
            message="The chat model could not be initialized.",
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
        )


def create_mcp_client():
    try:
        logger.info("Creating shared MCP client")
        return MultiServerMCPClient(
            {
                "my_server": {
                    "transport": "streamable_http",
                    "url": config.mcp_url,
                }
            }
        )
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Failed to create MCP client")
        raise Custom_Exception(
            message="The MCP client could not be initialized.",
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
        )


def create_checkpointer():
    try:
        logger.info("Creating shared PostgreSQL checkpointer")
        db_url = (
            f"postgresql://{config.db_username}:{config.db_password}"
            f"@{config.db_host}:{config.db_port}/{config.db_name}"
        )
        return AsyncPostgresSaver.from_conn_string(db_url)
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Failed to create PostgreSQL checkpointer")
        raise Custom_Exception(
            message="The checkpointer could not be initialized.",
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
        )
