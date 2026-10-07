from pathlib import Path
from typing import Optional
from uuid import UUID

from repositories.schema.coffee_shop_models import OrderStatus
from repositories.database import get_db_session
from repositories.repository import ChatBotRepository
from routers.router import router
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger, with_async_request_id

logger = get_logger(__name__)

repository = ChatBotRepository()


@router.tool
@with_async_request_id
async def get_menu_tool():
    """Get all the items from menu with its price and unique item_id and return the list.
    Use when the customer asks to see all the items or the menu in the shop."""
    try:
        logger.info("Loading menu catalog")
        async for db_session in get_db_session():
            return await repository.get_menu(db_session)
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Failed to load menu catalog")
        raise Custom_Exception("The menu could not be retrieved.", ErrorCode.INTERNAL_SERVER_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR)


@router.tool
@with_async_request_id
async def get_shop_details_tool():
    """Stores all the details about the coffee shop including location, contact details, contacting person.
    Call when the customer needs to know about the shop details or needs to raise a query regarding the shop."""
    try:
        logger.info("Loading shop details")
        file_path = Path(__file__).resolve().parent.parent / "data" / "shop_details.txt"
        if not file_path.exists():
            return "Shop details file is not available."
        content = file_path.read_text(encoding="utf-8")
        return f"here's the details of the coffee shop {content}"
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Failed to load shop details")
        raise Custom_Exception("The shop details could not be retrieved.", ErrorCode.INTERNAL_SERVER_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR)


@router.tool
@with_async_request_id
async def place_order_tool(item_id: list[int], count: list[int], customer_id: UUID):
    """Places an order for the customer. Use when the customer wants to order one or multiple items from the menu.
    Provide item_id and count as separate lists matching by position, along with the customer_id.
    Always confirm the items and quantities with the customer before calling this tool."""
    try:
        if not item_id or len(item_id) != len(count) or any(value <= 0 for value in count):
            raise Custom_Exception("Each item must have a positive quantity.", ErrorCode.VALIDATION_ERROR, HttpStatusCode.BAD_REQUEST)
        logger.info("Processing order placement")
        async for db_session in get_db_session():
            customer = await repository.get_customer(db_session, customer_id)
            if not customer:
                raise Custom_Exception(
                    message="Customer not found for the provided customer_id.",
                    code=ErrorCode.USER_NOT_FOUND,
                    status_code=HttpStatusCode.NOT_FOUND,
                )
            total_amount = 0
            for item, cnt in zip(item_id, count):
                product = await repository.validate_item(db_session, item)
                if not product:
                    raise Custom_Exception(
                        message=f"Item {item} not found in the menu.",
                        code=ErrorCode.VALIDATION_ERROR,
                        status_code=HttpStatusCode.BAD_REQUEST,
                    )
                total_amount += product.price * cnt

            result = await repository.place_order(db_session, item_id, count, total_amount, customer)
            logger.info("Order placement completed")
            return result
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Failed to place order")
        raise Custom_Exception("The order could not be created.", ErrorCode.INTERNAL_SERVER_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR)


@router.tool
@with_async_request_id
async def get_order_tool(customer_id: UUID, order_id: Optional[int] = None):
    """Retrieves order details for the customer.
    - If order_id is provided, returns the full details of that specific order.
    - If order_id is omitted, returns a summary list of the customer's last 5 orders.
    Use when the customer wants to view an order status, order details, or their recent order history.
    Always requires customer_id. order_id is optional."""
    try:
        logger.info("Fetching order details")
        async for db_session in get_db_session():
            customer = await repository.get_customer(db_session, customer_id)
            if not customer:
                raise Custom_Exception(
                    message="Customer not found for the provided customer_id.",
                    code=ErrorCode.USER_NOT_FOUND,
                    status_code=HttpStatusCode.NOT_FOUND,
                )
            if order_id is not None:
                logger.info("Fetching specific order details")
                result = await repository.get_order_by_id(db_session, order_id, customer.customer_id)
            else:
                logger.info("Fetching recent orders summary")
                result = await repository.get_recent_orders(db_session, customer.customer_id)
            logger.info("Order details retrieved successfully")
            return result
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Failed to fetch order details")
        raise Custom_Exception("Order details could not be retrieved.", ErrorCode.INTERNAL_SERVER_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR)


@router.tool
@with_async_request_id
async def update_order_tool(order_id: int, item_id: list[int], count: list[int], customer_id: UUID):
    """Modifies an existing order by replacing its items and recalculating the total amount.
    Use when the customer wants to change items or adjust quantities in an order they have already placed.
    Only orders in 'ordered' status can be modified — orders that are processing or completed cannot be changed.
    Requires the order_id, the new item_id list, the new count list, and customer_id.
    Always confirm the updated items and quantities with the customer before calling this tool."""
    try:
        if not item_id or len(item_id) != len(count) or any(value <= 0 for value in count):
            raise Custom_Exception("Each item must have a positive quantity.", ErrorCode.VALIDATION_ERROR, HttpStatusCode.BAD_REQUEST)
        logger.info("Processing order update")
        async for db_session in get_db_session():
            customer = await repository.get_customer(db_session, customer_id)
            if not customer:
                raise Custom_Exception(
                    message="Customer not found for the provided customer_id.",
                    code=ErrorCode.USER_NOT_FOUND,
                    status_code=HttpStatusCode.NOT_FOUND,
                )
            order = await repository.validate_order(db_session, order_id)
            if not order:
                raise Custom_Exception(
                    message="Order not found.",
                    code=ErrorCode.USER_NOT_FOUND,
                    status_code=HttpStatusCode.NOT_FOUND,
                )
            if order.customer_id != customer.customer_id:
                raise Custom_Exception(
                    message="This order does not belong to the given customer.",
                    code=ErrorCode.VALIDATION_ERROR,
                    status_code=HttpStatusCode.BAD_REQUEST,
                )
            if order.order_status != OrderStatus.ordered:
                raise Custom_Exception(
                    message=f"Order cannot be modified because it is already in '{order.order_status.value}' status.",
                    code=ErrorCode.VALIDATION_ERROR,
                    status_code=HttpStatusCode.BAD_REQUEST,
                )

            result = await repository.update_order(
                db_session, order_id, customer.customer_id, item_id, count, order)
            await db_session.commit()
            
            logger.info("Order update completed")
            return result
    except Custom_Exception:
        await db_session.rollback()
        raise
    except Exception:
        await db_session.rollback()
        logger.exception("Failed to update order")
        raise Custom_Exception("The order could not be updated.", ErrorCode.INTERNAL_SERVER_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR)


@router.tool
@with_async_request_id
async def cancel_order_tool(order_id: int, customer_id: UUID):
    """Cancels an existing order for the customer.
    Use when the customer explicitly asks to cancel an order they have placed.
    Only orders in 'ordered' status can be cancelled — orders that are processing or completed cannot be cancelled.
    Requires the order_id and the customer_id.
    Always confirm with the customer before calling this tool."""
    try:
        logger.info("Processing order cancellation")
        async for db_session in get_db_session():
            customer = await repository.get_customer(db_session, customer_id)
            if not customer:
                raise Custom_Exception(
                    message="Customer not found for the provided customer_id.",
                    code=ErrorCode.USER_NOT_FOUND,
                    status_code=HttpStatusCode.NOT_FOUND,
                )

            order = await repository.validate_order(db_session, order_id)
            if not order:
                raise Custom_Exception(
                    message="Order not found.",
                    code=ErrorCode.USER_NOT_FOUND,
                    status_code=HttpStatusCode.NOT_FOUND,
                )
            if order.customer_id != customer.customer_id:
                raise Custom_Exception(
                    message="This order does not belong to the given customer.",
                    code=ErrorCode.VALIDATION_ERROR,
                    status_code=HttpStatusCode.BAD_REQUEST,
                )
            if order.order_status != OrderStatus.ordered:
                raise Custom_Exception(
                    message=f"Order cannot be cancelled because it is already in '{order.order_status.value}' status.",
                    code=ErrorCode.VALIDATION_ERROR,
                    status_code=HttpStatusCode.BAD_REQUEST,
                )

            result = await repository.cancel_order(db_session, order_id, customer.customer_id, order)
            logger.info("Order cancellation completed")
            return result
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Failed to cancel order")
        raise Custom_Exception("The order could not be cancelled.", ErrorCode.INTERNAL_SERVER_ERROR, HttpStatusCode.INTERNAL_SERVER_ERROR)
