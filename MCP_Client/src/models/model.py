from __future__ import annotations

from typing import Optional, Literal

from pydantic import BaseModel, Field



class AgentRequest(BaseModel):
    """Request body for POST /agent."""
    request: str = Field(
        min_length=5,
        max_length=2000,
        description="Natural language business request for the manager agent.",
    )


class TaskItem(BaseModel):
    """A single step in the autonomous execution plan."""
    step: int = Field(description="Step number (1-based).")
    description: str = Field(description="What this step does.")
    tool: Optional[str] = Field(default=None, description="MCP tool called for this step, if any.")
    status: Literal["pending", "completed", "failed"] = Field(
        default="pending",
        description="Execution status of this step.",
    )


class AgentResponse(BaseModel):
    """Response body returned by POST /agent."""
    task_list: list[TaskItem] = Field(description="Ordered list of tasks the agent planned and executed.")
    assumptions: list[str] = Field(
        default_factory=list,
        description="Assumptions the agent made when the request was ambiguous.",
    )
    summary: str = Field(description="Human-readable summary of what the agent produced.")
    document_filename: str = Field(description="Filename of the generated .docx document.")


class UserQuery(BaseModel):
    user_query: str = Field(min_length=1, max_length=1000)

class HITLRequest(BaseModel):
    decision: Literal["approve", "reject"]

class MenuList(BaseModel):
    """Use this model for validation of keys in list of menu items dictionary"""
    id: int  = Field(description= "Serial number for the list")
    name: str = Field(description= "Name of each item")
    price: float = Field(description= "Price of the item")

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

class GeneralResponse(BaseModel):
    """Consume this if no tool call required or the request and the response is very general or greeting messages"""
    model_response: str = Field(description= "Just a greeting message")