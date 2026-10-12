"""
Tests for MCP_Client/src/repositories/schema/coffee_shop_models.py

Covers: ORM model construction, column existence, foreign keys,
        relationships, and the OrderStatus enum.
No DB connection required — tests only Python / SQLAlchemy metadata.
"""
import sys
import os

CLIENT_SRC = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "MCP_Client", "src"
)
if CLIENT_SRC not in sys.path:
    sys.path.insert(0, CLIENT_SRC)

import pytest
from repositories.schema.coffee_shop_models import (
    User, Customer, Item, Order, Order_Item, OrderStatus, Base
)


class TestOrderStatus:
    def test_all_statuses_exist(self):
        assert OrderStatus.ordered.value == "ordered"
        assert OrderStatus.processing.value == "processing"
        assert OrderStatus.pending.value == "pending"
        assert OrderStatus.completed.value == "completed"

    def test_is_python_enum(self):
        import enum
        assert issubclass(OrderStatus, enum.Enum)

    def test_four_statuses_defined(self):
        assert len(list(OrderStatus)) == 4


class TestUserModel:
    def test_tablename(self):
        assert User.__tablename__ == "users"

    def test_required_columns_present(self):
        cols = {c.name for c in User.__table__.columns}
        for col in ("user_id", "user_uuid", "name", "email", "password_hash", "role", "is_active"):
            assert col in cols, f"Column '{col}' missing from User"

    def test_can_instantiate(self):
        u = User(name="Admin", email="a@a.com", password_hash="h")
        assert u.email == "a@a.com"


class TestCustomerModel:
    def test_tablename(self):
        assert Customer.__tablename__ == "customers"

    def test_required_columns_present(self):
        cols = {c.name for c in Customer.__table__.columns}
        for col in (
            "customer_id", "customer_uuid", "name", "phone_number",
            "email", "password_hash", "role", "refresh_token",
            "is_revoked", "expires_at", "is_active",
        ):
            assert col in cols, f"Column '{col}' missing from Customer"

    def test_can_instantiate(self):
        c = Customer(name="Alice", phone_number="+91 9876543210",
                     email="alice@example.com", password_hash="h")
        assert c.name == "Alice"


class TestItemModel:
    def test_tablename(self):
        assert Item.__tablename__ == "items"

    def test_required_columns_present(self):
        cols = {c.name for c in Item.__table__.columns}
        for col in ("item_id", "item_uuid", "name", "price", "is_active"):
            assert col in cols

    def test_can_instantiate(self):
        item = Item(name="Latte", price=130.0)
        assert item.price == 130.0


class TestOrderModel:
    def test_tablename(self):
        assert Order.__tablename__ == "orders"

    def test_required_columns_present(self):
        cols = {c.name for c in Order.__table__.columns}
        for col in ("order_id", "order_uuid", "customer_id", "total_amount", "order_status", "is_active"):
            assert col in cols

    def test_customer_fk_exists(self):
        fks = {fk.column.table.name for fk in Order.__table__.foreign_keys}
        assert "customers" in fks

    def test_can_instantiate(self):
        o = Order(customer_id=1, total_amount=250.0)
        assert o.total_amount == 250.0


class TestOrderItemModel:
    def test_tablename(self):
        assert Order_Item.__tablename__ == "order_items"

    def test_required_columns_present(self):
        cols = {c.name for c in Order_Item.__table__.columns}
        for col in ("order_item_id", "order_id", "item_id", "item_count"):
            assert col in cols

    def test_both_fks_exist(self):
        fks = {fk.column.table.name for fk in Order_Item.__table__.foreign_keys}
        assert "orders" in fks
        assert "items" in fks

    def test_can_instantiate(self):
        oi = Order_Item(order_id=1, item_id=2, item_count=3)
        assert oi.item_count == 3
