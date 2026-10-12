"""
Tests for MCP_Server/src/tools/tool.py

Tools under test:
  - get_menu_tool
  - get_shop_details_tool
  - place_order_tool
  - get_order_tool
  - update_order_tool
  - cancel_order_tool

Strategy:
  - Import tool functions directly from their module (not the router),
    so the raw async functions under the decorators are tested.
  - Patch `get_db_session` in the tool module and replace the module-level
    `repository` singleton with an AsyncMock for each test.
  - Use `importlib` to load the module with the correct sys.path so that
    server-side modules resolve correctly.
"""
import sys
import os
import uuid
import importlib
import importlib.util
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_SERVER_SRC = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "MCP_Server", "src")
)
if _SERVER_SRC not in sys.path:
    sys.path.insert(0, _SERVER_SRC)

from repositories.schema.coffee_shop_models import OrderStatus
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.http_status import HttpStatusCode

# Import the tool module – this also registers the FastMCP tools
import tools.tool as _tool_mod

# Grab the raw underlying functions (strip the @with_async_request_id wrapper)
# Each decorated function has __wrapped__ pointing to the original
def _unwrap(fn):
    return getattr(fn, "__wrapped__", fn)


get_menu_tool        = _unwrap(_tool_mod.get_menu_tool)
get_shop_details_tool = _unwrap(_tool_mod.get_shop_details_tool)
place_order_tool     = _unwrap(_tool_mod.place_order_tool)
get_order_tool       = _unwrap(_tool_mod.get_order_tool)
update_order_tool    = _unwrap(_tool_mod.update_order_tool)
cancel_order_tool    = _unwrap(_tool_mod.cancel_order_tool)


def _db_patch(session_mock):
    """Patch get_db_session in the tool module."""
    async def _gen():
        yield session_mock

    return patch.object(_tool_mod, "get_db_session", return_value=_gen())


# --------------------------------------------------------------------------- #
# get_menu_tool                                                                 #
# --------------------------------------------------------------------------- #
class TestGetMenuTool:
    @pytest.mark.asyncio
    async def test_returns_menu_from_repository(self, mock_db_session):
        expected = {"items": [{"id": 1, "name": "Espresso", "price": 120.0}]}

        mock_repo = AsyncMock()
        mock_repo.get_menu.return_value = expected

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            result = await get_menu_tool()

        mock_repo.get_menu.assert_awaited_once()
        assert result == expected

    @pytest.mark.asyncio
    async def test_db_error_raises_custom_exception(self, mock_db_session):
        mock_repo = AsyncMock()
        mock_repo.get_menu.side_effect = Exception("DB down")

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            with pytest.raises(Custom_Exception):
                await get_menu_tool()

    @pytest.mark.asyncio
    async def test_repository_custom_exception_propagates(self, mock_db_session):
        expected = Custom_Exception("menu failure", "MENU_ERROR", 500)
        mock_repo = AsyncMock()
        mock_repo.get_menu.side_effect = expected

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            with pytest.raises(Custom_Exception) as exc_info:
                await get_menu_tool()

        assert exc_info.value is expected


# --------------------------------------------------------------------------- #
# get_shop_details_tool                                                         #
# --------------------------------------------------------------------------- #
class TestGetShopDetailsTool:
    @pytest.mark.asyncio
    async def test_returns_content_when_file_exists(self):
        with patch("tools.tool.Path") as MockPath:
            mock_p = MagicMock()
            mock_p.exists.return_value = True
            mock_p.read_text.return_value = "Brew Buddy - 123 Coffee Lane"
            mock_p.__truediv__.return_value = mock_p
            MockPath.return_value.resolve.return_value.parent.parent.__truediv__.return_value = mock_p

            result = await get_shop_details_tool()

        assert "Brew Buddy" in result

    @pytest.mark.asyncio
    async def test_returns_unavailable_when_file_missing(self):
        with patch("tools.tool.Path") as MockPath:
            mock_p = MagicMock()
            mock_p.exists.return_value = False
            mock_p.__truediv__.return_value = mock_p
            MockPath.return_value.resolve.return_value.parent.parent.__truediv__.return_value = mock_p

            result = await get_shop_details_tool()

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_file_read_error_raises_custom_exception(self):
        with patch("tools.tool.Path") as MockPath:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.read_text.side_effect = OSError("file unreadable")
            mock_path.__truediv__.return_value = mock_path
            MockPath.return_value.resolve.return_value.parent.parent.__truediv__.return_value = mock_path

            with pytest.raises(Custom_Exception):
                await get_shop_details_tool()


# --------------------------------------------------------------------------- #
# place_order_tool                                                              #
# --------------------------------------------------------------------------- #
class TestPlaceOrderTool:
    @pytest.mark.asyncio
    async def test_successful_order_placement(self, mock_db_session, fake_customer, fake_item):
        fake_item.price = 120.0
        mock_repo = AsyncMock()
        mock_repo.get_customer.return_value = fake_customer
        mock_repo.validate_item.return_value = fake_item
        mock_repo.place_order.return_value = {
            "order_id": 1, "total_amount": 240.0, "message": "Order placed"
        }

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            result = await place_order_tool(
                item_id=[1], count=[2], customer_id=fake_customer.customer_uuid
            )

        assert result["order_id"] == 1

    @pytest.mark.asyncio
    async def test_empty_item_list_raises_400(self):
        with pytest.raises(Custom_Exception) as exc_info:
            await place_order_tool(item_id=[], count=[], customer_id=uuid.uuid4())
        assert exc_info.value.status_code == HttpStatusCode.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_mismatched_lists_raises_400(self):
        with pytest.raises(Custom_Exception) as exc_info:
            await place_order_tool(item_id=[1, 2], count=[3], customer_id=uuid.uuid4())
        assert exc_info.value.status_code == HttpStatusCode.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_zero_count_raises_400(self):
        with pytest.raises(Custom_Exception) as exc_info:
            await place_order_tool(item_id=[1], count=[0], customer_id=uuid.uuid4())
        assert exc_info.value.status_code == HttpStatusCode.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_negative_count_raises_400(self):
        with pytest.raises(Custom_Exception) as exc_info:
            await place_order_tool(item_id=[1], count=[-1], customer_id=uuid.uuid4())
        assert exc_info.value.status_code == HttpStatusCode.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_customer_not_found_raises_404(self, mock_db_session):
        mock_repo = AsyncMock()
        mock_repo.get_customer.return_value = None

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            with pytest.raises(Custom_Exception) as exc_info:
                await place_order_tool(item_id=[1], count=[1], customer_id=uuid.uuid4())
        assert exc_info.value.status_code == HttpStatusCode.NOT_FOUND

    @pytest.mark.asyncio
    async def test_invalid_item_raises_400(self, mock_db_session, fake_customer):
        mock_repo = AsyncMock()
        mock_repo.get_customer.return_value = fake_customer
        mock_repo.validate_item.return_value = None

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            with pytest.raises(Custom_Exception) as exc_info:
                await place_order_tool(
                    item_id=[999], count=[1], customer_id=fake_customer.customer_uuid
                )
        assert exc_info.value.status_code == HttpStatusCode.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_repository_error_is_wrapped(self, mock_db_session, fake_customer):
        mock_repo = AsyncMock()
        mock_repo.get_customer.side_effect = RuntimeError("database unavailable")

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            with pytest.raises(Custom_Exception) as exc_info:
                await place_order_tool(
                    item_id=[1], count=[1], customer_id=fake_customer.customer_uuid
                )

        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR


# --------------------------------------------------------------------------- #
# get_order_tool                                                                #
# --------------------------------------------------------------------------- #
class TestGetOrderTool:
    @pytest.mark.asyncio
    async def test_returns_recent_orders_when_no_order_id(self, mock_db_session, fake_customer):
        recent = {"orders": [{"order_id": 1}]}
        mock_repo = AsyncMock()
        mock_repo.get_customer.return_value = fake_customer
        mock_repo.get_recent_orders.return_value = recent

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            result = await get_order_tool(customer_id=fake_customer.customer_uuid)

        mock_repo.get_recent_orders.assert_awaited_once_with(
            mock_db_session, fake_customer.customer_id
        )
        assert result == recent

    @pytest.mark.asyncio
    async def test_returns_specific_order_when_order_id_given(self, mock_db_session, fake_customer):
        order_detail = {"order_id": 5, "order_status": "ordered", "items": []}
        mock_repo = AsyncMock()
        mock_repo.get_customer.return_value = fake_customer
        mock_repo.get_order_by_id.return_value = order_detail

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            result = await get_order_tool(
                customer_id=fake_customer.customer_uuid, order_id=5
            )

        mock_repo.get_order_by_id.assert_awaited_once_with(
            mock_db_session, 5, fake_customer.customer_id
        )
        assert result == order_detail

    @pytest.mark.asyncio
    async def test_customer_not_found_raises_404(self, mock_db_session):
        mock_repo = AsyncMock()
        mock_repo.get_customer.return_value = None

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            with pytest.raises(Custom_Exception) as exc_info:
                await get_order_tool(customer_id=uuid.uuid4())
        assert exc_info.value.status_code == HttpStatusCode.NOT_FOUND

    @pytest.mark.asyncio
    async def test_repository_error_is_wrapped(self, mock_db_session, fake_customer):
        mock_repo = AsyncMock()
        mock_repo.get_customer.side_effect = RuntimeError("database unavailable")

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            with pytest.raises(Custom_Exception) as exc_info:
                await get_order_tool(customer_id=fake_customer.customer_uuid)

        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR


# --------------------------------------------------------------------------- #
# update_order_tool                                                             #
# --------------------------------------------------------------------------- #
class TestUpdateOrderTool:
    @pytest.mark.asyncio
    async def test_successful_update(self, mock_db_session, fake_customer, fake_order):
        fake_order.order_status = OrderStatus.ordered
        fake_order.customer_id = fake_customer.customer_id
        expected = {"order_id": 101, "total_amount": 360.0, "message": "Order updated successfully."}

        mock_repo = AsyncMock()
        mock_repo.get_customer.return_value = fake_customer
        mock_repo.validate_order.return_value = fake_order
        mock_repo.update_order.return_value = expected

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            result = await update_order_tool(
                order_id=fake_order.order_id,
                item_id=[1], count=[3],
                customer_id=fake_customer.customer_uuid,
            )

        assert result["total_amount"] == 360.0
        mock_db_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_empty_item_list_raises_400(self):
        with pytest.raises(Custom_Exception) as exc_info:
            await update_order_tool(
                order_id=1, item_id=[], count=[], customer_id=uuid.uuid4()
            )
        assert exc_info.value.status_code == HttpStatusCode.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_non_ordered_status_raises_400(self, mock_db_session, fake_customer, fake_order):
        fake_order.order_status = OrderStatus.processing
        fake_order.customer_id = fake_customer.customer_id

        mock_repo = AsyncMock()
        mock_repo.get_customer.return_value = fake_customer
        mock_repo.validate_order.return_value = fake_order

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            with pytest.raises(Custom_Exception) as exc_info:
                await update_order_tool(
                    order_id=fake_order.order_id, item_id=[1], count=[1],
                    customer_id=fake_customer.customer_uuid,
                )
        assert exc_info.value.status_code == HttpStatusCode.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_order_belongs_to_different_customer_raises_400(
        self, mock_db_session, fake_customer, fake_order
    ):
        fake_order.order_status = OrderStatus.ordered
        fake_order.customer_id = 9999

        mock_repo = AsyncMock()
        mock_repo.get_customer.return_value = fake_customer
        mock_repo.validate_order.return_value = fake_order

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            with pytest.raises(Custom_Exception) as exc_info:
                await update_order_tool(
                    order_id=fake_order.order_id, item_id=[1], count=[1],
                    customer_id=fake_customer.customer_uuid,
                )
        assert exc_info.value.status_code == HttpStatusCode.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_order_not_found_raises_404(self, mock_db_session, fake_customer):
        mock_repo = AsyncMock()
        mock_repo.get_customer.return_value = fake_customer
        mock_repo.validate_order.return_value = None

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            with pytest.raises(Custom_Exception) as exc_info:
                await update_order_tool(
                    order_id=999, item_id=[1], count=[1],
                    customer_id=fake_customer.customer_uuid,
                )
        assert exc_info.value.status_code == HttpStatusCode.NOT_FOUND

    @pytest.mark.asyncio
    async def test_customer_not_found_raises_404(self, mock_db_session):
        mock_repo = AsyncMock()
        mock_repo.get_customer.return_value = None

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            with pytest.raises(Custom_Exception) as exc_info:
                await update_order_tool(
                    order_id=1, item_id=[1], count=[1], customer_id=uuid.uuid4()
                )
        assert exc_info.value.status_code == HttpStatusCode.NOT_FOUND

    @pytest.mark.asyncio
    async def test_repository_error_is_wrapped_and_session_rolled_back(
        self, mock_db_session
    ):
        mock_repo = AsyncMock()
        mock_repo.get_customer.side_effect = RuntimeError("database unavailable")

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            with pytest.raises(Custom_Exception) as exc_info:
                await update_order_tool(
                    order_id=1, item_id=[1], count=[1], customer_id=uuid.uuid4()
                )

        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR
        mock_db_session.rollback.assert_awaited_once()


# --------------------------------------------------------------------------- #
# cancel_order_tool                                                             #
# --------------------------------------------------------------------------- #
class TestCancelOrderTool:
    @pytest.mark.asyncio
    async def test_successful_cancellation(self, mock_db_session, fake_customer, fake_order):
        fake_order.order_status = OrderStatus.ordered
        fake_order.customer_id = fake_customer.customer_id
        expected = {"order_id": fake_order.order_id, "message": "Order cancelled successfully."}

        mock_repo = AsyncMock()
        mock_repo.get_customer.return_value = fake_customer
        mock_repo.validate_order.return_value = fake_order
        mock_repo.cancel_order.return_value = expected

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            result = await cancel_order_tool(
                order_id=fake_order.order_id,
                customer_id=fake_customer.customer_uuid,
            )

        assert "message" in result
        mock_repo.cancel_order.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_non_ordered_status_raises_400(self, mock_db_session, fake_customer, fake_order):
        fake_order.order_status = OrderStatus.completed
        fake_order.customer_id = fake_customer.customer_id

        mock_repo = AsyncMock()
        mock_repo.get_customer.return_value = fake_customer
        mock_repo.validate_order.return_value = fake_order

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            with pytest.raises(Custom_Exception) as exc_info:
                await cancel_order_tool(
                    order_id=fake_order.order_id,
                    customer_id=fake_customer.customer_uuid,
                )
        assert exc_info.value.status_code == HttpStatusCode.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_order_not_found_raises_404(self, mock_db_session, fake_customer):
        mock_repo = AsyncMock()
        mock_repo.get_customer.return_value = fake_customer
        mock_repo.validate_order.return_value = None

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            with pytest.raises(Custom_Exception) as exc_info:
                await cancel_order_tool(
                    order_id=999, customer_id=fake_customer.customer_uuid
                )
        assert exc_info.value.status_code == HttpStatusCode.NOT_FOUND

    @pytest.mark.asyncio
    async def test_order_belongs_to_different_customer_raises_400(
        self, mock_db_session, fake_customer, fake_order
    ):
        fake_order.order_status = OrderStatus.ordered
        fake_order.customer_id = 8888

        mock_repo = AsyncMock()
        mock_repo.get_customer.return_value = fake_customer
        mock_repo.validate_order.return_value = fake_order

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            with pytest.raises(Custom_Exception) as exc_info:
                await cancel_order_tool(
                    order_id=fake_order.order_id,
                    customer_id=fake_customer.customer_uuid,
                )
        assert exc_info.value.status_code == HttpStatusCode.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_customer_not_found_raises_404(self, mock_db_session):
        mock_repo = AsyncMock()
        mock_repo.get_customer.return_value = None

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            with pytest.raises(Custom_Exception) as exc_info:
                await cancel_order_tool(order_id=1, customer_id=uuid.uuid4())
        assert exc_info.value.status_code == HttpStatusCode.NOT_FOUND

    @pytest.mark.asyncio
    async def test_repository_error_is_wrapped(self, mock_db_session):
        mock_repo = AsyncMock()
        mock_repo.get_customer.side_effect = RuntimeError("database unavailable")

        with _db_patch(mock_db_session):
            _tool_mod.repository = mock_repo
            with pytest.raises(Custom_Exception) as exc_info:
                await cancel_order_tool(order_id=1, customer_id=uuid.uuid4())

        assert exc_info.value.status_code == HttpStatusCode.INTERNAL_SERVER_ERROR
