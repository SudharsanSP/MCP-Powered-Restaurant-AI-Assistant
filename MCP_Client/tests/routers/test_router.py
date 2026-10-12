"""
Tests for MCP_Client/src/routers/router.py
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI, Request

from routers.router import router
from services.dependency import get_chatbot_service
from services.service import ChatBotService
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode


@pytest.fixture
def mock_chatbot_service():
    return AsyncMock(spec=ChatBotService)


@pytest.fixture
def test_app(mock_chatbot_service):
    app = FastAPI()

    @app.middleware("http")
    async def add_state(request: Request, call_next):
        request.state.request_id = "test-chat-req-id"
        return await call_next(request)

    app.include_router(router)
    app.dependency_overrides[get_chatbot_service] = lambda: mock_chatbot_service
    return app


class TestChatBotRouter:
    @pytest.mark.asyncio
    async def test_chat_bot_router_success(self, test_app, mock_chatbot_service):
        thread_id = uuid.uuid4()
        mock_chatbot_service.chat_bot_service.return_value = {
            "model_response": "Hello! Welcome to Brew Buddy."
        }
        with patch("routers.router.customer_id_context") as mock_ctx:
            mock_ctx.get.return_value = uuid.uuid4()
            payload = {"user_query": "Hello!"}
            async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
                res = await ac.post(f"/coffee_shop_bot/api/v1/chat_bot/{thread_id}", json=payload)

        assert res.status_code == 200
        assert res.json()["data"]["model_response"] == "Hello! Welcome to Brew Buddy."

    @pytest.mark.asyncio
    async def test_chat_bot_approval_success(self, test_app, mock_chatbot_service):
        thread_id = uuid.uuid4()
        mock_chatbot_service.chat_bot_hitl_service.return_value = {
            "model_response": "Order confirmed!"
        }
        with patch("routers.router.customer_id_context") as mock_ctx:
            mock_ctx.get.return_value = uuid.uuid4()
            payload = {"decision": "approve"}
            async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
                res = await ac.post(f"/coffee_shop_bot/api/v1/chat_bot/{thread_id}/approval", json=payload)

        assert res.status_code == 200
        assert res.json()["data"]["model_response"] == "Order confirmed!"

    @pytest.mark.asyncio
    async def test_chat_bot_router_custom_exception(self, test_app, mock_chatbot_service):
        thread_id = uuid.uuid4()
        mock_chatbot_service.chat_bot_service.side_effect = Custom_Exception(
            message="Agent invocation failed",
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
        )
        with patch("routers.router.customer_id_context") as mock_ctx:
            mock_ctx.get.return_value = uuid.uuid4()
            payload = {"user_query": "Order latte"}
            with pytest.raises(Custom_Exception) as exc_info:
                async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
                    await ac.post(f"/coffee_shop_bot/api/v1/chat_bot/{thread_id}", json=payload)
        assert exc_info.value.code == ErrorCode.INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_chat_bot_router_unhandled_exception(self, test_app, mock_chatbot_service):
        thread_id = uuid.uuid4()
        mock_chatbot_service.chat_bot_service.side_effect = RuntimeError("Crash")
        with patch("routers.router.customer_id_context") as mock_ctx:
            mock_ctx.get.return_value = uuid.uuid4()
            payload = {"user_query": "Hello!"}
            with pytest.raises(Custom_Exception) as exc_info:
                async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
                    await ac.post(f"/coffee_shop_bot/api/v1/chat_bot/{thread_id}", json=payload)
        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR
