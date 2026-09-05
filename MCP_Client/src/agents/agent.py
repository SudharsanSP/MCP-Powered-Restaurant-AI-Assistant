from uuid import UUID
from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware, SummarizationMiddleware
from langchain.agents.structured_output import ToolStrategy
from langchain.agents.structured_output import StructuredOutputValidationError, MultipleStructuredOutputsError
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from models.model import MenuResponse, OrderResponse, StatusResponse
from agents.prompt import Prompt
from utilities.logger import get_logger

logger = get_logger(__name__)

class Agent:
    def __init__(self, agent, mcp_client):
        self.agent = agent
        self.mcp_client = mcp_client

    async def get_tools(self):
        logger.info("Loading tools from the shared MCP client")
        tools = await self.mcp_client.get_tools()
        logger.info("Loaded %s tools from the MCP server", len(tools))
        return tools

    def call_agent_factory(self, model, summary_model, tools, checkpointer):
        logger.info("Creating the shared LangChain agent")
        prompt = Prompt()
        return create_agent(
            model=model,
            tools=tools,
            middleware=[
                SummarizationMiddleware(
                    model=summary_model,
                    trigger=("messages", 5),
                    keep=("messages", 2),
                    system_prompt=prompt.summary_system_prompt(),
                ),
                PIIMiddleware(
                    "email",
                    strategy="redact",
                    apply_to_input=True,
                    apply_to_output=True,
                ),
            ],
            response_format=ToolStrategy(
                schema=OrderResponse | StatusResponse | MenuResponse,
                handle_errors=self.custom_error_handler,
            ),
            system_prompt=prompt.get_system_prompt(),
            checkpointer=checkpointer,
        )

    @staticmethod
    def custom_error_handler(error: Exception):
        if isinstance(error, StructuredOutputValidationError):
            logger.warning("Structured output validation failed: %s", error)
            return "Schema validation failed. Check filed constraints and retry"
        elif isinstance(error, MultipleStructuredOutputsError):
            logger.warning("Agent returned multiple structured outputs")
            return "Multiple outputs were returned, pick the single format that is more relevant"
        else:
            logger.error(
                "Agent returned an unexpected structured output error",
                extra={"exception": str(error)},
            )
            return f"Unexpected error: {str(error)}"

    async def call_agent(self, request, customer_id: UUID):
        try:
            logger.info("Starting agent execution for customer_id=%s", customer_id)
            messages = [
                (
                    "user",
                    f"customer_id={customer_id}; query={request.user_query}",
                )
            ]

            result = await self.agent.ainvoke(
                {"messages": messages},
                {"configurable": {"thread_id": str(customer_id)}},
            )
            logger.info("Agent returned structured result for customer_id=%s", customer_id)
            print(result)
            return result.get("structured_response")
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Agent execution failed for customer_id=%s", customer_id)
            raise Custom_Exception(
            message="The assistant could not complete the request.",
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )
