from uuid import UUID
from typing import Optional

from models.admin import (
    GetOrdersResponse,
    CustomerDetails,
    OrderItems,
    UpdateOrderStatusResponse,
    ItemResponse,
)
from repositories.admin_repository import AdminRepository
from repositories.database import get_db_session
from repositories.schema.coffee_shop_models import OrderStatus
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger

logger = get_logger(__name__)


class AdminService:
    def __init__(self) -> None:
        self.repository = AdminRepository()

    async def get_orders(self):
        async for session in get_db_session():
            try:
                logger.info("Service: fetching all orders")
                orders = await self.repository.get_orders(session)
                order_data = [
                    GetOrdersResponse(
                        order_uuid=str(order.order_uuid),
                        order_status=order.order_status.value,
                        total_amount=order.total_amount,
                        ordered_at=order.created_at,
                        customer=CustomerDetails(
                            customer_uuid=str(order.customer.customer_uuid),
                            name=order.customer.name,
                            phone_number=order.customer.phone_number,
                        ),
                        items=[
                            OrderItems(
                                name=item.item.name,
                                price=item.item.price,
                                count=item.item_count,
                            )
                            for item in order.order_items
                        ],
                    )
                    for order in orders
                ]
                logger.info("Fetched %d orders successfully", len(order_data))
                return order_data
            except Custom_Exception:
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                logger.exception("Unexpected error while fetching orders")
                raise Custom_Exception(
                    "Unable to fetch orders.",
                    ErrorCode.INTERNAL_SERVER_ERROR,
                    HttpStatusCode.INTERNAL_SERVER_ERROR,
                )

    async def update_order_status(self, order_uuid: UUID):
        async for session in get_db_session():
            try:
                logger.info("Updating status for order_uuid: %s", order_uuid)
                order = await self.repository.get_order(session, order_uuid)
                if not order:
                    logger.warning("Order not found for order_uuid: %s", order_uuid)
                    raise Custom_Exception(
                        "Order not found.",
                        ErrorCode.DATA_NOT_FOUND,
                        HttpStatusCode.NOT_FOUND,
                    )

                status_flow = {
                    OrderStatus.ordered: OrderStatus.processing,
                    OrderStatus.processing: OrderStatus.completed,
                }
                new_status = status_flow.get(order.order_status)
                if new_status is None:
                    logger.warning(
                        "Order_uuid %s is already in terminal status '%s'",order_uuid, order.order_status.value)
                    raise Custom_Exception(
                        f"Order is already in '{order.order_status.value}' status and cannot be updated further.",
                        ErrorCode.VALIDATION_ERROR,
                        HttpStatusCode.BAD_REQUEST,
                    )

                updated_order = await self.repository.update_order_status(session, order, new_status)
                await session.commit()
                logger.info("Order status updated")
                return UpdateOrderStatusResponse(
                    order_uuid=str(updated_order.order_uuid),
                    order_status=updated_order.order_status.value,
                    updated_at=updated_order.updated_at,
                )
            except Custom_Exception:
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                logger.exception("Service: unexpected error while updating order status for order_uuid: %s", order_uuid)
                raise Custom_Exception(
                    "Unable to update order status.",
                    ErrorCode.INTERNAL_SERVER_ERROR,
                    HttpStatusCode.INTERNAL_SERVER_ERROR,
                )

    async def create_item(self, name: str, price: float):
        async for session in get_db_session():
            try:
                logger.info("Creating new item")
                item = await self.repository.create_item(session, name, price)
                await session.commit()
                logger.info("Item created successfully")
                return ItemResponse(
                    item_uuid=str(item.item_uuid),
                    name=item.name,
                    price=item.price,
                    created_at=item.created_at,
                )
            except Custom_Exception:
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                logger.exception("Unexpected error while creating item")
                raise Custom_Exception(
                    "Unable to create item.",
                    ErrorCode.INTERNAL_SERVER_ERROR,
                    HttpStatusCode.INTERNAL_SERVER_ERROR,
                )

    async def update_item(
        self,
        item_uuid: UUID,
        name: Optional[str],
        price: Optional[float],
    ):
        async for session in get_db_session():
            try:
                logger.info("Updating item")
                item = await self.repository.get_item_by_uuid(session, item_uuid)
                if not item:
                    logger.warning("Item not found for Upation")
                    raise Custom_Exception(
                        "Item not found.",
                        ErrorCode.DATA_NOT_FOUND,
                        HttpStatusCode.NOT_FOUND,
                    )

                updated_item = await self.repository.update_item(session, item, name, price)
                await session.commit()
                logger.info("Item updated successfully")
                return ItemResponse(
                    item_uuid=str(updated_item.item_uuid),
                    name=updated_item.name,
                    price=updated_item.price,
                    is_active=updated_item.is_active,
                    created_at=updated_item.created_at,
                )
            except Custom_Exception:
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                logger.exception("Unexpected error while updating item")
                raise Custom_Exception(
                    "Unable to update item.",
                    ErrorCode.INTERNAL_SERVER_ERROR,
                    HttpStatusCode.INTERNAL_SERVER_ERROR,
                )

    async def delete_item(self, item_uuid: UUID):
        async for session in get_db_session():
            try:
                logger.info("Deleting item")
                item = await self.repository.get_item_by_uuid(session, item_uuid)
                if not item:
                    logger.warning("Item not found for deletion")
                    raise Custom_Exception(
                        "Item not found.",
                        ErrorCode.DATA_NOT_FOUND,
                        HttpStatusCode.NOT_FOUND,
                    )

                await self.repository.delete_item(session, item)
                await session.commit()
                logger.info("Item soft-deleted successfully")
            except Custom_Exception:
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                logger.exception("Unexpected error while deleting")
                raise Custom_Exception(
                    "Unable to delete item.",
                    ErrorCode.INTERNAL_SERVER_ERROR,
                    HttpStatusCode.INTERNAL_SERVER_ERROR,
                )
