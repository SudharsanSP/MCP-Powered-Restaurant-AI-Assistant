from __future__ import annotations

import boto3
from langchain_aws import ChatBedrock
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from settings import config
from utilities.logger import get_logger

logger = get_logger(__name__)


def create_bedrock_client():
    logger.info("Creating shared Bedrock runtime client for region=%s", config.aws_region)
    return boto3.client(
        service_name="bedrock-runtime",
        region_name=config.aws_region,
    )


def create_chatbedrock(bedrock_client, max_tokens: int, temperature: float):
    logger.info(
        "Creating shared ChatBedrock model with max_tokens=%s temperature=%s",
        max_tokens,
        temperature,
    )
    return ChatBedrock(
        client=bedrock_client,
        model_id=config.model_id,
        provider="amazon",
        model_kwargs={
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
    )


def create_mcp_client():
    logger.info("Creating shared MCP client for URL=%s", config.mcp_url)
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