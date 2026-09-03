from fastmcp import FastMCP
router = FastMCP("router")

from tools.tool import get_order_tool, place_order_tool 
# router.add_tool(get_order_tool)
# router.add_tool(place_order_tool)

from resources.resources import get_menu_resource, get_shop_details
# router.add_resource(get_menu_resource)
# router.add_resource(get_shop_details)

from prompts.prompt import order_assistant_prompt, order_status_prompt
# router.add_prompt(order_assistant_prompt)
# router.add_prompt(order_status_prompt)