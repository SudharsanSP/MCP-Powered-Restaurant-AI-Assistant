from pathlib import Path
from typing import Optional
from uuid import UUID

from sqlalchemy.future import select
from sqlalchemy import func, desc

from repositories.schema.coffee_shop_models import OrderStatus, Order, Order_Item, Item, Customer
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
        if "db_session" in locals() and db_session is not None:
            await db_session.rollback()
        raise
    except Exception:
        if "db_session" in locals() and db_session is not None:
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


# ---------------------------------------------------------------------------
# Manager / Admin tools — used exclusively by the /agent autonomous endpoint
# ---------------------------------------------------------------------------

@router.tool
@with_async_request_id
async def get_all_orders_tool(limit: int = 100):
    """Retrieve all orders across every customer for management reporting.
    Returns a list of orders with order_id, customer name, item names,
    quantities, total_amount, order_status, and created_at.
    Use when the manager requests a sales report, order summary, or any
    analytics that requires a global view of all orders."""
    try:
        logger.info("Fetching all orders for manager report")
        async for db_session in get_db_session():
            result = await db_session.execute(
                select(
                    Order.order_id,
                    Order.total_amount,
                    Order.order_status,
                    Order.created_at,
                    Customer.name.label("customer_name"),
                )
                .join(Customer, Customer.customer_id == Order.customer_id)
                .where(Order.is_active.is_(True))
                .order_by(desc(Order.created_at))
                .limit(limit)
            )
            rows = result.all()

            orders = []
            for row in rows:
                items_result = await db_session.execute(
                    select(Item.name, Order_Item.item_count)
                    .join(Order_Item, Order_Item.item_id == Item.item_id)
                    .where(
                        Order_Item.order_id == row.order_id,
                        Order_Item.is_active.is_(True),
                        Item.is_active.is_(True),
                    )
                )
                item_list = [
                    {"name": name, "quantity": count}
                    for name, count in items_result.all()
                ]
                orders.append(
                    {
                        "order_id": row.order_id,
                        "customer_name": row.customer_name,
                        "items": item_list,
                        "total_amount": row.total_amount,
                        "order_status": row.order_status.value
                        if hasattr(row.order_status, "value")
                        else str(row.order_status),
                        "created_at": row.created_at.isoformat()
                        if row.created_at
                        else None,
                    }
                )
            logger.info("All orders fetched successfully")
            return {"orders": orders, "total_count": len(orders)}
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Failed to fetch all orders")
        raise Custom_Exception(
            "All orders could not be retrieved.",
            ErrorCode.INTERNAL_SERVER_ERROR,
            HttpStatusCode.INTERNAL_SERVER_ERROR,
        )


@router.tool
@with_async_request_id
async def get_top_items_tool(limit: int = 5):
    """Analyse order history to rank menu items by total quantity ordered.
    Returns each item's name, total units sold, number of distinct orders
    it appeared in, and its revenue contribution.
    Use for sales reports, menu review documents, and expansion proposals."""
    try:
        logger.info("Calculating top selling items")
        async for db_session in get_db_session():
            result = await db_session.execute(
                select(
                    Item.item_id,
                    Item.name,
                    Item.price,
                    func.sum(Order_Item.item_count).label("total_units_sold"),
                    func.count(Order_Item.order_id.distinct()).label("order_count"),
                )
                .join(Order_Item, Order_Item.item_id == Item.item_id)
                .join(Order, Order.order_id == Order_Item.order_id)
                .where(
                    Item.is_active.is_(True),
                    Order_Item.is_active.is_(True),
                    Order.is_active.is_(True),
                )
                .group_by(Item.item_id, Item.name, Item.price)
                .order_by(desc("total_units_sold"))
                .limit(limit)
            )
            rows = result.all()
            ranked = [
                {
                    "rank": idx + 1,
                    "item_id": row.item_id,
                    "name": row.name,
                    "price": row.price,
                    "total_units_sold": int(row.total_units_sold),
                    "order_count": int(row.order_count),
                    "revenue_contribution": round(row.price * int(row.total_units_sold), 2),
                }
                for idx, row in enumerate(rows)
            ]
            logger.info("Top items calculated successfully")
            return {"top_items": ranked}
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Failed to calculate top items")
        raise Custom_Exception(
            "Top items could not be retrieved.",
            ErrorCode.INTERNAL_SERVER_ERROR,
            HttpStatusCode.INTERNAL_SERVER_ERROR,
        )


@router.tool
@with_async_request_id
async def get_order_stats_tool():
    """Return aggregate order statistics for management reporting.
    Provides: total orders, total revenue, average order value,
    and a breakdown of order count and revenue by each order status
    (ordered, processing, pending, completed).
    Use as the quick-stats step in any sales or performance report."""
    try:
        logger.info("Computing order statistics")
        async for db_session in get_db_session():
            # Overall aggregates
            overall = await db_session.execute(
                select(
                    func.count(Order.order_id).label("total_orders"),
                    func.coalesce(func.sum(Order.total_amount), 0).label("total_revenue"),
                    func.coalesce(func.avg(Order.total_amount), 0).label("avg_order_value"),
                ).where(Order.is_active.is_(True))
            )
            overall_row = overall.one()

            # Per-status breakdown
            status_result = await db_session.execute(
                select(
                    Order.order_status,
                    func.count(Order.order_id).label("count"),
                    func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
                )
                .where(Order.is_active.is_(True))
                .group_by(Order.order_status)
            )
            status_rows = status_result.all()
            status_breakdown = [
                {
                    "status": row.order_status.value
                    if hasattr(row.order_status, "value")
                    else str(row.order_status),
                    "order_count": int(row.count),
                    "revenue": round(float(row.revenue), 2),
                }
                for row in status_rows
            ]

            logger.info("Order statistics computed successfully")
            return {
                "total_orders": int(overall_row.total_orders),
                "total_revenue": round(float(overall_row.total_revenue), 2),
                "average_order_value": round(float(overall_row.avg_order_value), 2),
                "status_breakdown": status_breakdown,
            }
    except Custom_Exception:
        raise
    except Exception:
        logger.exception("Failed to compute order statistics")
        raise Custom_Exception(
            "Order statistics could not be retrieved.",
            ErrorCode.INTERNAL_SERVER_ERROR,
            HttpStatusCode.INTERNAL_SERVER_ERROR,
        )
