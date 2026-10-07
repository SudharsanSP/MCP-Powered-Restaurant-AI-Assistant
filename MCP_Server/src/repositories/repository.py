from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from repositories.schema.coffee_shop_models import Customer, Order, Order_Item, Item, OrderStatus
from utilities.exceptions.http_status import HttpStatusCode
from repositories.database import Database
from utilities.logger import get_logger

logger = get_logger(__name__)


class ChatBotRepository:
    db_instance = Database()

    async def get_customer(self, db_session: AsyncSession, customer_id: UUID):
        try:
            logger.info("Fetching customer record")
            result = await db_session.execute(
                select(Customer).where(Customer.customer_uuid == customer_id, Customer.is_active.is_(True))
            )
            return result.scalar_one_or_none()
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to fetch customer record")
            raise Custom_Exception(
                message="The customer could not be retrieved.",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def get_order(self, db_session: AsyncSession, customer_id: int):
        try:
            logger.info("Fetching latest order")
            result = await db_session.execute(
                select(Order)
                .where(Order.customer_id == customer_id, Order.is_active.is_(True))
                .order_by(desc(Order.created_at))
                .limit(1)
            )
            return result.scalar_one_or_none()
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to fetch latest order")
            raise Custom_Exception(
                message="The order could not be retrieved.",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def get_order_details(self, db_session: AsyncSession, order_id: int):
        try:
            logger.info("Fetching order items")
            result = await db_session.execute(
                select(Order_Item).where(Order_Item.order_id == order_id, Order_Item.is_active.is_(True))
            )
            return result.scalars().all()
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to fetch order items")
            raise Custom_Exception(
                message="The order details could not be retrieved.",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def validate_item(self, db_session: AsyncSession, item_id: int):
        try:
            logger.info("Validating menu item")
            result = await db_session.execute(
                select(Item).where(Item.item_id == item_id, Item.is_active.is_(True))
            )
            return result.scalar_one_or_none()
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to validate menu item")
            raise Custom_Exception(
                message="The menu item could not be validated.",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def validate_order(self, db_session: AsyncSession, order_id: int):
        try:
            logger.info("Validating order")
            result = await db_session.execute(
                select(Order).where(Order.order_id == order_id, Order.is_active.is_(True))
            )
            return result.scalar_one_or_none()
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to validate order")
            raise Custom_Exception(
                message="The order could not be validated.",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def get_menu(self, db_session: AsyncSession):
        try:
            logger.info("Loading menu catalog")
            result = await db_session.execute(select(Item).where(Item.is_active.is_(True)))
            items = result.scalars().all()
            menu = [
                {"id": item.item_id, "name": item.name, "price": item.price}
                for item in items
            ]
            return {"items": menu}
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to load menu catalog")
            raise Custom_Exception(
                message="The menu could not be retrieved.",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def place_order(self, db_session: AsyncSession, item_id, count, total_amount, customer: Customer):
        try:
            logger.info("Creating order")
            new_order = Order(
                customer_id=customer.customer_id,
                total_amount=total_amount,
                created_by=customer.name,
            )
            db_session.add(new_order)
            await db_session.flush()

            for item_id, cnt in zip(item_id, count):
                db_session.add(
                    Order_Item(
                        order_id=new_order.order_id,
                        item_id=item_id,
                        item_count=cnt,
                    )
                )

            await db_session.commit()
            logger.info("Order placed successfully")
            return {
                "order_id": new_order.order_id,
                "total_amount": total_amount,
                "message": f"Order placed successfully for customer_id {customer.customer_id}",
            }
        except Custom_Exception:
            await db_session.rollback()
            raise
        except Exception:
            await db_session.rollback()
            logger.exception("Failed to place order")
            raise Custom_Exception(
                message="The order could not be created.",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def get_order_detail(self, db_session: AsyncSession, customer_id: int):
        try:
            logger.info("Retrieving latest order details")
            order = await self.get_order(db_session, customer_id)
            if not order:
                return {"message": "There is no order for this customer."}

            result = await db_session.execute(
                select(Item.item_id, Item.name, Order_Item.item_count)
                .select_from(Item)
                .join(Order_Item, Order_Item.item_id == Item.item_id)
                .where(
                    Order_Item.order_id == order.order_id,
                    Order_Item.is_active.is_(True),
                    Item.is_active.is_(True),
                )
            )

            item_list = [
                {"id": item_id, "name": name, "count": count}
                for item_id, name, count in result.all()
            ]

            return {
                "order_id": order.order_id,
                "order_status": order.order_status.value if hasattr(order.order_status, "value") else str(order.order_status),
                "items": item_list,
                "total_amount": order.total_amount,
            }
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to fetch latest order details")
            raise Custom_Exception(
                message="The order details could not be retrieved.",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def get_order_by_id(self, db_session: AsyncSession, order_id: int, customer_id: int):
        try:
            logger.info("Retrieving order details by order")
            result = await db_session.execute(
                select(Order).where(
                    Order.order_id == order_id,
                    Order.customer_id == customer_id,
                    Order.is_active.is_(True),
                )
            )
            order = result.scalar_one_or_none()
            if not order:
                return {"message": "Order not found for this customer."}

            items_result = await db_session.execute(
                select(Item.item_id, Item.name, Order_Item.item_count)
                .select_from(Item)
                .join(Order_Item, Order_Item.item_id == Item.item_id)
                .where(
                    Order_Item.order_id == order.order_id,
                    Order_Item.is_active.is_(True),
                    Item.is_active.is_(True),
                )
            )

            item_list = [
                {"id": item_id, "name": name, "count": count}
                for item_id, name, count in items_result.all()
            ]

            logger.info("Order details retrieved successfully")
            return {
                "order_id": order.order_id,
                "order_status": order.order_status.value if hasattr(order.order_status, "value") else str(order.order_status),
                "items": item_list,
                "total_amount": order.total_amount,
            }
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to fetch order details")
            raise Custom_Exception(
                message="The order details could not be retrieved.",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def get_recent_orders(self, db_session: AsyncSession, customer_id: int):
        try:
            logger.info("Retrieving recent orders summary")
            result = await db_session.execute(
                select(Order)
                .where(Order.customer_id == customer_id, Order.is_active.is_(True))
                .order_by(desc(Order.created_at))
                .limit(5)
            )
            orders = result.scalars().all()
            if not orders:
                return {"message": "No recent orders found for this customer."}

            summary = [
                {
                    "order_id": order.order_id,
                    "order_status": order.order_status.value if hasattr(order.order_status, "value") else str(order.order_status),
                    "total_amount": order.total_amount,
                    "ordered_at": order.created_at.isoformat() if order.created_at else None,
                }
                for order in orders
            ]
            logger.info("Recent orders retrieved successfully")
            return {"orders": summary}
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to fetch recent orders")
            raise Custom_Exception(
                message="Recent orders could not be retrieved.",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def update_order(
        self,
        db_session: AsyncSession,
        order_id: int,
        customer_id: int,
        item_ids: list[int],
        counts: list[int],
        order: Order
    ):
        try:
            logger.info("Updating order")
            existing_items_result = await db_session.execute(
                select(Order_Item).where(
                    Order_Item.order_id == order_id,
                    Order_Item.is_active.is_(True),
                )
            )
            existing_items = existing_items_result.scalars().all()
            for existing_item in existing_items:
                existing_item.is_active = False
                existing_item.updated_at = datetime.utcnow()
                existing_item.updated_by = "CUSTOMER"
            await db_session.flush()
            logger.info("Existing order items removed")

            total_amount = 0.0
            for item_id, cnt in zip(item_ids, counts):
                product = await self.validate_item(db_session, item_id)
                if not product:
                    raise Custom_Exception(
                        message=f"Item {item_id} not found in the menu.",
                        code=ErrorCode.VALIDATION_ERROR,
                        status_code=HttpStatusCode.BAD_REQUEST,
                    )
                total_amount += product.price * cnt
                db_session.add(
                    Order_Item(
                        order_id=order_id,
                        item_id=item_id,
                        item_count=cnt,
                    )
                )

            order.total_amount = total_amount
            order.updated_at = datetime.now()
            order.updated_by = "CUSTOMER"
            await db_session.flush()
            logger.info("Order updated successfully")
            return {
                "order_id": order_id,
                "total_amount": total_amount,
                "message": "Order updated successfully.",
            }
        except Custom_Exception:
            raise
        except Exception:
            logger.exception("Failed to update order")
            raise Custom_Exception(
                message="The order could not be updated.",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def cancel_order(self, db_session: AsyncSession, order_id: int, customer_id: int, order: Order):
        try:
            logger.info("Cancelling order")

            order.is_active = False
            order.updated_at = datetime.utcnow()
            order.updated_by = "CUSTOMER"

            items_result = await db_session.execute(
                select(Order_Item).where(
                    Order_Item.order_id == order_id,
                    Order_Item.is_active.is_(True),
                )
            )
            order_items = items_result.scalars().all()
            for order_item in order_items:
                order_item.is_active = False
                order_item.updated_at = datetime.utcnow()
                order_item.updated_by = "CUSTOMER"

            await db_session.commit()
            logger.info("Order cancelled successfully")
            return {"order_id": order_id, "message": "Order cancelled successfully."}
        except Custom_Exception:
            await db_session.rollback()
            raise
        except Exception:
            await db_session.rollback()
            logger.exception("Failed to cancel order")
            raise Custom_Exception(
                message="The order could not be cancelled.",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )
