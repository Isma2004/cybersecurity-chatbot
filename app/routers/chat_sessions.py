# app/routers/chat_sessions.py
from fastapi import APIRouter, HTTPException
from typing import List

from app.models.schemas import (
    ChatSession, ChatMessageRequest, CreateChatRequest, 
    ChatSessionResponse, ChatListResponse, ChatResponse
)
from app.services.chat_session_service import chat_session_service
from app.services.chat_service import chat_service
from app.services.vector_service import vector_service

router = APIRouter()

@router.get("/chats", response_model=ChatListResponse)
async def get_chat_sessions():
    """Get all chat sessions"""
    try:
        sessions = chat_session_service.get_sessions()
        return ChatListResponse(
            sessions=sessions,
            total=len(sessions)
        )
    except Exception as e:
        print(f"❌ Error getting chat sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chats", response_model=ChatSession)
async def create_chat_session(request: CreateChatRequest):
    """Create a new chat session"""
    try:
        session = chat_session_service.create_session(request.title)
        return session
    except Exception as e:
        print(f"❌ Error creating chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chats/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(session_id: str):
    """Get a specific chat session with messages"""
    try:
        session_data = chat_session_service.get_session_with_messages(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return ChatSessionResponse(
            session=session_data["session"],
            messages=session_data["messages"]
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chats/{session_id}/messages", response_model=ChatResponse)
async def send_message_to_session(session_id: str, request: ChatMessageRequest):
    """Send a message to a specific chat session"""
    try:
        # Verify session exists
        session_data = chat_session_service.get_session_with_messages(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Add user message
        user_message = chat_session_service.add_message(
            session_id=session_id,
            message_type="user",
            content=request.message
        )
        
        # Get AI response using existing chat service
        from app.models.schemas import ChatRequest
        chat_request = ChatRequest(
            message=request.message,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        ai_response = chat_service.chat(chat_request)
        
        # Add AI message
        ai_message = chat_session_service.add_message(
            session_id=session_id,
            message_type="assistant",
            content=ai_response.response,
            sources=ai_response.sources,
            tokens_used=ai_response.tokens_used,
            processing_time=ai_response.processing_time
        )
        
        return ai_response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error sending message to session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chats/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session"""
    try:
        success = chat_session_service.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/chats/{session_id}/title")
async def update_chat_title(session_id: str, title: str):
    """Update chat session title"""
    try:
        success = chat_session_service.update_session_title(session_id, title)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Title updated successfully"}
    except Exception as e:
        print(f"❌ Error updating chat title: {e}")
        raise HTTPException(status_code=500, detail=str(e))