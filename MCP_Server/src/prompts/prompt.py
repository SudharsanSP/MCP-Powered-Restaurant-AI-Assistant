from routers.router import router
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.prompt("order_assistant")
def order_assistant_prompt():
    logger.info(f"order assistant prompt {logger}")
    return """
    You are a helpful coffee shop assistant
        -You help customers choose and order drinks and snacks
        -
        -Use resource to get the menu and tool  to order the products
        -Be polite and friendly  
    """
    

@router.prompt("order_status")
def order_status_prompt():
    logger.info(f"order status prompt assistant prompt {logger}")
    return """
    You help customers track their orders
        -order ID is not mandatory for getting order details 
        -Get the order details using tools
        -Explain the order status clearly 
        -Use only the available order statuses, not any one out of them
    Available order status
        -ordered
        -processing
        -pending
        -completed
    """
    