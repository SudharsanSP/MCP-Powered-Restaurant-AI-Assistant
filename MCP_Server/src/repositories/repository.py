from __future__ import annotations

from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from repositories.database import Database
from utilities.logger import get_logger
from repositories.schema.coffee_shop_models import Customer, Order, Order_Item, Item

logger = get_logger(__name__)


class ChatBotRepository:
    db_instance = Database()

    async def get_customer(self, db_session: AsyncSession, customer_id: int):
        try:
            logger.info("Fetching customer record for customer_id=%s", customer_id)
            result = await db_session.execute(
                select(Customer).where(Customer.customer_id == customer_id)
            )
            return result.scalar_one_or_none()
        except Custom_Exception:
            raise
        except Exception as exc:
            logger.exception("Failed to fetch customer customer_id=%s", customer_id)
            raise Custom_Exception(
                message=f"Repository error: {exc}",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def get_order(self, db_session: AsyncSession, customer_id: int):
        try:
            logger.info("Fetching latest order for customer_id=%s", customer_id)
            result = await db_session.execute(
                select(Order)
                .where(Order.customer_id == customer_id)
                .order_by(desc(Order.created_at))
            )
            return result.scalar_one_or_none()
        except Custom_Exception:
            raise
        except Exception as exc:
            logger.exception("Failed to fetch order for customer_id=%s", customer_id)
            raise Custom_Exception(
                message=f"Repository error: {exc}",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def get_order_details(self, db_session: AsyncSession, order_id: int):
        try:
            logger.info("Fetching order items for order_id=%s", order_id)
            result = await db_session.execute(
                select(Order_Item).where(Order_Item.order_id == order_id)
            )
            return result.scalars().all()
        except Custom_Exception:
            raise
        except Exception as exc:
            logger.exception("Failed to fetch order details for order_id=%s", order_id)
            raise Custom_Exception(
                message=f"Repository error: {exc}",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def validate_item(self, db_session: AsyncSession, item_id: int):
        try:
            logger.info("Validating menu item item_id=%s", item_id)
            result = await db_session.execute(
                select(Item).where(Item.item_id == item_id)
            )
            return result.scalar_one_or_none()
        except Custom_Exception:
            raise
        except Exception as exc:
            logger.exception("Failed to validate item item_id=%s", item_id)
            raise Custom_Exception(
                message=f"Repository error: {exc}",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def validate_order(self, db_session: AsyncSession, order_id: int):
        try:
            logger.info("Validating order order_id=%s", order_id)
            result = await db_session.execute(
                select(Order).where(Order.order_id == order_id)
            )
            return result.scalar_one_or_none()
        except Custom_Exception:
            raise
        except Exception as exc:
            logger.exception("Failed to validate order order_id=%s", order_id)
            raise Custom_Exception(
                message=f"Repository error: {exc}",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def get_menu_repository(self, db_session: AsyncSession):
        try:
            logger.info("Loading menu catalog")
            result = await db_session.execute(select(Item))
            items = result.scalars().all()
            menu = [
                {"id": item.item_id, "name": item.name, "price": item.price}
                for item in items
            ]
            return {"items": menu}
        except Custom_Exception:
            raise
        except Exception as exc:
            logger.exception("Failed while fetching menu catalog")
            raise Custom_Exception(
                message=f"Repository error: {exc}",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def place_order_repository(self, db_session: AsyncSession, item_id, count, total_amount, customer_id):
        try:
            logger.info("Creating order for customer_id=%s", customer_id)
            customer = await self.get_customer(db_session, customer_id)
            if customer is None:
                raise Custom_Exception(
                    message="Customer not found for the provided customer_id",
                    code=ErrorCode.USER_NOT_FOUND,
                    status_code=HttpStatusCode.NOT_FOUND,
                )

            new_order = Order(
                customer_id=customer_id,
                total_amount=total_amount,
                created_by=customer.name,
            )
            db_session.add(new_order)
            await db_session.flush()

            for item, cnt in zip(item_id, count):
                db_session.add(
                    Order_Item(
                        order_id=new_order.order_id,
                        item_id=item,
                        item_count=cnt,
                    )
                )

            await db_session.commit()
            logger.info("Order placed successfully. order_id=%s customer_id=%s", new_order.order_id, customer_id)
            return {
                "order_id": new_order.order_id,
                "total_amount": total_amount,
                "message": f"Order placed successfully for customer_id {customer_id}",
            }
        except Custom_Exception:
            await db_session.rollback()
            raise
        except Exception as exc:
            await db_session.rollback()
            logger.exception("Failed to place order for customer_id=%s", customer_id)
            raise Custom_Exception(
                message=f"Repository error: {exc}",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )

    async def get_order_detail_repository(self, db_session: AsyncSession, customer_id):
        try:
            logger.info("Retrieving order details for customer_id=%s", customer_id)
            order = await self.get_order(db_session, customer_id)
            if not order:
                return {"message": "There is no order for this customer."}

            result = await db_session.execute(
                select(Item.item_id, Item.name, Order_Item.item_count)
                .select_from(Item)
                .join(Order_Item, Order_Item.item_id == Item.item_id)
                .where(Order_Item.order_id == order.order_id)
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
        except Exception as exc:
            logger.exception("Failed to fetch order detail for customer_id=%s", customer_id)
            raise Custom_Exception(
                message=f"Repository error: {exc}",
                code=ErrorCode.DATABASE_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )
