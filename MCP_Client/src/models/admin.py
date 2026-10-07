from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class CustomerDetails(BaseModel):
    customer_uuid: str
    name: str
    phone_number: str

class OrderItems(BaseModel):
    name: str
    price: float
    count: int

class GetOrdersResponse(BaseModel):
    order_uuid: str
    order_status: str
    total_amount: float
    ordered_at: datetime
    customer: CustomerDetails
    items: list[OrderItems]

class UpdateOrderStatusResponse(BaseModel):
    order_uuid: str
    order_status: str
    updated_at: Optional[datetime]

class ItemResponse(BaseModel):
    item_uuid: str
    name: str
    price: float
    created_at: datetime

class CreateItemRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)

class UpdateItemRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None
