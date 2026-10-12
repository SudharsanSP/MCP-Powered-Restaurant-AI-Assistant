"""
Tests for MCP_Client/src/models/model.py
"""
import pytest
from pydantic import ValidationError

from models.model import (
    UserQuery,
    HITLRequest,
    MenuList,
    MenuResponse,
    OrderResponse,
    StatusResponse,
    GeneralResponse,
)


class TestModelSchemas:
    def test_user_query_valid(self):
        q = UserQuery(user_query="Can I have a cappuccino?")
        assert q.user_query == "Can I have a cappuccino?"

    def test_user_query_empty_fails(self):
        with pytest.raises(ValidationError):
            UserQuery(user_query="")

    def test_hitl_request_valid(self):
        req1 = HITLRequest(decision="approve")
        req2 = HITLRequest(decision="reject")
        assert req1.decision == "approve"
        assert req2.decision == "reject"

    def test_hitl_request_invalid(self):
        with pytest.raises(ValidationError):
            HITLRequest(decision="maybe")

    def test_menu_list(self):
        item = MenuList(id=1, name="Espresso", price=120.0)
        assert item.id == 1
        assert item.name == "Espresso"
        assert item.price == 120.0

    def test_menu_response(self):
        resp = MenuResponse(
            model_response="Here is the menu",
            menu_items=MenuList(id=1, name="Latte", price=150.0),
        )
        assert resp.model_response == "Here is the menu"

    def test_order_response(self):
        resp = OrderResponse(
            model_response="Thank you!",
            order_id=1,
            order_items=[MenuList(id=1, name="Latte", price=150.0)],
            total_amount=150,
        )
        assert resp.order_id == 1

    def test_status_response(self):
        resp = StatusResponse(
            model_response="Your order status",
            order_id=1,
            order_status={"status": "ordered"},
        )
        assert resp.order_id == 1

    def test_general_response(self):
        resp = GeneralResponse(model_response="Hello! Welcome to Brew Buddy!")
        assert resp.model_response == "Hello! Welcome to Brew Buddy!"
