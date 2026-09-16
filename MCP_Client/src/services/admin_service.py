from models.admin import GetOrdersResponse, CustomerDetails, OrderItems
from repositories.admin_repository import AdminRepository
from repositories.database import get_db_session
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger

logger = get_logger(__name__)

class AdminService:
    def __init__(self) -> None:
        self.repository = AdminRepository()

    async def get_orders(self):
        order_data = []
        async for session in get_db_session():
            try:
                logger.info("Started fetching orders")
                orders = await self.repository.get_orders(session)
                for order in orders:
                    order_data.append(
                        GetOrdersResponse(
                            order_uuid = str(order.order_uuid),
                            order_status = order.order_status,
                            total_amount = order.total_amount,
                            ordered_at = order.created_at,
                            customer = CustomerDetails(
                                customer_uuid = str(order.customer.customer_uuid),
                                name = order.customer.name,
                                phone_number = order.customer.phone_number
                            ),
                            items = [
                                OrderItems(
                                    name = item.item.name,
                                    price= item.item.price,
                                    count = item.item_count
                                )
                                for item in order.order_items
                            ]
                        )
                    )
                logger.info("Fetching orders completed")
                return order_data
            except Custom_Exception:
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                logger.exception("Fetching orders failed")
                raise Custom_Exception(
                    "Unable to fetch orders.",
                    ErrorCode.INTERNAL_SERVER_ERROR,
                    HttpStatusCode.INTERNAL_SERVER_ERROR,
                )
