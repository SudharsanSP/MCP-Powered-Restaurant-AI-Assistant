from __future__ import annotations

from typing import Optional, Literal

from pydantic import BaseModel, Field

class UserQuery(BaseModel):
    user_query: str = Field(min_length=1, max_length=1000)

class HITLRequest(BaseModel):
    decision: Literal["approve", "reject"]

class MenuResponse(BaseModel):
    """Consume this model if & only if you wanted to return a Menu to the user or get_menu_tool is called"""
    model_response: str = Field(description= "General response about the shop from the model")
    menu_items: MenuList = Field(description= "All the items available in menu")

class OrderResponse(BaseModel):
    """Consume this if & only if you wanted to return an order been placed as a response"""
    model_response: str = Field(description= "General cheering response from the model with greeting and thanking for order")
    order_id: int = Field(description= "Order id of the placed order")
    order_items: Optional[list[MenuList]] = Field(description="List of items in the order")
    total_amount: int = Field(description="Total amount of the order")

class StatusResponse(BaseModel):
    """Consume this model if & only if you wanted to provide order status as response"""
    model_response: str = Field(description= "General response from the model with ordered items only")
    order_id: int = Field(description= "Order id of the order")    
    order_status: dict = Field(description= "Status of the order")

class MenuList(BaseModel):
    """Use this model for validation of keys in list of menu items dictionary"""
    id: int  = Field(description= "Serial number for the list")
    name: str = Field(description= "Name of each item")
    price: float = Field(description= "Price of the item")

class GeneralResponse(BaseModel):
    """Consume this if no tool call required or the request and the response is very general or greeting messages"""
    model_response: str = Field(description= "Just a greeting message")