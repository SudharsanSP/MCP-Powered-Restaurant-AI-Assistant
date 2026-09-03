from sqlalchemy import Column, Integer, Enum, text, DateTime, String, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

# class Item(Base):
#     __tablename__ = "items"
#     item_id = Column(Integer, primary_key=True)
#     name = Column(String, nullable = False)
#     price = Column(Float,nullable= False)
#     is_active = Column(Boolean, default=True)
#     created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
#     created_by = Column(String, server_default=text("'ADMIN'"))
#     updated_at = Column(DateTime, nullable=True)
#     updated_by = Column(String, nullable= True)

# class OrderStatus(enum.Enum):
#     ordered = "ordered"
#     processing = "processing"
#     pending = "pending"
#     completed = "completed"

# class Order(Base):
#     __tablename__ = "orders"
#     order_id = Column(Integer, primary_key=True)
#     total_amount = Column(Float, nullable= False)
#     order_status = Column(Enum(OrderStatus), nullable=False,default=OrderStatus.ordered)
#     is_active = Column(Boolean, default=True)
#     created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
#     created_by = Column(String, server_default=text("'ADMIN'"))
#     updated_at = Column(DateTime, nullable=True)
#     updated_by = Column(String, nullable= True)


# class Order_Item(Base):
#     __tablename__ = "order_items"
#     order_item_id = Column(Integer, primary_key=True)
#     order_id = Column(Integer, ForeignKey("orders.order_id"))
#     item_id = Column(Integer, ForeignKey("items.item_id"))
#     item_count = Column(Integer, nullable= False)
#     is_active = Column(Boolean, default=True)
#     created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
#     created_by = Column(String, server_default=text("'ADMIN'"))
#     updated_at = Column(DateTime, nullable=True)
#     updated_by = Column(String, nullable= True)
#     #  relationship
#     item = relationship("Item", backref = "order_items")
#     order = relationship("Order", backref="order_items")

