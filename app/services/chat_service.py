# app/services/chat_service.py
import requests
import time
import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

from app.models.schemas import ChatRequest, ChatResponse, SourceReference
from app.services.vector_service import vector_service

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class FullCloudChatService:
    """Chat service using Kaggle for both embeddings and LLM"""
    
    def __init__(self):
        self.kaggle_url = os.getenv("KAGGLE_API_URL", "").strip()
        self.kaggle_key = os.getenv("KAGGLE_API_KEY", "").strip()
        self.model_name = "Mistral-7B-Instruct-v0.3"
        self._test_connection()
    
    def _test_connection(self):
        """Test Kaggle connection"""
        if not self.kaggle_url or not self.kaggle_key:
            print("⚠️ Kaggle not configured")
            self.kaggle_available = False
            return
        
        try:
            print(f"🔗 Testing Kaggle chat service: {self.kaggle_url}")
            response = requests.get(
                f"{self.kaggle_url}/health",
                headers={"Authorization": f"Bearer {self.kaggle_key}"},
                timeout=10
            )
            
            if response.status_code == 200:
                health_data = response.json()
                models_loaded = health_data.get('models_loaded', {})
                
                if models_loaded.get('mistral', False):
                    self.kaggle_available = True
                    print("✅ Kaggle chat service connected and ready")
                    print(f"🤖 Chat model: {health_data.get('models', {}).get('chat', 'unknown')}")
                else:
                    print("❌ Kaggle chat model not loaded")
                    self.kaggle_available = False
            else:
                print(f"❌ Kaggle health check failed: {response.status_code}")
                self.kaggle_available = False
                
        except Exception as e:
            print(f"❌ Kaggle connection error: {e}")
            self.kaggle_available = False
    
    def _generate_fallback_response(self, chunks: List[SourceReference], question: str) -> str:
        """Intelligent fallback when Kaggle unavailable"""
        if not chunks:
            return "Service cloud indisponible et aucun document pertinent trouvé."
        
        question_lower = question.lower()
        
        # Enhanced keyword matching
        cyber_keywords = {
            "mot de passe": ["mot de passe", "password", "caractère", "minimum", "complexité"],
            "incident": ["incident", "signaler", "soc", "réponse", "temps"],
            "authentification": ["authentification", "mfa", "multi-facteur", "2fa"],
            "phishing": ["phishing", "hameçonnage", "email", "malveillant"],
            "iso": ["iso", "27001", "norme", "certification", "conformité"],
            "données": ["données", "confidentialité", "rgpd", "protection"],
            "formation": ["formation", "sensibilisation", "employé", "training"]
        }
        
        # Find relevant topic
        best_topic = None
        max_score = 0
        
        for topic, keywords in cyber_keywords.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            if score > max_score:
                max_score = score
                best_topic = topic
        
        response_parts = ["🤖 Service cloud indisponible - Réponse basée sur l'analyse locale:\n"]
        
        # Extract relevant content
        found_content = False
        for chunk in chunks[:2]:
            content = chunk.chunk_content
            
            if best_topic and max_score > 0:
                keywords = cyber_keywords[best_topic]
                sentences = content.split('. ')
                
                for sentence in sentences:
                    if any(keyword in sentence.lower() for keyword in keywords):
                        response_parts.append(f"\n• {sentence.strip()}.")
                        found_content = True
                        break
        
        # If no specific match, show most relevant chunk
        if not found_content:
            best_chunk = chunks[0]
            preview = best_chunk.chunk_content[:400]
            if len(best_chunk.chunk_content) > 400:
                preview += "..."
            response_parts.append(f"\n{preview}")
        
        # Add sources
        sources = list(set(chunk.document_name for chunk in chunks[:3]))
        response_parts.append(f"\n\n📄 Sources: {', '.join(sources)}")
        
        return "".join(response_parts)
    
    def chat(self, request: ChatRequest) -> ChatResponse:
        """Main chat method using Kaggle"""
        start_time = time.time()
        
        try:
            query = request.message
            print(f"💬 Processing: '{query[:50]}...'")
            
            # Get relevant chunks using cloud embeddings
            relevant_chunks = vector_service.search_similar_chunks(query, top_k=3)
            
            if not relevant_chunks:
                return ChatResponse(
                    response="Aucun document pertinent trouvé. Veuillez vérifier que des documents ont été téléchargés.",
                    sources=[],
                    processing_time=time.time() - start_time
                )
            
            print(f"🔍 Found {len(relevant_chunks)} relevant chunks")
            
            # Generate response
            if self.kaggle_available:
                print("🎮 Using Kaggle chat service")
                
                # Build context for Kaggle
                context_parts = []
                for chunk in relevant_chunks[:3]:
                    context_parts.append(f"Document: {chunk.document_name}\n{chunk.chunk_content}")
                
                context = "\n\n".join(context_parts)
                
                # Call Kaggle chat API
                try:
                    payload = {
                        "context": context[:2500],  # Limit context size
                        "question": query,
                        "max_tokens": request.max_tokens or 512
                    }
                    
                    response = requests.post(
                        f"{self.kaggle_url}/chat",
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {self.kaggle_key}"
                        },
                        json=payload,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        response_text = result["response"]
                        tokens_used = result.get("tokens_used", 0)
                    else:
                        print(f"❌ Kaggle API error: {response.status_code}")
                        response_text = self._generate_fallback_response(relevant_chunks, query)
                        tokens_used = 0
                        
                except Exception as e:
                    print(f"❌ Kaggle API call failed: {e}")
                    response_text = self._generate_fallback_response(relevant_chunks, query)
                    tokens_used = 0
            else:
                print("📝 Using local fallback")
                response_text = self._generate_fallback_response(relevant_chunks, query)
                tokens_used = 0
            
            processing_time = time.time() - start_time
            
            return ChatResponse(
                response=response_text,
                sources=relevant_chunks,
                processing_time=processing_time,
                tokens_used=tokens_used
            )
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return ChatResponse(
                response=f"Erreur technique: {str(e)}",
                sources=[],
                processing_time=time.time() - start_time
            )
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "model_loaded": True,
            "model_name": self.model_name if self.kaggle_available else "local-fallback",
            "active_backend": "kaggle" if self.kaggle_available else "fallback",
            "status": "ready",
            "kaggle_connected": self.kaggle_available,
            "kaggle_url": self.kaggle_url if self.kaggle_url else "Not configured",
            "memory_usage": "0 MB (cloud-based)" if self.kaggle_available else "0 MB (local)"
        }
    
    def is_ready(self) -> bool:
        """Always ready with fallback"""
        return True

# Global service
print("🚀 Initializing full cloud chat service...")
chat_service = FullCloudChatService()
print("✅ Chat service ready!")

__all__ = ['chat_service']