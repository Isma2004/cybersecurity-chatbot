from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import chat_service

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Handle chat requests"""
    try:
        print(f"💬 Received chat request: {request.message[:50]}...")
        
        if not chat_service.is_ready():
            raise HTTPException(
                status_code=503, 
                detail="Chat service is not ready. Please check model loading."
            )
        
        response = chat_service.chat(request)
        print(f"✅ Chat response generated successfully")
        return response
        
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/status")
async def get_chat_status():
    """Get chat service status"""
    try:
        return chat_service.get_model_status()
    except Exception as e:
        return {"error": str(e), "status": "error"}