from repositories.database import get_db_session
from repositories.repository import ChatBotRepository
from routers.router import router
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.logger import get_logger

logger = get_logger(__name__)

repository = ChatBotRepository()


@router.tool
async def place_order_tool(item_id: list[int], count: list[int], customer_id: int):
    """Places order for the customer. Use when the customer wants to order some items in the menu.
    If customer wants to order one or multiple items, give the item_id and the count as separate list in name items, item_count as input with the customer_id as integer.
    """
    try:
        logger.info("Processing order placement for customer_id=%s with %s item(s)", customer_id, len(item_id))
        async for db_session in get_db_session():
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
            logger.info("Order placement completed for customer_id=%s", customer_id)
            return result
    except Custom_Exception:
        raise
    except Exception as e:
        logger.exception("Failed to place order for customer_id=%s", customer_id)
        return f"can't create order {str(e)}"


@router.tool
async def get_order_tool(customer_id: int):
    """Collects customer_id from user and checks the presence of order for the customer and the other details of the order.
    Use when the customer wants to view the details or the status of their order.
    Must get the customer_id from customer to check the status of their order & order_id is not mandatory"""
    try:
        logger.info("Fetching order details for customer_id=%s", customer_id)
        async for db_session in get_db_session():
            result = await repository.get_order_detail_repository(db_session, customer_id)
            logger.info("Order details retrieved for customer_id=%s", customer_id)
            return result
    except Custom_Exception:
        raise
    except Exception as e:
        logger.exception("Failed to fetch order details for customer_id=%s", customer_id)
        return f"can't get order details because of {str(e)}"