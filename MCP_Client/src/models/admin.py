from pydantic import BaseModel
from datetime import datetime

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
