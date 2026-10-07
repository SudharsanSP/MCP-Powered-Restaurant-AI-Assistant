from uuid import UUID
from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware, SummarizationMiddleware, HumanInTheLoopMiddleware
from langchain.agents.structured_output import ToolStrategy
from langchain.agents.structured_output import StructuredOutputValidationError, MultipleStructuredOutputsError
from langgraph.types import Command
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from models.model import MenuResponse, OrderResponse, StatusResponse
from agents.prompt import Prompt
from utilities.logger import get_logger

logger = get_logger(__name__)

@staticmethod
def custom_error_handler(error: Exception):
    if isinstance(error, StructuredOutputValidationError):
        logger.warning("Structured output validation failed")
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

class Agent:
    def __init__(self, agent, mcp_client):
        self.agent = agent
        self.mcp_client = mcp_client

    async def get_tools(self):
        logger.info("Loading tools from the shared MCP client")
        tools = await self.mcp_client.get_tools()
        logger.info("Loaded MCP tools")
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
                    trigger=("fraction", 0.2),
                    keep=("messages", 2),
                    system_prompt=prompt.summary_system_prompt(),
                ),
                PIIMiddleware(
                    "email",
                    strategy="redact",
                    apply_to_input=True,
                    apply_to_output=True,
                ),
                HumanInTheLoopMiddleware(
                    interrupt_on={
                        "place_order_tool": {"allowed_decisions": ["approve", "reject"]},
                        "update_order_tool": {"allowed_decisions": ["approve", "reject"]},
                        "cancel_order_tool": {"allowed_decisions": ["approve", "reject"]},
                    },
                    description_prefix="Approval required before modifying order",
                )
            ],
            # response_format=ToolStrategy(
            #     schema=OrderResponse | StatusResponse | MenuResponse,
            #     handle_errors=custom_error_handler,
            # ),
            system_prompt=prompt.get_system_prompt(),
            checkpointer=checkpointer,
        )


    async def call_agent(self, request, thread_id: UUID, customer_id: UUID):
        try:
            logger.info("Starting agent execution")
            messages = [
                (
                    "user",
                    f"customer_id={customer_id}; query={request.user_query}",
                )
            ]

            result = await self.agent.ainvoke(
                {"messages": messages},
                {"configurable": {"thread_id": str(thread_id)}},
            )
            print(result)
            if "__interrupt__" in result:
                logger.info("Agent returned response with interruption")
                return  result["__interrupt__"][0].value["action_requests"][0]["description"]
            logger.info("Agent returned structured result")
            # return result.get("structured_response")
            return result["messages"][-1].content[0]["text"]
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Agent execution failed")
            raise Custom_Exception(
            message="The assistant could not complete the request.",
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def reinvoke_agent(self, decision, thread_id: UUID, customer_id: UUID):
            try:
                logger.info("Starting agent re-execution")
                result = await self.agent.ainvoke(
                    Command(
                        resume={
                            "decisions": [decision]
                        }
                    ),
                    {"configurable": {"thread_id": str(thread_id)}},
                )
                logger.info("Agent returned structured result")
                print(result)
                # return result.get("structured_response")
                return result["messages"][-1].content[0]["text"]
            except Custom_Exception:
                raise
            except Exception:
                logger.exception("Agent execution failed")
                raise Custom_Exception(
                message="The assistant could not complete the request.",
                    code=ErrorCode.INTERNAL_SERVER_ERROR,
                    status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
                )
