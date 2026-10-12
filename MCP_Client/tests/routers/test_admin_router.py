"""
Tests for MCP_Client/src/routers/admin_router.py
"""
import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI, Request

from routers.admin_router import router
from services.dependency import get_admin_service
from services.admin_service import AdminService
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode


@pytest.fixture
def mock_admin_service():
    return AsyncMock(spec=AdminService)


@pytest.fixture
def test_app(mock_admin_service):
    app = FastAPI()

    @app.middleware("http")
    async def add_state(request: Request, call_next):
        request.state.request_id = "test-req-id"
        return await call_next(request)

    app.include_router(router)
    app.dependency_overrides[get_admin_service] = lambda: mock_admin_service
    return app


class TestAdminRouter:
    @pytest.mark.asyncio
    async def test_get_orders_success(self, test_app, mock_admin_service):
        mock_admin_service.get_orders.return_value = [{"order_uuid": str(uuid.uuid4())}]
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            res = await ac.get("/coffee_shop_bot/api/v1/admin/orders")
        assert res.status_code == 200
        assert res.json()["message"] == "Orders fetched successfully"

    @pytest.mark.asyncio
    async def test_update_order_status_success(self, test_app, mock_admin_service):
        order_id = uuid.uuid4()
        mock_admin_service.update_order_status.return_value = {
            "order_uuid": str(order_id),
            "order_status": "processing",
        }
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            res = await ac.patch(f"/coffee_shop_bot/api/v1/admin/orders/{order_id}/status")
        assert res.status_code == 200
        assert res.json()["message"] == "Order status updated successfully"

    @pytest.mark.asyncio
    async def test_create_item_success(self, test_app, mock_admin_service):
        mock_admin_service.create_item.return_value = {
            "item_uuid": str(uuid.uuid4()),
            "name": "Latte",
            "price": 150.0,
        }
        payload = {"name": "Latte", "price": 150.0}
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            res = await ac.post("/coffee_shop_bot/api/v1/admin/items", json=payload)
        assert res.status_code == 201
        assert res.json()["message"] == "Item created successfully"

    @pytest.mark.asyncio
    async def test_update_item_success(self, test_app, mock_admin_service):
        item_id = uuid.uuid4()
        mock_admin_service.update_item.return_value = {
            "item_uuid": str(item_id),
            "name": "Iced Latte",
            "price": 160.0,
        }
        payload = {"name": "Iced Latte", "price": 160.0}
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            res = await ac.patch(f"/coffee_shop_bot/api/v1/admin/items/{item_id}", json=payload)
        assert res.status_code == 200
        assert res.json()["message"] == "Item updated successfully"

    @pytest.mark.asyncio
    async def test_delete_item_success(self, test_app, mock_admin_service):
        item_id = uuid.uuid4()
        mock_admin_service.delete_item.return_value = None
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            res = await ac.delete(f"/coffee_shop_bot/api/v1/admin/items/{item_id}")
        assert res.status_code == 200
        assert res.json()["message"] == "Item deleted successfully"

    @pytest.mark.asyncio
    async def test_get_orders_error_handling(self, test_app, mock_admin_service):
        mock_admin_service.get_orders.side_effect = Custom_Exception(
            message="Database query error",
            code=ErrorCode.DATABASE_ERROR,
            status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
        )
        with pytest.raises(Custom_Exception) as exc_info:
            async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
                await ac.get("/coffee_shop_bot/api/v1/admin/orders")
        assert exc_info.value.code == ErrorCode.DATABASE_ERROR

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("method", "http_method", "path", "payload"),
        [
            ("get_orders", "GET", "/coffee_shop_bot/api/v1/admin/orders", None),
            (
                "update_order_status",
                "PATCH",
                f"/coffee_shop_bot/api/v1/admin/orders/{uuid.uuid4()}/status",
                None,
            ),
            (
                "create_item",
                "POST",
                "/coffee_shop_bot/api/v1/admin/items",
                {"name": "Latte", "price": 150.0},
            ),
            (
                "update_item",
                "PATCH",
                f"/coffee_shop_bot/api/v1/admin/items/{uuid.uuid4()}",
                {"name": "Latte", "price": 150.0},
            ),
            (
                "delete_item",
                "DELETE",
                f"/coffee_shop_bot/api/v1/admin/items/{uuid.uuid4()}",
                None,
            ),
        ],
    )
    async def test_unexpected_service_errors_are_wrapped(
        self, test_app, mock_admin_service, method, http_method, path, payload
    ):
        getattr(mock_admin_service, method).side_effect = RuntimeError("service failure")

        with pytest.raises(Custom_Exception) as exc_info:
            async with AsyncClient(
                transport=ASGITransport(app=test_app), base_url="http://test"
            ) as client:
                await client.request(http_method, path, json=payload)

        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR
