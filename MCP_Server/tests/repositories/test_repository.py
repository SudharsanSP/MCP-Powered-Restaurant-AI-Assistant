"""
Tests for MCP_Server/src/repositories/repository.py

Class under test: ChatBotRepository

All methods are tested against an AsyncMock session — no real database.

Key gotcha: get_customer() takes a UUID (customer_uuid column), while
get_order() / get_recent_orders() take the integer PK (customer_id).
"""
import sys
import os
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

SERVER_SRC = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "MCP_Server", "src"
)
if SERVER_SRC not in sys.path:
    sys.path.insert(0, SERVER_SRC)

from repositories.repository import ChatBotRepository
from repositories.schema.coffee_shop_models import OrderStatus
from utilities.exceptions.custom_exception import Custom_Exception


# --------------------------------------------------------------------------- #
# Session helpers                                                               #
# --------------------------------------------------------------------------- #
def _session_scalar_one_or_none(row):
    """Session where execute().scalar_one_or_none() returns row."""
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = row
    session.execute.return_value = result
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


def _session_scalars_all(rows):
    """Session where execute().scalars().all() returns rows."""
    session = AsyncMock()
    result = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = rows
    result.scalars.return_value = scalars
    session.execute.return_value = result
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


def _session_result_all(rows):
    """Session where execute().all() returns rows (used for JOIN queries)."""
    session = AsyncMock()
    result = MagicMock()
    result.all.return_value = rows
    session.execute.return_value = result
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


# --------------------------------------------------------------------------- #
# get_customer                                                                  #
# --------------------------------------------------------------------------- #
class TestGetCustomer:
    @pytest.mark.asyncio
    async def test_returns_customer_when_found(self, fake_customer):
        session = _session_scalar_one_or_none(fake_customer)
        repo = ChatBotRepository()
        result = await repo.get_customer(session, fake_customer.customer_uuid)
        assert result is fake_customer

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        session = _session_scalar_one_or_none(None)
        repo = ChatBotRepository()
        result = await repo.get_customer(session, uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_db_error_raises_custom_exception(self):
        session = AsyncMock()
        session.execute.side_effect = Exception("DB down")
        repo = ChatBotRepository()
        with pytest.raises(Custom_Exception):
            await repo.get_customer(session, uuid.uuid4())


# --------------------------------------------------------------------------- #
# get_order                                                                     #
# --------------------------------------------------------------------------- #
class TestGetOrder:
    @pytest.mark.asyncio
    async def test_returns_latest_order(self, fake_order):
        session = _session_scalar_one_or_none(fake_order)
        repo = ChatBotRepository()
        result = await repo.get_order(session, 1)
        assert result is fake_order

    @pytest.mark.asyncio
    async def test_returns_none_when_no_order(self):
        session = _session_scalar_one_or_none(None)
        repo = ChatBotRepository()
        result = await repo.get_order(session, 99)
        assert result is None

    @pytest.mark.asyncio
    async def test_db_error_raises_custom_exception(self):
        session = AsyncMock()
        session.execute.side_effect = Exception("connection lost")
        repo = ChatBotRepository()
        with pytest.raises(Custom_Exception):
            await repo.get_order(session, 1)


class TestGetOrderDetails:
    @pytest.mark.asyncio
    async def test_returns_active_order_items(self):
        order_items = [MagicMock(), MagicMock()]
        session = _session_scalars_all(order_items)

        result = await ChatBotRepository().get_order_details(session, 1)

        assert result == order_items

    @pytest.mark.asyncio
    async def test_db_error_raises_custom_exception(self):
        session = AsyncMock()
        session.execute.side_effect = RuntimeError("database unavailable")

        with pytest.raises(Custom_Exception):
            await ChatBotRepository().get_order_details(session, 1)


# --------------------------------------------------------------------------- #
# validate_item                                                                 #
# --------------------------------------------------------------------------- #
class TestValidateItem:
    @pytest.mark.asyncio
    async def test_returns_item_when_found(self, fake_item):
        session = _session_scalar_one_or_none(fake_item)
        repo = ChatBotRepository()
        result = await repo.validate_item(session, fake_item.item_id)
        assert result is fake_item

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        session = _session_scalar_one_or_none(None)
        repo = ChatBotRepository()
        result = await repo.validate_item(session, 999)
        assert result is None

    @pytest.mark.asyncio
    async def test_db_error_raises_custom_exception(self):
        session = AsyncMock()
        session.execute.side_effect = Exception("DB error")
        repo = ChatBotRepository()
        with pytest.raises(Custom_Exception):
            await repo.validate_item(session, 1)


# --------------------------------------------------------------------------- #
# validate_order                                                                #
# --------------------------------------------------------------------------- #
class TestValidateOrder:
    @pytest.mark.asyncio
    async def test_returns_order_when_found(self, fake_order):
        session = _session_scalar_one_or_none(fake_order)
        repo = ChatBotRepository()
        result = await repo.validate_order(session, fake_order.order_id)
        assert result is fake_order

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        session = _session_scalar_one_or_none(None)
        repo = ChatBotRepository()
        result = await repo.validate_order(session, 9999)
        assert result is None

    @pytest.mark.asyncio
    async def test_db_error_raises_custom_exception(self):
        session = AsyncMock()
        session.execute.side_effect = Exception("DB down")
        repo = ChatBotRepository()
        with pytest.raises(Custom_Exception):
            await repo.validate_order(session, 1)


# --------------------------------------------------------------------------- #
# get_menu                                                                      #
# --------------------------------------------------------------------------- #
class TestGetMenu:
    @pytest.mark.asyncio
    async def test_returns_dict_with_items_list(self, fake_item):
        session = _session_scalars_all([fake_item])
        repo = ChatBotRepository()
        result = await repo.get_menu(session)
        assert "items" in result
        assert len(result["items"]) == 1
        assert result["items"][0]["id"] == fake_item.item_id
        assert result["items"][0]["name"] == fake_item.name
        assert result["items"][0]["price"] == fake_item.price

    @pytest.mark.asyncio
    async def test_empty_menu_returns_empty_list(self):
        session = _session_scalars_all([])
        repo = ChatBotRepository()
        result = await repo.get_menu(session)
        assert result["items"] == []

    @pytest.mark.asyncio
    async def test_db_error_raises_custom_exception(self):
        session = AsyncMock()
        session.execute.side_effect = Exception("DB down")
        repo = ChatBotRepository()
        with pytest.raises(Custom_Exception):
            await repo.get_menu(session)


class TestGetOrderDetail:
    @pytest.mark.asyncio
    async def test_no_order_returns_message(self):
        repository = ChatBotRepository()

        async def no_order(_session, _customer_id):
            return None

        repository.get_order = no_order

        result = await repository.get_order_detail(AsyncMock(), 1)

        assert result == {"message": "There is no order for this customer."}

    @pytest.mark.asyncio
    async def test_order_returns_details(self, fake_order):
        session = AsyncMock()
        query_result = MagicMock()
        query_result.all.return_value = [(1, "Espresso", 2)]
        session.execute.return_value = query_result
        repository = ChatBotRepository()

        async def latest_order(_session, _customer_id):
            return fake_order

        repository.get_order = latest_order

        result = await repository.get_order_detail(session, fake_order.customer_id)

        assert result["order_id"] == fake_order.order_id
        assert result["items"] == [{"id": 1, "name": "Espresso", "count": 2}]
        assert result["order_status"] == fake_order.order_status.value

    @pytest.mark.asyncio
    async def test_query_error_raises_custom_exception(self, fake_order):
        session = AsyncMock()
        session.execute.side_effect = RuntimeError("database unavailable")
        repository = ChatBotRepository()

        async def latest_order(_session, _customer_id):
            return fake_order

        repository.get_order = latest_order

        with pytest.raises(Custom_Exception):
            await repository.get_order_detail(session, fake_order.customer_id)


# --------------------------------------------------------------------------- #
# place_order                                                                   #
# --------------------------------------------------------------------------- #
class TestPlaceOrder:
    @pytest.mark.asyncio
    async def test_returns_order_dict(self, fake_customer):
        session = AsyncMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.add = MagicMock()

        repo = ChatBotRepository()
        result = await repo.place_order(
            session, [1], [2], 240.0, fake_customer
        )

        assert "order_id" in result
        assert result["total_amount"] == 240.0
        assert "message" in result
        session.flush.assert_awaited()
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_multiple_items_all_added(self, fake_customer):
        """All (item_id, count) pairs must be added as Order_Item rows."""
        session = AsyncMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.add = MagicMock()

        repo = ChatBotRepository()
        await repo.place_order(session, [1, 2], [3, 1], 480.0, fake_customer)

        # session.add should be called once for the Order + once per item = 3 total
        assert session.add.call_count >= 3

    @pytest.mark.asyncio
    async def test_flush_error_rolls_back_and_raises(self, fake_customer):
        session = AsyncMock()
        session.flush.side_effect = Exception("flush failed")
        session.rollback = AsyncMock()

        repo = ChatBotRepository()
        with pytest.raises(Custom_Exception):
            await repo.place_order(session, [1], [1], 120.0, fake_customer)
        session.rollback.assert_awaited_once()


# --------------------------------------------------------------------------- #
# get_order_by_id                                                               #
# --------------------------------------------------------------------------- #
class TestGetOrderById:
    @pytest.mark.asyncio
    async def test_order_found_returns_dict(self, fake_order):
        # First execute() returns the order, second returns item join rows
        session = AsyncMock()
        order_result = MagicMock()
        order_result.scalar_one_or_none.return_value = fake_order
        items_result = MagicMock()
        items_result.all.return_value = [(1, "Espresso", 2)]
        session.execute.side_effect = [order_result, items_result]

        repo = ChatBotRepository()
        result = await repo.get_order_by_id(session, fake_order.order_id, 1)

        assert result["order_id"] == fake_order.order_id
        assert "items" in result
        assert result["items"][0]["name"] == "Espresso"

    @pytest.mark.asyncio
    async def test_order_not_found_returns_message_dict(self):
        session = AsyncMock()
        order_result = MagicMock()
        order_result.scalar_one_or_none.return_value = None
        session.execute.return_value = order_result

        repo = ChatBotRepository()
        result = await repo.get_order_by_id(session, 999, 1)
        assert "message" in result

    @pytest.mark.asyncio
    async def test_db_error_raises_custom_exception(self):
        session = AsyncMock()
        session.execute.side_effect = Exception("DB error")
        repo = ChatBotRepository()
        with pytest.raises(Custom_Exception):
            await repo.get_order_by_id(session, 1, 1)


# --------------------------------------------------------------------------- #
# get_recent_orders                                                             #
# --------------------------------------------------------------------------- #
class TestGetRecentOrders:
    @pytest.mark.asyncio
    async def test_returns_orders_summary(self, fake_order):
        session = _session_scalars_all([fake_order])
        repo = ChatBotRepository()
        result = await repo.get_recent_orders(session, 1)
        assert "orders" in result
        assert len(result["orders"]) == 1
        assert result["orders"][0]["order_id"] == fake_order.order_id

    @pytest.mark.asyncio
    async def test_no_orders_returns_message(self):
        session = _session_scalars_all([])
        repo = ChatBotRepository()
        result = await repo.get_recent_orders(session, 1)
        assert "message" in result

    @pytest.mark.asyncio
    async def test_db_error_raises_custom_exception(self):
        session = AsyncMock()
        session.execute.side_effect = Exception("DB error")
        repo = ChatBotRepository()
        with pytest.raises(Custom_Exception):
            await repo.get_recent_orders(session, 1)


# --------------------------------------------------------------------------- #
# update_order                                                                  #
# --------------------------------------------------------------------------- #
class TestUpdateOrder:
    @pytest.mark.asyncio
    async def test_returns_updated_order_dict(self, fake_order, fake_item):
        """Deactivates old items, adds new ones, recalculates total."""
        existing_item = MagicMock()
        existing_item.is_active = True

        session = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()

        # First execute: get existing order_items
        existing_result = MagicMock()
        existing_scalars = MagicMock()
        existing_scalars.all.return_value = [existing_item]
        existing_result.scalars.return_value = existing_scalars

        # validate_item will also call execute — patch at the method level
        session.execute.return_value = existing_result

        repo = ChatBotRepository()

        # Patch validate_item to avoid chained execute calls
        async def mock_validate_item(sess, item_id):
            return fake_item

        repo.validate_item = mock_validate_item

        result = await repo.update_order(
            session, fake_order.order_id, 1, [1], [2], fake_order
        )

        assert result["order_id"] == fake_order.order_id
        assert result["total_amount"] == fake_item.price * 2
        assert existing_item.is_active is False
        session.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_invalid_item_raises_custom_exception(self, fake_order):
        existing_item = MagicMock()
        session = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()

        existing_result = MagicMock()
        existing_scalars = MagicMock()
        existing_scalars.all.return_value = [existing_item]
        existing_result.scalars.return_value = existing_scalars
        session.execute.return_value = existing_result

        repo = ChatBotRepository()

        async def mock_validate_item_none(sess, item_id):
            return None     # item doesn't exist

        repo.validate_item = mock_validate_item_none

        with pytest.raises(Custom_Exception):
            await repo.update_order(
                session, fake_order.order_id, 1, [999], [1], fake_order
            )


# --------------------------------------------------------------------------- #
# cancel_order                                                                  #
# --------------------------------------------------------------------------- #
class TestCancelOrder:
    @pytest.mark.asyncio
    async def test_returns_cancellation_dict(self, fake_order):
        order_item = MagicMock()
        order_item.is_active = True

        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()

        items_result = MagicMock()
        items_scalars = MagicMock()
        items_scalars.all.return_value = [order_item]
        items_result.scalars.return_value = items_scalars
        session.execute.return_value = items_result

        repo = ChatBotRepository()
        result = await repo.cancel_order(session, fake_order.order_id, 1, fake_order)

        assert result["order_id"] == fake_order.order_id
        assert "message" in result
        assert fake_order.is_active is False
        assert order_item.is_active is False
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_db_error_rolls_back_and_raises(self, fake_order):
        session = AsyncMock()
        session.execute.side_effect = Exception("DB error")
        session.rollback = AsyncMock()

        repo = ChatBotRepository()
        with pytest.raises(Custom_Exception):
            await repo.cancel_order(session, fake_order.order_id, 1, fake_order)
        session.rollback.assert_awaited_once()
