from settings import config
from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware, SummarizationMiddleware
from langchain.agents.structured_output import ToolStrategy
from langchain_mcp_adapters.prompts import load_mcp_prompt
from langchain_mcp_adapters.resources import load_mcp_resources
from langchain.agents.structured_output import StructuredOutputValidationError, MultipleStructuredOutputsError
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from models.model import MenuResponse, OrderResponse, StatusResponse
from agents.prompt import Prompt
from utilities.logger import get_logger

logger = get_logger(__name__)

PROMPT_ARGS = {
    "order_assistant": {"use":"assist customers in ordering"},
    "order_status": {"use":"assist customers in getting order details and order updates"}
}
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
                    trigger=("messages", 10),
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
            logger.error("Agent returned an unexpected structured output error: %s", error)
            return f"Unexpected error: {str(error)}"

    async def call_agent(self, request, customer_id):
        try:
            logger.info("Starting agent execution for customer_id=%s", customer_id)
            async with self.mcp_client.session("my_server") as session:
                list_result = await session.list_prompts()
                available_prompts = list_result.prompts

                all_prompt_messages = []
                for prompt in available_prompts:
                    args = PROMPT_ARGS.get(prompt.name, {})
                    messages = await load_mcp_prompt(session, prompt.name, arguments=args)
                    all_prompt_messages.extend(messages)

                blobs = await load_mcp_resources(session)
                resource_context = ""
                for blob in blobs:
                    uri = blob.metadata.get("uri", "unknown")
                    text = blob.as_bytes().decode("utf-8", errors="replace")
                    resource_context += f"\n[{uri}]\n{text}\n"

                messages = list(all_prompt_messages)
                if resource_context:
                    messages.append(
                        f"Here are the available resources:\n{resource_context}"
                    )
                messages.append(("user", f"hey, my customer_id is {customer_id}, {request.user_query}"))

            result = await self.agent.ainvoke(
                {"messages": messages},
                {"configurable": {"thread_id": customer_id}},
            )
            logger.info("Agent returned structured result for customer_id=%s", customer_id)
            return result.get("structured_response")
        except Custom_Exception:
            raise
        except Exception as e:
            logger.exception("Agent execution failed for customer_id=%s", customer_id)
            raise Custom_Exception(
                message=f"calling agent error: {str(e)}",
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )
