import uuid

from sqlalchemy import Column, Integer, Enum, text, DateTime, String, ForeignKey, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()
class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    user_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False, default="admin", server_default="admin")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    created_by = Column(String, server_default=text("'ADMIN'"))
    updated_at = Column(DateTime, nullable=True)
    updated_by = Column(String, nullable= True)

class Customer(Base):
    __tablename__ = "customers"
    customer_id = Column(Integer, primary_key=True)
    customer_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False, default="user", server_default="user")
    refresh_token = Column(String, nullable=True)
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    created_by = Column(String, server_default=text("'ADMIN'"))
    updated_at = Column(DateTime, nullable=True)
    updated_by = Column(String, nullable= True)

class Item(Base):
    __tablename__ = "items"
    item_id = Column(Integer, primary_key=True)
    item_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4)
    name = Column(String, nullable = False)
    price = Column(Float,nullable= False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    created_by = Column(String, server_default=text("'ADMIN'"))
    updated_at = Column(DateTime, nullable=True)
    updated_by = Column(String, nullable= True)

class OrderStatus(enum.Enum):
    ordered = "ordered"
    processing = "processing"
    pending = "pending"
    completed = "completed"

class Order(Base):
    __tablename__ = "orders"
    order_id = Column(Integer, primary_key=True)
    order_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    total_amount = Column(Float, nullable= False)
    order_status = Column(Enum(OrderStatus), nullable=False,default=OrderStatus.ordered)
    is_active = Column(Boolean, server_default=text("true"))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    created_by = Column(String, server_default=text("'ADMIN'"))
    updated_at = Column(DateTime, nullable=True)
    updated_by = Column(String, nullable= True)
    #  relationship
    customer = relationship("Customer", backref="orders")


class Order_Item(Base):
    __tablename__ = "order_items"
    order_item_id = Column(Integer, primary_key=True)
    order_item_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    item_id = Column(Integer, ForeignKey("items.item_id"))
    item_count = Column(Integer, nullable= False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    created_by = Column(String, server_default=text("'ADMIN'"))
    updated_at = Column(DateTime, nullable=True)
    updated_by = Column(String, nullable= True)
    #  relationship
    item = relationship("Item", backref = "order_items")
    order = relationship("Order", backref="order_items")
