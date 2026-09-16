from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.schema.coffee_shop_models import Order, Order_Item
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger

logger = get_logger(__name__)
class AdminRepository:

    async def get_orders(self, session: AsyncSession):
        try:
            logger.info("Fetching all orders")
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
            logger.exception("Failed to fetch orders")
            raise Custom_Exception(
                "Unable to fetch orders.",
                ErrorCode.DATABASE_ERROR,
                HttpStatusCode.INTERNAL_SERVER_ERROR,
            )
