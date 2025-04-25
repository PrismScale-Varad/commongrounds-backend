from typing import Tuple, List, Generator
from sqlalchemy.orm import Session
from models.chat import Chat, Message
from models.user import User
from utils.chat import generate_chat_title, generate_llm_response, stream_llm_response
from services.auth_service import generate_embedding, search_users_by_embedding
from core.config import logger


def generate_chat_title_after_messages(db: Session, chat: Chat) -> None:
    user_messages = db.query(Message).filter(Message.chat_id == chat.id, Message.sender == 'user').order_by(Message.created_at).all()
    if len(user_messages) >= 5:
        messages_text = "\n".join([msg.message for msg in user_messages])
        title = generate_chat_title(messages_text)
        if title:
            chat.title = title
            db.commit()
            db.refresh(chat)


def create_chat(db: Session, user: User, message: str) -> Tuple[Chat, str]:
    default_title = "New Chat"
    chat = Chat(
        title=default_title,
        user_id=user.id,
        context=[]
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    user_msg, assistant_msg = create_message(db, chat, message)
    generate_chat_title_after_messages(db, chat)
    return chat, assistant_msg.message


def get_chat(db: Session, chat_id: int, user: User) -> Chat:
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise Exception("Chat not found or unauthorized")
    generate_chat_title_after_messages(db, chat)
    return chat


def create_message(db: Session, chat: Chat, message: str) -> Tuple[Message, Message]:
    user_msg = Message(
        chat_id=chat.id,
        sender="user",
        message=message
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)
    llm_text = generate_llm_response(chat)
    assistant_msg = Message(
        chat_id=chat.id,
        sender="assistant",
        message=llm_text
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    return user_msg, assistant_msg


def stream_message_response(db: Session, chat: Chat, message: str) -> Generator[str, None, None]:
    user_msg = Message(
        chat_id=chat.id,
        sender="user",
        message=message
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    assistant_msg = None
    collected_text = ""

    for chunk in stream_llm_response(chat, message):
        collected_text += chunk

        # Create assistant message if not present, else update
        if assistant_msg is None:
            assistant_msg = Message(
                chat_id=chat.id,
                sender="assistant",
                message=collected_text
            )
            db.add(assistant_msg)
        else:
            assistant_msg.message = collected_text

        db.commit()
        db.refresh(assistant_msg)

        yield chunk

    # Yield a terminator indicator
    yield "[DONE]"
