from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

class UserQuery(BaseModel):
    user_query: str

class MenuResponse(BaseModel):
    """Consume this model if & only if you wanted to return a Menu to the user"""
    model_response: str = Field(description= "General response about the shop from the model")
    menu_items: MenuList = Field(description= "All the items available in menu")

class OrderResponse(BaseModel):
    """Consume this if & only if you wanted to return an order been placed as a response"""
    model_response: str = Field(description= "General response from the model")
    order_id: int = Field(description= "Order id of the placed order")
    order_items: Optional[list[dict[str, MenuList]]] = Field(description="List of items in the order")
    total_amount: float = Field(description="Total amount of the order")

class StatusResponse(BaseModel):
    """Consume this model if & only if you wanted to provide order status as response"""
    order_id: int = Field(description= "Order id of the order")    
    order_status: dict = Field(description= "Status of the order")

class MenuList(BaseModel):
    """Use this model for validation of keys in list of itams dictionary"""
    id: int  = Field(description= "Unique id for each item")
    name: str = Field(description= "name of each item")
    price: float = Field(description= "price of the item")