from typing import Tuple, List
from sqlalchemy.orm import Session
from models.chat import Chat, Message
from models.user import User
from utils.chat import generate_chat_title, generate_llm_response
from services.auth_service import generate_embedding, search_users_by_embedding
from core.config import logger


# New helper function to generate chat title after 5 user messages

def generate_chat_title_after_messages(db: Session, chat: Chat) -> None:
    """
    Generate and update chat title using LLM after at least 5 user messages.
    """
    user_messages = db.query(Message).filter(Message.chat_id == chat.id, Message.sender == 'user').order_by(Message.created_at).all()
    if len(user_messages) >= 5:
        messages_text = "\n".join([msg.message for msg in user_messages])
        # Use LLM to generate a succinct title
        title = generate_chat_title(messages_text)
        if title:
            chat.title = title
            db.commit()
            db.refresh(chat)



def create_chat(db: Session, user: User, message: str) -> Tuple[Chat, str]:
    """
    Create a new chat for the user, store the first message, and generate a placeholder LLM response.
    
    Returns:
        chat: The created Chat object.
        llm_text: The placeholder LLM response (extracted from the assistant message).
    """
    # Use a generic default title initially
    default_title = "New Chat"
    chat = Chat(
        title=default_title,
        user_id=user.id,
        context=[]  # Placeholder empty context; update as needed
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    
    # Create the user's message and automatically create an assistant message
    user_msg, assistant_msg = create_message(db, chat, message)

    # After the message creation, check if we need to update title (if >= 5 messages, update title)
    generate_chat_title_after_messages(db, chat)
    
    return chat, assistant_msg.message


def get_chat(db: Session, chat_id: int, user: User) -> Chat:
    """
    Retrieve a chat by its ID and ensure it belongs to the user.
    """
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise Exception("Chat not found or unauthorized")

    # Update title if enough messages
    generate_chat_title_after_messages(db, chat)

    return chat


# The rest of the code remains unchanged

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


def user_search_tool(db: Session, chat: Chat, query: str) -> Message:
    """
    This function allows the LLM to search for users by a query string,
    uses embeddings similarity search internally,
    formats the results excluding profile_pic and saves the results as a 'tool' message in the chat.

    Returns:
        The saved Message instance representing the tool's output.
    """
    embedding = generate_embedding(query)
    if not embedding:
        raise ValueError("Failed to generate embedding for the query")
    
    users = search_users_by_embedding(db, embedding, top_n=5)
    
    if not users:
        message_content = "No matching users found."
    else:
        message_lines = ["User search results:"]
        for user in users:
            # Compose user info excluding profile_pic
            line = f"- ID: {user.id}, Username: {user.username or 'N/A'}, Email: {user.email}, Bio: {user.bio or 'N/A'}, Profession: {user.profession or 'N/A'}"
            message_lines.append(line)
        message_content = "\n".join(message_lines)

    # Save this tool response as a message with sender="tool" to be compatible with LLM message history
    tool_msg = Message(
        chat_id=chat.id,
        sender="tool",
        message=message_content
    )
    db.add(tool_msg)
    db.commit()
    db.refresh(tool_msg)

    logger.info(f"Saved user search tool message in chat {chat.id}")

    return tool_msg
