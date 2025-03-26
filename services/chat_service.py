from typing import Tuple
from sqlalchemy.orm import Session
from models.chat import Chat, Message
from models.user import User
from utils.chat import generate_chat_title, generate_llm_response

def create_chat(db: Session, user: User, message: str) -> Tuple[Chat, str]:
    """
    Create a new chat for the user, store the first message, and generate a placeholder LLM response.
    
    Returns:
        chat: The created Chat object.
        llm_text: The placeholder LLM response (extracted from the assistant message).
    """
    # Generate a chat title from the first message
    title = generate_chat_title(message)
    chat = Chat(
        title=title,
        user_id=user.id,
        context=[]  # Placeholder empty context; update as needed
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    
    # Create the user's message and automatically create an assistant message
    user_msg, assistant_msg = create_message(db, chat, message)
    
    return chat, assistant_msg.message

def get_chat(db: Session, chat_id: int, user: User) -> Chat:
    """
    Retrieve a chat by its ID and ensure it belongs to the user.
    """
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise Exception("Chat not found or unauthorized")
    return chat

def create_message(db: Session, chat: Chat, message: str) -> Tuple[Message, Message]:
    """
    Create a new message for a given chat:
      - Create the user's message.
      - Generate a placeholder LLM response and create an assistant message.
    
    Returns:
        A tuple of (user_message, assistant_message).
    """
    # Create the user's message
    user_msg = Message(
        chat_id=chat.id,
        sender="user",
        message=message
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)
    
    # Generate a placeholder LLM response
    llm_text = generate_llm_response(chat)
    
    # Create the assistant's message
    assistant_msg = Message(
        chat_id=chat.id,
        sender="assistant",
        message=llm_text
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    
    return user_msg, assistant_msg
