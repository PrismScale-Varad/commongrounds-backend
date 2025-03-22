from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
from core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    active_token = Column(String, nullable=True)
    
    # Profile fields
    username = Column(String, nullable=True)
    profile_pic = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    interests = Column(ARRAY(String), nullable=True)
