from pathlib import Path
from repositories.database import get_db_session
from uuid import UUID
from repositories.repository import ChatBotRepository
from routers.router import router
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.logger import get_logger, with_async_request_id

logger = get_logger(__name__)

repository = ChatBotRepository()

@router.tool
@with_async_request_id
async def get_menu_tool():
    """Get all the items from menu with its price and unique item_id and return the list.
    Use when the customer asks to see all the items or the menu in the shop"""
    try:
        logger.info("Loading menu catalog")
        async for db_session in get_db_session():
            return await repository.get_menu_repository(db_session)
    except Custom_Exception:
        raise
    except Exception as e:
        logger.exception("Failed to load menu catalog")
        return f"can't get menu because of {str(e)}"


@router.tool
@with_async_request_id
async def get_shop_details_tool():
    """Stores all the details about the coffee shop including location, contact details, contacting person.
    Calls when the customer needs to know about the shop details or needs to raise query regaring the shop."""
    try:
        logger.info("Loading shop details")
        file_path = Path(__file__).resolve().parent.parent / "data" / "shop_details.txt"
        if not file_path.exists():
            return "Shop details file is not available."
        content = file_path.read_text(encoding="utf-8")
        return f"here's the details of the coffee shop {content}"
    except Custom_Exception:
        raise
    except Exception as e:
        logger.exception("Failed to load shop details")
        return f"can't get menu because of {str(e)}"

@router.tool
@with_async_request_id
async def place_order_tool(item_id: list[int], count: list[int], customer_id: UUID):
    """Places order for the customer. Use when the customer wants to order some items in the menu.
    If customer wants to order one or multiple items, give the item_id and the count as separate list in name items, item_count as input with the customer_id as integer.
    """
    try:
        if not item_id or len(item_id) != len(count) or any(value <= 0 for value in count):
            raise Custom_Exception("Each item must have a positive quantity.", "VALIDATION_ERROR", 400)
        logger.info("Processing order placement")
        async for db_session in get_db_session():
            customer = await self.get_customer(db_session, customer_id)
            if customer is None:
                raise Custom_Exception(
                    message="Customer not found for the provided customer_id",
                    code=ErrorCode.USER_NOT_FOUND,
                    status_code=HttpStatusCode.NOT_FOUND,
                )
            total_amount = 0
            for item, cnt in zip(item_id, count):
                product = await repository.validate_item(db_session, item)
                if not product:
                    raise Custom_Exception(
                        message=f"Item {item} not found in the menu",
                        code="ITEM_NOT_FOUND",
                        status_code=404,
                    )
                total_amount += int(product.price) * cnt

            result = await repository.place_order_repository(db_session, item_id, count, total_amount, customer_id)
            logger.info("Order placement completed")
            return result
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Failed to place order")
        raise Custom_Exception("The order could not be created.", "INTERNAL_SERVER_ERROR", 500)


@router.tool
@with_async_request_id
async def get_order_tool(customer_id: UUID):
    """Collects customer_id from user and checks the presence of order for the customer and the other details of the order.
    Use when the customer wants to view the details or the status of their order.
    Must get the customer_id from customer to check the status of their order & order_id is not mandatory"""
    try:
        logger.info("Fetching order details")
        async for db_session in get_db_session():
            customer = await repository.get_customer(db_session, customer_id)
            if not customer:
                raise Custom_Exception("Error occured in validating Customer ID.", "INVALID_DATA", 400)
            result = await repository.get_order_detail_repository(db_session, customer.customer_id)
            logger.info("Order details retrieved")
            return result
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Failed to fetch order details")
        raise Custom_Exception("Order details could not be retrieved.", "INTERNAL_SERVER_ERROR", 500)