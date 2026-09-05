from sqlalchemy import Column, Integer, Enum, text, DateTime, String, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
Base = declarative_base()