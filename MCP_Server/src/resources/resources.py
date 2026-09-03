from pathlib import Path

from repositories.database import get_db_session
from repositories.repository import ChatBotRepository
from routers.router import router
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.logger import get_logger

logger = get_logger(__name__)
repository = ChatBotRepository()


@router.resource("resource://menu")
async def get_menu_resource():
    """Get all the items from menu with its price and unique item_id and return the list.
    Use when the customer asks to see all the items or the menu in the shop"""
    try:
        logger.info("Loading menu resource")
        async for db_session in get_db_session():
            return await repository.get_menu_repository(db_session)
    except Custom_Exception:
        raise
    except Exception as e:
        logger.exception("Failed to load menu resource")
        return f"can't get menu because of {str(e)}"


@router.resource("resource://shop_details")
def get_shop_details():
    """Stores all the details about the coffee shop including location, contact details, contacting person.
    Calls when the customer needs to know about the shop details or needs to raise query regaring the shop."""
    try:
        logger.info("Loading shop details resource")
        file_path = Path(__file__).resolve().parent.parent / "data" / "shop_details.txt"
        if not file_path.exists():
            return "Shop details file is not available."
        content = file_path.read_text(encoding="utf-8")
        return f"here's the details of the coffee shop {content}"
    except Custom_Exception:
        raise
    except Exception as e:
        logger.exception("Failed to load shop details resource")
        return f"can't get menu because of {str(e)}"
    