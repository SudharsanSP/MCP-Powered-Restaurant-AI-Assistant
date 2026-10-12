"""
Tests for MCP_Client/src/repositories/admin_repository.py

Functions under test:
  - get_orders
  - get_order
  - update_order_status
  - get_item_by_uuid
  - create_item
  - update_item
  - delete_item
"""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from repositories.admin_repository import AdminRepository
from repositories.schema.coffee_shop_models import OrderStatus
from utilities.exceptions.custom_exception import Custom_Exception


def _make_session_scalars(rows):
    """Session where execute().scalars().all() returns rows."""
    session = AsyncMock()
    execute_result = MagicMock()
    scalars_result = MagicMock()
    scalars_result.all.return_value = rows
    execute_result.scalars.return_value = scalars_result
    session.execute.return_value = execute_result
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


def _make_session_scalar_one(row):
    """Session where execute().scalars().one_or_none() returns row."""
    session = AsyncMock()
    execute_result = MagicMock()
    scalars_result = MagicMock()
    scalars_result.one_or_none.return_value = row
    execute_result.scalars.return_value = scalars_result
    session.execute.return_value = execute_result
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


class TestGetOrders:
    @pytest.mark.asyncio
    async def test_returns_list_of_orders(self, fake_order):
        session = _make_session_scalars([fake_order])
        repo = AdminRepository()
        result = await repo.get_orders(session)
        assert result == [fake_order]

    @pytest.mark.asyncio
    async def test_returns_empty_list(self):
        session = _make_session_scalars([])
        repo = AdminRepository()
        result = await repo.get_orders(session)
        assert result == []

    @pytest.mark.asyncio
    async def test_db_error_raises_custom_exception(self):
        session = AsyncMock()
        session.execute.side_effect = Exception("DB error")
        repo = AdminRepository()
        with pytest.raises(Custom_Exception):
            await repo.get_orders(session)


class TestGetOrder:
    @pytest.mark.asyncio
    async def test_found(self, fake_order):
        session = _make_session_scalar_one(fake_order)
        repo = AdminRepository()
        result = await repo.get_order(session, uuid.uuid4())
        assert result is fake_order

    @pytest.mark.asyncio
    async def test_not_found(self):
        session = _make_session_scalar_one(None)
        repo = AdminRepository()
        result = await repo.get_order(session, uuid.uuid4())
        assert result is None


class TestUpdateOrderStatus:
    @pytest.mark.asyncio
    async def test_sets_new_status(self, fake_order):
        session = AsyncMock()
        session.flush = AsyncMock()
        repo = AdminRepository()
        updated = await repo.update_order_status(session, fake_order, OrderStatus.processing)
        assert updated.order_status == OrderStatus.processing
        assert updated.updated_by == "ADMIN"
        session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_flush_error_raises_custom_exception(self, fake_order):
        session = AsyncMock()
        session.flush.side_effect = Exception("flush failed")
        repo = AdminRepository()
        with pytest.raises(Custom_Exception):
            await repo.update_order_status(session, fake_order, OrderStatus.processing)


class TestGetItemByUuid:
    @pytest.mark.asyncio
    async def test_found(self, fake_item):
        session = _make_session_scalar_one(fake_item)
        repo = AdminRepository()
        result = await repo.get_item_by_uuid(session, fake_item.item_uuid)
        assert result is fake_item

    @pytest.mark.asyncio
    async def test_not_found(self):
        session = _make_session_scalar_one(None)
        repo = AdminRepository()
        result = await repo.get_item_by_uuid(session, uuid.uuid4())
        assert result is None


class TestCreateItem:
    @pytest.mark.asyncio
    async def test_adds_item_and_flushes(self):
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        repo = AdminRepository()
        result = await repo.create_item(session, "Cappuccino", 140.0)
        session.add.assert_called_once()
        session.flush.assert_called_once()
        assert result.name == "Cappuccino"
        assert result.price == 140.0

    @pytest.mark.asyncio
    async def test_flush_error_raises_custom_exception(self):
        session = AsyncMock()
        session.add = MagicMock()
        session.flush.side_effect = Exception("flush failed")
        repo = AdminRepository()
        with pytest.raises(Custom_Exception):
            await repo.create_item(session, "Latte", 130.0)


class TestUpdateItem:
    @pytest.mark.asyncio
    async def test_updates_name_and_price(self, fake_item):
        session = AsyncMock()
        session.flush = AsyncMock()
        repo = AdminRepository()
        result = await repo.update_item(session, fake_item, "Mocha", 160.0)
        assert result.name == "Mocha"
        assert result.price == 160.0
        assert result.updated_by == "ADMIN"

    @pytest.mark.asyncio
    async def test_none_values_not_applied(self, fake_item):
        """If name/price is None they should NOT overwrite existing values."""
        session = AsyncMock()
        session.flush = AsyncMock()
        original_name = fake_item.name
        original_price = fake_item.price
        repo = AdminRepository()
        result = await repo.update_item(session, fake_item, None, None)
        assert result.name == original_name
        assert result.price == original_price


class TestDeleteItem:
    @pytest.mark.asyncio
    async def test_soft_deletes_item(self, fake_item):
        session = AsyncMock()
        session.flush = AsyncMock()
        repo = AdminRepository()
        await repo.delete_item(session, fake_item)
        assert fake_item.is_active is False
        assert fake_item.updated_by == "ADMIN"
        session.flush.assert_called_once()
