from fastapi import APIRouter, HTTPException, Depends  # Add Depends here
from typing import Optional 
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import chat_service
from app.services.auth_service import auth_service  # ADD THIS
from app.services.vector_service import vector_service  # ADD THIS
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()

security = HTTPBearer(auto_error=False)  # auto_error=False for backward compatibility

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Handle chat requests with optional authentication"""
    try:
        print(f"💬 Received chat request: {request.message[:50]}...")
        
        # Check if authenticated
        session_id = None
        username = None
        
        if credentials:
            # Try to get session info from token
            token = credentials.credentials
            payload = auth_service.verify_token(token)
            if payload:
                session_id = payload.get("session_id")
                username = payload.get("sub")
                print(f"👤 Authenticated user: {username}, Session: {session_id[:8] if session_id else 'None'}")
                
                # Add session info to request
                request.session_id = session_id
        else:
            print("👤 Anonymous user (no authentication)")
        
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
                detail="Le service de chat n'est pas prêt."
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

@router.get("/chat/context-info")
async def get_context_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get information about available document context"""
    try:
        if not credentials:
            return {
                "authenticated": False,
                "message": "Connectez-vous pour accéder aux documents personnels"
            }
        
        # Get session info
        token = credentials.credentials
        payload = auth_service.verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        session_id = payload.get("session_id")
        
        # Get document counts
        global_docs = len(set(
            chunk.document_id for chunk in vector_service.global_documents.values()
        ))
        
        personal_docs = 0
        if session_id in vector_service.session_documents:
            personal_docs = len(set(
                chunk.document_id 
                for chunk in vector_service.session_documents[session_id]['chunks'].values()
            ))
        
        return {
            "authenticated": True,
            "global_documents": global_docs,
            "personal_documents": personal_docs,
            "total_available": global_docs + personal_docs,
            "message": f"Vous avez accès à {global_docs} documents officiels et {personal_docs} documents personnels."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

@router.get("/chat/debug")
async def debug_session_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Debug endpoint to check session state and documents"""
    try:
        if not credentials:
            return {"error": "No credentials provided"}
        
        # Get session info
        token = credentials.credentials
        payload = auth_service.verify_token(token)
        
        if not payload:
            return {"error": "Invalid token"}
        
        session_id = payload.get("session_id")
        username = payload.get("sub")
        
        # Check what documents are available
        debug_info = {
            "authenticated": True,
            "username": username,
            "session_id": session_id,
            "session_id_short": session_id[:8] if session_id else None,
            "global_documents_count": len(vector_service.global_documents),
            "personal_documents_available": session_id in vector_service.session_documents if session_id else False,
            "personal_documents_count": 0,
            "all_sessions": list(vector_service.session_documents.keys())[:3]  # First 3 for debugging
        }
        
        if session_id and session_id in vector_service.session_documents:
            session_data = vector_service.session_documents[session_id]
            debug_info["personal_documents_count"] = len(session_data['chunks'])
            debug_info["session_expires_at"] = session_data['expires_at'].isoformat()
            
            # List some personal document names
            personal_doc_names = []
            for chunk in list(session_data['chunks'].values())[:3]:  # First 3
                filename = chunk.metadata.get('filename', 'Unknown')
                if filename not in personal_doc_names:
                    personal_doc_names.append(filename)
            debug_info["personal_document_names"] = personal_doc_names
        
        return debug_info
        
    except Exception as e:
        return {"error": str(e)}
