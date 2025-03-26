from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from core.database import Base, SessionLocal
from models.user import User

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    
    # The single user who is having the chat (e.g., with an LLM assistant)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref="chats")
    
    # Context: an array of user IDs (as strings or integers) representing additional users
    context = Column(ARRAY(String), nullable=True)
    
    # One-to-many relationship with messages
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

    @property
    def expanded_context(self):
        """
        Returns a list of full user objects for each user ID in the context array.
        """
        if not self.context:
            return []
        session = SessionLocal()
        try:
            # Assuming context stores user IDs as strings that can be converted to int
            user_ids = [int(uid) for uid in self.context]
            users = session.query(User).filter(User.id.in_(user_ids)).all()
        finally:
            session.close()
        return users

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    chat = relationship("Chat", back_populates="messages")
    
    # Sender is a simple field: either "user" or "assistant"
    sender = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
