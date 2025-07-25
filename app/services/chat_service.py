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
        """Main chat method with multi-tenant support"""
        start_time = time.time()
        
        try:
            query = request.message
            session_id = getattr(request, 'session_id', None)
            include_global = getattr(request, 'include_global', True)
            include_personal = getattr(request, 'include_personal', True)
            
            print(f"💬 Processing: '{query[:50]}...'")
            if session_id:
                print(f"   Session: {session_id[:8]}")
                print(f"   Include global: {include_global}, Include personal: {include_personal}")
            
            # Check if this is actually a question or just a greeting/simple message
            if not self._is_question_or_query(query):
                print("👋 Detected greeting/simple message - responding politely")
                polite_response = self._generate_polite_response(query)
                return ChatResponse(
                    response=polite_response,
                    sources=[],
                    processing_time=time.time() - start_time,
                    tokens_used=0
                )
            
            print("❓ Detected question/query - searching documents")
            
            # Get relevant chunks with session context
            relevant_chunks = vector_service.search_similar_chunks(
                query=query,
                top_k=5 if session_id else 3,  # Get more chunks when searching multiple sources
                session_id=session_id,
                include_global=include_global,
                include_personal=include_personal
            )
            
            if not relevant_chunks:
                return ChatResponse(
                    response="Je n'ai pas trouvé de documents pertinents pour répondre à votre question. Pouvez-vous reformuler ou être plus spécifique sur le sujet de cybersécurité qui vous intéresse ?",
                    sources=[],
                    processing_time=time.time() - start_time
                )
            
            print(f"🔍 Found {len(relevant_chunks)} relevant chunks")
            
            # Generate response
            if self.kaggle_available:
                print("🎮 Using Kaggle chat service")
                
                # Build context with source indicators
                context_parts = []
                for chunk in relevant_chunks[:3]:
                    # Check if document name has source type
                    if "[GLOBAL]" in chunk.document_name or "[PERSONAL]" in chunk.document_name:
                        context_parts.append(f"{chunk.document_name}\n{chunk.chunk_content}")
                    else:
                        context_parts.append(f"Document: {chunk.document_name}\n{chunk.chunk_content}")
                
                context = "\n\n".join(context_parts)
                
                # Call Kaggle chat API
                try:
                    payload = {
                        "context": context[:2500],
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
                        response_text = self._generate_enhanced_fallback(relevant_chunks, query)
                        tokens_used = 0
                        
                except Exception as e:
                    print(f"❌ Kaggle API call failed: {e}")
                    response_text = self._generate_enhanced_fallback(relevant_chunks, query)
                    tokens_used = 0
            else:
                print("📝 Using local fallback")
                response_text = self._generate_enhanced_fallback(relevant_chunks, query)
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

    def _generate_enhanced_fallback(self, chunks: List[SourceReference], question: str) -> str:
        """Enhanced fallback with source type indication"""
        if not chunks:
            return "Service cloud indisponible et aucun document pertinent trouvé."
        
        response_parts = ["🤖 Réponse basée sur l'analyse locale:\n"]
        
        # Group chunks by source type
        global_chunks = [c for c in chunks if "[GLOBAL]" in c.document_name]
        personal_chunks = [c for c in chunks if "[PERSONAL]" in c.document_name]
        regular_chunks = [c for c in chunks if "[GLOBAL]" not in c.document_name and "[PERSONAL]" not in c.document_name]
        
        # Add content from global documents first
        if global_chunks:
            response_parts.append("\n📚 D'après les documents officiels:")
            for chunk in global_chunks[:2]:
                doc_name = chunk.document_name.replace("[GLOBAL] ", "")
                content_preview = chunk.chunk_content[:300]
                if len(chunk.chunk_content) > 300:
                    content_preview += "..."
                response_parts.append(f"\n• {doc_name}: {content_preview}")
        
        # Add content from personal documents
        if personal_chunks:
            response_parts.append("\n\n📄 D'après vos documents personnels:")
            for chunk in personal_chunks[:1]:
                doc_name = chunk.document_name.replace("[PERSONAL] ", "")
                content_preview = chunk.chunk_content[:200]
                if len(chunk.chunk_content) > 200:
                    content_preview += "..."
                response_parts.append(f"\n• {doc_name}: {content_preview}")
        
        # Add regular chunks (backward compatibility)
        if regular_chunks and not global_chunks and not personal_chunks:
            # Fallback to original behavior
            return self._generate_fallback_response(regular_chunks, question)
        
        return "".join(response_parts)
    
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
    
    def _is_question_or_query(self, message: str) -> bool:
        """Detect if the message is actually a question or query that requires document search"""
        message_lower = message.lower().strip()
        
        # Simple greetings and polite expressions (no document search needed)
        simple_greetings = [
            "Bonjour","bonjour", "bonsoir", "salut", "hello", "hi", "hey",
            "merci", "au revoir", "à bientôt", "bonne journée",
            "comment allez-vous", "comment ça va", "ça va", "cava?", "cava",
            "merci beaucoup", "d'accord", "ok", "oui", "non"
        ]
        
        # If the message is just a simple greeting
        if any(greeting in message_lower for greeting in simple_greetings) and len(message.split()) <= 3:
            return False
        
        # Question indicators (should trigger document search)
        question_indicators = [
            # Question words
            "comment", "pourquoi", "qu'est-ce", "quelle", "quel", "quels", "quelles",
            "qui", "où", "quand", "combien", "que faire", "how", "what", "why", "where",
            
            # Question patterns
            "?", "peux-tu", "pouvez-vous", "peux tu", "pouvez vous",
            "dis-moi", "expliquer", "expliquez", "aide", "aidez",
            "recommandation", "conseil", "procédure", "politique",
            
            # Security/IT terms that likely indicate real questions
            "sécurité", "cybersécurité", "mot de passe", "authentification",
            "iso", "rgpd", "incident", "malware", "phishing", "firewall",
            "sauvegarde", "chiffrement", "vulnérabilité", "audit"
        ]
        
        # If message contains question indicators, it's probably a real question
        return any(indicator in message_lower for indicator in question_indicators)
    
    def _generate_polite_response(self, message: str) -> str:
        """Generate a polite response for greetings and simple messages"""
        message_lower = message.lower().strip()
        
        if any(greeting in message_lower for greeting in ["bonjour", "hello", "salut", "hi"]):
            return """Bonjour ! 👋 
            
Je suis l'Assistant DocuSense de Crédit Agricole du Maroc, votre assistant intelligent spécialisé en cybersécurité.

Je suis là pour vous aider avec :
• Les politiques de sécurité informatique
• Les procédures RGPD et protection des données  
• Les bonnes pratiques de cybersécurité
• Les normes ISO 27001
• La gestion des incidents de sécurité

N'hésitez pas à me poser vos questions sur la cybersécurité ! 🔐"""

        elif any(thanks in message_lower for thanks in ["merci", "thank"]):
            return "De rien ! 😊 Je suis là pour vous aider avec vos questions de cybersécurité. N'hésitez pas si vous avez d'autres questions !"
        
        elif any(goodbye in message_lower for goodbye in ["au revoir", "à bientôt", "bye"]):
            return "Au revoir ! À bientôt pour d'autres questions sur la cybersécurité. Bonne journée ! 👋"
        
        elif any(how in message_lower for how in ["comment ça va", "comment allez-vous", "ça va", "cava?", "cava"]):
            return "Je vais bien, merci ! 😊 Je suis prêt à répondre à vos questions sur la cybersécurité. Comment puis-je vous aider aujourd'hui ?"
        
        else:
            return """Bonjour ! Je suis votre assistant cybersécurité DocuSense. 
            
Pour mieux vous aider, pouvez-vous me poser une question spécifique sur :
• La sécurité informatique
• Les politiques et procédures
• La protection des données
• La gestion des incidents
• Les bonnes pratiques

Que souhaitez-vous savoir ? 🤔"""

# Global service
print("🚀 Initializing full cloud chat service...")
chat_service = FullCloudChatService()
print("✅ Chat service ready!")

__all__ = ['chat_service']
