from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# Request schema for creating a new chat (using the first message)
class ChatCreate(BaseModel):
    message: str

# Response schema for a message
class MessageResponse(BaseModel):
    id: int
    chat_id: int
    sender: str
    message: str
    created_at: datetime

    class Config:
        orm_mode = True

# Response schema for a chat
class ChatResponse(BaseModel):
    id: int
    title: str
    user_id: int
    context: Optional[List[str]] = None
    # Expanded context: full user data for each user in context
    expanded_context: Optional[List] = []  
    messages: List[MessageResponse] = []

    class Config:
        orm_mode = True

# Request schema for creating a new message
class MessageCreate(BaseModel):
    chat_id: int
    message: str

# Schema for returning a placeholder LLM response
class LLMResponse(BaseModel):
    response: str
