"""
Tests for MCP_Client/src/services/admin_service.py

Functions under test:
  - AdminService.get_orders
  - AdminService.update_order_status
  - AdminService.create_item
  - AdminService.update_item
  - AdminService.delete_item
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.admin_service import AdminService
from repositories.schema.coffee_shop_models import OrderStatus
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.http_status import HttpStatusCode


def _build_service(repo_mock=None):
    if repo_mock is None:
        repo_mock = AsyncMock()
    service = AdminService()
    service.repository = repo_mock
    return service, repo_mock


def _mock_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    async def _gen():
        yield session

    return session, _gen


class TestGetOrders:
    @pytest.mark.asyncio
    async def test_returns_formatted_orders(self, fake_order):
        session, gen = _mock_session()
        mock_repo = AsyncMock()
        mock_repo.get_orders.return_value = [fake_order]

        service, _ = _build_service(mock_repo)

        with patch("services.admin_service.get_db_session", return_value=gen()):
            result = await service.get_orders()

        assert len(result) == 1
        assert result[0].order_uuid == str(fake_order.order_uuid)

    @pytest.mark.asyncio
    async def test_empty_orders(self):
        session, gen = _mock_session()
        mock_repo = AsyncMock()
        mock_repo.get_orders.return_value = []

        service, _ = _build_service(mock_repo)

        with patch("services.admin_service.get_db_session", return_value=gen()):
            result = await service.get_orders()

        assert result == []

    @pytest.mark.asyncio
    async def test_db_error_raises_custom_exception(self):
        session, gen = _mock_session()
        mock_repo = AsyncMock()
        mock_repo.get_orders.side_effect = Exception("DB error")

        service, _ = _build_service(mock_repo)

        with patch("services.admin_service.get_db_session", return_value=gen()):
            with pytest.raises(Custom_Exception):
                await service.get_orders()


class TestUpdateOrderStatus:
    @pytest.mark.asyncio
    async def test_progresses_ordered_to_processing(self, fake_order):
        fake_order.order_status = OrderStatus.ordered

        updated_order = MagicMock()
        updated_order.order_uuid = fake_order.order_uuid
        updated_order.order_status = OrderStatus.processing
        updated_order.updated_at = datetime.now(timezone.utc)

        session, gen = _mock_session()
        mock_repo = AsyncMock()
        mock_repo.get_order.return_value = fake_order
        mock_repo.update_order_status.return_value = updated_order

        service, _ = _build_service(mock_repo)

        with patch("services.admin_service.get_db_session", return_value=gen()):
            result = await service.update_order_status(fake_order.order_uuid)

        assert result.order_status == "processing"

    @pytest.mark.asyncio
    async def test_order_not_found_raises_404(self):
        session, gen = _mock_session()
        mock_repo = AsyncMock()
        mock_repo.get_order.return_value = None

        service, _ = _build_service(mock_repo)

        with patch("services.admin_service.get_db_session", return_value=gen()):
            with pytest.raises(Custom_Exception) as exc_info:
                await service.update_order_status(uuid.uuid4())

        assert exc_info.value.status_code == HttpStatusCode.NOT_FOUND

    @pytest.mark.asyncio
    async def test_completed_order_raises_400(self, fake_order):
        """An order already in 'completed' status cannot be progressed."""
        fake_order.order_status = OrderStatus.completed

        session, gen = _mock_session()
        mock_repo = AsyncMock()
        mock_repo.get_order.return_value = fake_order

        service, _ = _build_service(mock_repo)

        with patch("services.admin_service.get_db_session", return_value=gen()):
            with pytest.raises(Custom_Exception) as exc_info:
                await service.update_order_status(fake_order.order_uuid)

        assert exc_info.value.status_code == HttpStatusCode.BAD_REQUEST


class TestCreateItem:
    @pytest.mark.asyncio
    async def test_creates_item_successfully(self):
        mock_item = MagicMock()
        mock_item.item_uuid = uuid.uuid4()
        mock_item.name = "Latte"
        mock_item.price = 130.0
        mock_item.created_at = datetime.now(timezone.utc)

        session, gen = _mock_session()
        mock_repo = AsyncMock()
        mock_repo.create_item.return_value = mock_item

        service, _ = _build_service(mock_repo)

        with patch("services.admin_service.get_db_session", return_value=gen()):
            result = await service.create_item("Latte", 130.0)

        assert result.name == "Latte"
        assert result.price == 130.0

    @pytest.mark.asyncio
    async def test_db_error_raises_500(self):
        session, gen = _mock_session()
        mock_repo = AsyncMock()
        mock_repo.create_item.side_effect = Exception("DB error")

        service, _ = _build_service(mock_repo)

        with patch("services.admin_service.get_db_session", return_value=gen()):
            with pytest.raises(Custom_Exception) as exc_info:
                await service.create_item("Espresso", 100.0)

        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR


class TestUpdateItem:
    @pytest.mark.asyncio
    async def test_item_not_found_raises_404(self):
        session, gen = _mock_session()
        mock_repo = AsyncMock()
        mock_repo.get_item_by_uuid.return_value = None

        service, _ = _build_service(mock_repo)

        with patch("services.admin_service.get_db_session", return_value=gen()):
            with pytest.raises(Custom_Exception) as exc_info:
                await service.update_item(uuid.uuid4(), "Mocha", 150.0)

        assert exc_info.value.status_code == HttpStatusCode.NOT_FOUND

    @pytest.mark.asyncio
    async def test_updates_successfully(self, fake_item):
        updated = MagicMock()
        updated.item_uuid = fake_item.item_uuid
        updated.name = "Mocha"
        updated.price = 150.0
        updated.is_active = True
        updated.created_at = fake_item.created_at

        session, gen = _mock_session()
        mock_repo = AsyncMock()
        mock_repo.get_item_by_uuid.return_value = fake_item
        mock_repo.update_item.return_value = updated

        service, _ = _build_service(mock_repo)

        with patch("services.admin_service.get_db_session", return_value=gen()):
            result = await service.update_item(fake_item.item_uuid, "Mocha", 150.0)

        assert result.name == "Mocha"


class TestDeleteItem:
    @pytest.mark.asyncio
    async def test_item_not_found_raises_404(self):
        session, gen = _mock_session()
        mock_repo = AsyncMock()
        mock_repo.get_item_by_uuid.return_value = None

        service, _ = _build_service(mock_repo)

        with patch("services.admin_service.get_db_session", return_value=gen()):
            with pytest.raises(Custom_Exception) as exc_info:
                await service.delete_item(uuid.uuid4())

        assert exc_info.value.status_code == HttpStatusCode.NOT_FOUND

    @pytest.mark.asyncio
    async def test_deletes_successfully(self, fake_item):
        session, gen = _mock_session()
        mock_repo = AsyncMock()
        mock_repo.get_item_by_uuid.return_value = fake_item
        mock_repo.delete_item = AsyncMock()

        service, _ = _build_service(mock_repo)

        with patch("services.admin_service.get_db_session", return_value=gen()):
            await service.delete_item(fake_item.item_uuid)

        mock_repo.delete_item.assert_called_once()
