"""
Shared fixtures and environment isolation for MCP_Client tests.
"""
import sys
import os
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock

import pytest

_CLIENT_SRC = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "src")
)
_SERVER_SRC = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "MCP_Server", "src")
)

# Isolate sys.path for MCP_Client
if _SERVER_SRC in sys.path:
    sys.path.remove(_SERVER_SRC)
if _CLIENT_SRC in sys.path:
    sys.path.remove(_CLIENT_SRC)
sys.path.insert(0, _CLIENT_SRC)

# Purge any conflicting modules from server
_CONFLICTING_PREFIXES = (
    "settings", "utilities", "models", "repositories", "tools",
    "routers", "migration", "services", "agents", "client",
    "middleware", "main",
)
for _mod_name in list(sys.modules.keys()):
    for _prefix in _CONFLICTING_PREFIXES:
        if _mod_name == _prefix or _mod_name.startswith(_prefix + "."):
            del sys.modules[_mod_name]
            break


@pytest.fixture
def fake_customer():
    """Returns a MagicMock that looks like a Customer ORM row."""
    customer = MagicMock()
    customer.customer_id = 1
    customer.customer_uuid = uuid.uuid4()
    customer.name = "Alice"
    customer.email = "alice@example.com"
    customer.phone_number = "+91 9876543210"
    customer.role = "user"
    customer.is_active = True
    customer.is_revoked = False
    customer.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    return customer


@pytest.fixture
def fake_admin():
    """Returns a MagicMock that looks like a User (admin) ORM row."""
    admin = MagicMock()
    admin.user_id = 1
    admin.user_uuid = uuid.uuid4()
    admin.name = "Admin"
    admin.email = "admin@example.com"
    admin.role = "admin"
    admin.is_active = True
    admin.is_revoked = False
    admin.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    return admin


@pytest.fixture
def fake_item():
    """Returns a MagicMock that looks like an Item ORM row."""
    item = MagicMock()
    item.item_id = 1
    item.item_uuid = uuid.uuid4()
    item.name = "Espresso"
    item.price = 120.0
    item.is_active = True
    item.created_at = datetime.now(timezone.utc)
    return item


@pytest.fixture
def fake_order(fake_customer, fake_item):
    """Returns a MagicMock that looks like an Order ORM row with nested relations."""
    from repositories.schema.coffee_shop_models import OrderStatus

    order_item = MagicMock()
    order_item.item = fake_item
    order_item.item_count = 2

    order = MagicMock()
    order.order_id = 1
    order.order_uuid = uuid.uuid4()
    order.customer_id = fake_customer.customer_id
    order.customer = fake_customer
    order.total_amount = 240.0
    order.order_status = OrderStatus.ordered
    order.order_items = [order_item]
    order.created_at = datetime.now(timezone.utc)
    order.updated_at = None
    order.is_active = True
    return order


@pytest.fixture
def mock_db_session():
    """Returns an AsyncMock that behaves like an SQLAlchemy AsyncSession."""
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session
