from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from core.database import get_db
from models.chat import Chat
from models.user import User
from schemas.chat import ChatCreate, ChatResponse, MessageCreate, MessageResponse
from services.chat_service import create_chat, get_chat, create_message

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

@router.get("/test")
async def test_route():
    """
    A simple test route to verify that the chat router is included.
    """
    return JSONResponse({"message": "Chat router is working"})

@router.post("/", response_model=ChatResponse)
async def create_chat_route(chat_create: ChatCreate, request: Request, db: Session = Depends(get_db)):
    """
    Create a new chat using the first message. Returns the chat and a placeholder LLM response.
    """
    current_user = request.state.user
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    chat, llm_response = create_chat(db, current_user, chat_create.message)
    # Here, we return the chat object.
    # If you want to include the LLM response separately, you can return a dict:
    return chat

@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat_route(chat_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Retrieve a chat by its ID.
    """
    current_user = request.state.user
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    chat = get_chat(db, chat_id, current_user)
    return chat

@router.post("/message", response_model=MessageResponse)
async def create_message_route(message_create: MessageCreate, request: Request, db: Session = Depends(get_db)):
    """
    Create a new message in a chat. Returns the LLM-generated (assistant) message.
    """
    current_user: User = request.state.user
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    # Retrieve the chat ensuring it belongs to the current user
    chat = db.query(Chat).filter(Chat.id == message_create.chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    # Use the updated service to create both messages
    user_msg, assistant_msg = create_message(db, chat, message_create.message)
    return assistant_msg
