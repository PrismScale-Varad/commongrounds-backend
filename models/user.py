from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
from core.database import Base

MAX_WORDS = 500

def count_words(text: str) -> int:
    if not text:
        return 0
    return len(text.split())

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
    bio = Column(Text, nullable=True)  # User biography, max 500 words
    profession = Column(Text, nullable=True)  # User profession description, max 500 words
    oauth_accounts = relationship("OAuth", back_populates="user")

    @validates('bio')
    def validate_bio(self, key, value):
        if value and count_words(value) > MAX_WORDS:
            raise ValueError(f"Bio exceeds maximum word limit of {MAX_WORDS}.")
        return value

    @validates('profession')
    def validate_profession(self, key, value):
        if value and count_words(value) > MAX_WORDS:
            raise ValueError(f"Profession exceeds maximum word limit of {MAX_WORDS}.")
        return value
