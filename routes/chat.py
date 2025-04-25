from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from starlette.responses import StreamingResponse
import json

from core.database import get_db
from models.chat import Chat
from models.user import User
from schemas.chat import ChatCreate, ChatResponse, MessageCreate, MessageResponse
from services.chat_service import create_chat, get_chat, create_message, stream_message_response

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

@router.get("/test")
async def test_route():
    return JSONResponse({"message": "Chat router is working"})

@router.post("/", response_model=ChatResponse)
async def create_chat_route(chat_create: ChatCreate, request: Request, db: Session = Depends(get_db)):
    current_user = request.state.user
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    chat, llm_response = create_chat(db, current_user, chat_create.message)
    return chat

@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat_route(chat_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = request.state.user
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    chat = get_chat(db, chat_id, current_user)
    return chat

@router.post("/message", response_model=MessageResponse)
async def create_message_route(message_create: MessageCreate, request: Request, db: Session = Depends(get_db)):
    current_user: User = request.state.user
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    chat = db.query(Chat).filter(Chat.id == message_create.chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    user_msg, assistant_msg = create_message(db, chat, message_create.message)
    return assistant_msg


@router.post("/message/stream")
async def stream_message_route(message_create: MessageCreate, request: Request, db: Session = Depends(get_db)):
    current_user: User = request.state.user
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    chat = db.query(Chat).filter(Chat.id == message_create.chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    def event_generator():
        for chunk in stream_message_response(db, chat, message_create.message):
            if chunk == "[DONE]":
                break
            yield f"data: {chunk}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
