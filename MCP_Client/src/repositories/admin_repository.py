import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.schema.coffee_shop_models import Order, Order_Item, Item, OrderStatus
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger

logger = get_logger(__name__)


class AdminRepository:

    async def get_orders(self, session: AsyncSession):
        try:
            logger.info("Querying all orders with customer and items")
            result = await session.execute(
                select(Order)
                .options(
                    selectinload(Order.customer),
                    selectinload(Order.order_items).selectinload(Order_Item.item)
                )
                .order_by(Order.created_at.desc())
            )
            return result.scalars().all()
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Database error while fetching all orders")
            raise Custom_Exception(
                "Unable to fetch orders.",
                ErrorCode.DATABASE_ERROR,
                HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def get_order(self, session: AsyncSession, order_uuid: UUID):
        try:
            logger.info("Querying order by uuid: %s", order_uuid)
            result = await session.execute(
                select(Order).where(Order.order_uuid == order_uuid)
            )
            return result.scalars().one_or_none()
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Database error while fetching order uuid: %s", order_uuid)
            raise Custom_Exception(
                "Unable to fetch order.",
                ErrorCode.DATABASE_ERROR,
                HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def update_order_status(self, session: AsyncSession, order: Order, new_status: OrderStatus):
        try:
            logger.info("Updating order status to '%s' for order_uuid: %s", new_status.value, order.order_uuid)
            order.order_status = new_status
            order.updated_at = datetime.utcnow()
            order.updated_by = "ADMIN"
            await session.flush()
            logger.info("Order status updated successfully for order_uuid: %s", order.order_uuid)
            return order
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Database error while updating order status for order_uuid: %s", order.order_uuid)
            raise Custom_Exception(
                "Unable to update order status.",
                ErrorCode.DATABASE_ERROR,
                HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def get_item_by_uuid(self, session: AsyncSession, item_uuid: UUID):
        try:
            logger.info("Querying item by uuid")
            result = await session.execute(
                select(Item).where(Item.item_uuid == item_uuid)
            )
            return result.scalars().one_or_none()
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Database error while fetching item")
            raise Custom_Exception(
                "Unable to fetch item.",
                ErrorCode.DATABASE_ERROR,
                HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def create_item(self, session: AsyncSession, name: str, price: float):
        try:
            logger.info("Inserting new item")
            item = Item(
                item_uuid=uuid.uuid4(),
                name=name,
                price=price,
                is_active=True,
            )
            session.add(item)
            await session.flush()
            logger.info("Item created successfully")
            return item
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Database error while creating item ")
            raise Custom_Exception(
                "Unable to create item.",
                ErrorCode.DATABASE_ERROR,
                HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def update_item(self, session: AsyncSession, item: Item, name: str | None, price: float | None):
        try:
            logger.info("Updating item")
            if name is not None:
                item.name = name
            if price is not None:
                item.price = price
            item.updated_at = datetime.utcnow()
            item.updated_by = "ADMIN"
            await session.flush()
            logger.info("Item updated successfully")
            return item
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Database error while updating item_uuid: %s", item.item_uuid)
            raise Custom_Exception(
                "Unable to update item.",
                ErrorCode.DATABASE_ERROR,
                HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def delete_item(self, session: AsyncSession, item: Item):
        try:
            logger.info("Soft-deleting item")
            item.is_active = False
            item.updated_at = datetime.utcnow()
            item.updated_by = "ADMIN"
            await session.flush()
            logger.info("Item soft-deleted successfully")
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Database error while deleting item")
            raise Custom_Exception(
                "Unable to delete item.",
                ErrorCode.DATABASE_ERROR,
                HttpStatusCode.INTERNAL_SERVER_ERROR,
            )
