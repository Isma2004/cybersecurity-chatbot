from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import chat_service

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Handle chat requests for French cybersecurity assistance"""
    try:
        print(f"💬 Received chat request: {request.message[:50]}...")
        
        # Validate request
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Le message ne peut pas être vide"
            )
        
        # Check if chat service is ready
        if not chat_service.is_ready():
            raise HTTPException(
                status_code=503, 
                detail="Le service de chat n'est pas prêt. Veuillez vérifier le chargement du modèle."
            )
        
        # Process the chat request
        response = chat_service.chat(request)
        
        print(f"✅ Chat response generated successfully")
        print(f"📊 Sources found: {len(response.sources)}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors du traitement de votre message: {str(e)}"
        )

@router.get("/chat/status")
async def get_chat_status():
    """Get chat service status and model information"""
    try:
        status = chat_service.get_model_status()
        return {
            **status,
            "endpoints": {
                "chat": "/api/chat",
                "status": "/api/chat/status",
                "suggestions": "/api/chat/suggestions"
            }
        }
    except Exception as e:
        return {
            "error": str(e), 
            "status": "error",
            "message": "Erreur lors de la récupération du statut du service de chat"
        }

@router.get("/chat/suggestions")
async def get_chat_suggestions(count: int = 6):
    """Get suggested questions for French cybersecurity topics"""
    
    suggestions = [
        "Quelles sont les meilleures pratiques pour les mots de passe?",
        "Comment se protéger contre le phishing?",
        "Qu'est-ce que l'authentification à deux facteurs?",
        "Comment sécuriser les données sensibles en entreprise?",
        "Quelles sont les exigences de la norme ISO 27001?",
        "Comment réagir en cas de violation de données?",
        "Quels sont les principaux types de cyberattaques?",
        "Comment mettre en place une politique de sécurité informatique?",
        "Qu'est-ce qu'un plan de continuité d'activité?",
        "Comment sensibiliser les employés à la cybersécurité?"
    ]
    
    return {
        "suggestions": suggestions[:count],
        "total_available": len(suggestions),
        "language": "french",
        "domain": "cybersecurity"
    }

@router.post("/chat/reset")
async def reset_conversation():
    """Reset the current conversation context"""
    try:
        # For now, this is a placeholder since our chat service is stateless
        # In the future, this could clear conversation history if we implement it
        return {
            "message": "Conversation réinitialisée avec succès",
            "status": "reset_complete",
            "timestamp": "now"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la réinitialisation: {str(e)}"
        )