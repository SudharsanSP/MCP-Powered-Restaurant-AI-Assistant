from typing import Union
import boto3
from langchain_aws import ChatBedrock
from agents.prompt import Prompt
from settings import config
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.prompts import load_mcp_prompt
from langchain_mcp_adapters.resources import load_mcp_resources
from langchain.agents import create_agent
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain.agents.middleware import SummarizationMiddleware, PIIMiddleware
from langchain.agents.structured_output import StructuredOutputValidationError, MultipleStructuredOutputsError, ToolStrategy
from models.model  import OrderResponse, StatusResponse, MenuResponse
from utilities.error_log import error_logger
from utilities.logger import get_logger

logger = get_logger(__name__)

PROMPT_ARGS = {
    "order_assistant": {"use":"assist customers in ordering"},
    "order_status": {"use":"assist customers in getting order details and order updates"}
}
DB_URL=f"postgresql://{config.db_username}:{config.db_password}@{config.db_host}:{config.db_port}/{config.db_name}"

system_prompt = Prompt()
class Agent:
    async def get_bedrock_client(self):
        try:   
            logger.info(f"bedrock client creation {logger}")
            print("bedrockClient")
            return boto3.client(
                service_name="bedrock-runtime",
                # aws_access_key_id= config.aws_access_key ,
                # aws_secret_access_key= config.aws_secret_key,
                region_name=config.aws_region
            )
        except Custom_Exception:
            raise
        except Exception as e:
            error_logger(
                file_name = 'agent.py',
                function_name = 'get_bedrock_client', 
                error_message = str(e)
            )
            raise Custom_Exception(
                message=f"bedrock client creation error: {str(e)}",
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def create_llm_model(self, max_token =config.max_token, temperature=config.temperature):
        try:
            logger.info("Creating ChatBedrock model with max_tokens=%s temperature=%s", max_token, temperature)
            return ChatBedrock(
                client= await self.get_bedrock_client(),
                model_id=config.model_id,
                provider="amazon",
                model_kwargs={
                    "max_tokens": max_token,
                    "temperature":temperature,
                }
            )
        except Custom_Exception:
            raise
        except Exception as e:
            error_logger(
                file_name = 'agent.py',
                function_name = 'create_llm_model', 
                error_message = str(e)
            )
            raise Custom_Exception(
                message=f"creating llm_model error: {str(e)}",
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )
        
    async def create_mcp_client(self):
        try:
            logger.info("Initializing MCP client for URL=%s", config.mcp_url)
            return  MultiServerMCPClient(
                    {
                        "my_server":{
                            "transport":"streamable_http",
                            "url": config.mcp_url
                        }
                    }
            )
        except Custom_Exception:
            raise
        except Exception as e:
            error_logger(
                file_name = 'agent.py',
                function_name = 'create_mcp_client', 
                error_message = str(e)
            )
            raise Custom_Exception(
                message=f"creating Multi Server MCP Cient error: {str(e)}",
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )
   
    # async def create_agent_instance(self, checkpointer):
        # try:
        #     logger.info(f"create agent {logger}")
        #     llm_model = await self.create_llm_model()
        #     client = await self.create_mcp_client()
        #     tools = await client.get_tools()
        #     agent_prompt = system_prompt.get_system_prompt()
        #     summary_prompt = system_prompt.summary_system_prompt()
        #     return create_agent(
        #             model=llm_model,
        #             tools=tools,
        #             middleware= [
        #                 SummarizationMiddleware(
        #                     model = await self.create_llm_model(max_token = 150, temperature =0.5),
        #                     trigger= ("messages", 10),
        #                     keep=("messages", 2),
        #                     system_prompt = summary_prompt,
        #                 ),
        #                 PIIMiddleware(
        #                     "email",
        #                     strategy="redact",
        #                     apply_to_input=True,
        #                     apply_to_output=True,                        
        #                 ),
        #             ],
        #             response_format= ToolStrategy(
        #                 schema= Union[OrderResponse, StatusResponse, MenuResponse],
        #                 handle_errors= self.custom_error_handler
        #             ),
        #             system_prompt=agent_prompt,
        #             checkpointer=checkpointer
        #     )
        # except Custom_Exception:
        #     raise
        # except Exception as e:
        #     error_logger(
        #         file_name = 'agent.py',
        #         function_name = 'create_agent_instance', 
        #         error_message = str(e)
        #     )
        #     raise Custom_Exception(
        #         message=f"creating agent error: {str(e)}",
        #         code=ErrorCode.INTERNAL_SERVER_ERROR,
        #         status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
        #     )
        
    def custom_error_handler(self, error: Exception):
        if isinstance(error, StructuredOutputValidationError):
            return "Schema validation failed. Check filed constraints and retry"
        elif isinstance(error, MultipleStructuredOutputsError):
            return "Multiple outputs were returned, pick the single format that is more relevant"
        else:
            return f"Unexpected error: {str(error)}"

    async def call_agent(self, request, customer_id):
        try:
            logger.info("Starting agent execution for customer_id=%s", customer_id)
            async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpointer:
                await checkpointer.setup()
                client = await self.create_mcp_client()
                llm_model = await self.create_llm_model()
                tools = await client.get_tools()
                agent_prompt = system_prompt.get_system_prompt()
                summary_prompt = system_prompt.summary_system_prompt()

                agent = create_agent(
                    model=llm_model,
                    tools=tools,
                    middleware= [
                        SummarizationMiddleware(
                            model = await self.create_llm_model(max_token = 150, temperature =0.5),
                            trigger= ("messages", 10),
                            keep=("messages", 2),
                            system_prompt = summary_prompt,
                        ),
                        PIIMiddleware(
                            "email",
                            strategy="redact",
                            apply_to_input=True,
                            apply_to_output=True,                        
                        ),
                    ],
                    response_format= ToolStrategy(
                        schema= Union[OrderResponse, StatusResponse, MenuResponse],
                        handle_errors= self.custom_error_handler
                    ),
                    system_prompt=agent_prompt,
                    checkpointer=checkpointer
                )
     
                async with client.session("my_server") as session:
                    list_result      = await session.list_prompts()
                    available_prompts = list_result.prompts

                    all_prompt_messages = []
                    for prompt in available_prompts:
                        # print(prompt, "************"*20)
                        args     = PROMPT_ARGS.get(prompt.name, {})
                        messages = await load_mcp_prompt(session, prompt.name, arguments=args)
                        # print(messages,"++++++++++++"*15)
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
                    messages.append(("user",f"hey, my customer_id is {customer_id}, {request.user_query}" ))
                # print(request.user_query)
                result = await agent.ainvoke(
                    {"messages": messages},
                    {"configurable": {"thread_id": customer_id}}
                )
                logger.info("Agent returned structured result for customer_id=%s", customer_id)
                final_result = result.get('structured_response')
                return final_result
        except Custom_Exception:
            raise
        except Exception as e:
            logger.exception("Agent execution failed for customer_id=%s", customer_id)
            error_logger(
                file_name='agent.py',
                function_name='call_agent',
                error_message=str(e),
            )
            raise Custom_Exception(
                message=f"calling agent error: {str(e)}",
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )
