"""
Tests for MCP_Client/src/models/admin.py
"""
from datetime import datetime
import pytest
from pydantic import ValidationError

from models.admin import (
    CustomerDetails,
    OrderItems,
    GetOrdersResponse,
    UpdateOrderStatusResponse,
    ItemResponse,
    CreateItemRequest,
    UpdateItemRequest,
)


class TestAdminModels:
    def test_customer_details(self):
        c = CustomerDetails(
            customer_uuid="uuid-1",
            name="Alice",
            phone_number="1234567890",
        )
        assert c.name == "Alice"
        assert c.customer_uuid == "uuid-1"

    def test_order_items(self):
        item = OrderItems(name="Latte", price=150.0, count=2)
        assert item.name == "Latte"
        assert item.price == 150.0
        assert item.count == 2

    def test_get_orders_response(self):
        resp = GetOrdersResponse(
            order_uuid="order-1",
            order_status="ordered",
            total_amount=300.0,
            ordered_at=datetime.now(),
            customer=CustomerDetails(
                customer_uuid="cust-1", name="Alice", phone_number="1234567890"
            ),
            items=[OrderItems(name="Latte", price=150.0, count=2)],
        )
        assert resp.order_uuid == "order-1"
        assert len(resp.items) == 1

    def test_update_order_status_response(self):
        resp = UpdateOrderStatusResponse(
            order_uuid="order-1",
            order_status="completed",
            updated_at=datetime.now(),
        )
        assert resp.order_status == "completed"

    def test_item_response(self):
        resp = ItemResponse(
            item_uuid="item-1",
            name="Mocha",
            price=180.0,
            created_at=datetime.now(),
        )
        assert resp.name == "Mocha"

    def test_create_item_request_valid(self):
        req = CreateItemRequest(name="Cappuccino", price=140.0)
        assert req.name == "Cappuccino"
        assert req.price == 140.0

    def test_create_item_request_invalid_price(self):
        with pytest.raises(ValidationError):
            CreateItemRequest(name="Cappuccino", price=0.0)

    def test_create_item_request_empty_name(self):
        with pytest.raises(ValidationError):
            CreateItemRequest(name="", price=100.0)

    def test_update_item_request(self):
        req = UpdateItemRequest(name="Updated", price=200.0, is_active=False)
        assert req.name == "Updated"
        assert req.price == 200.0
        assert req.is_active is False
