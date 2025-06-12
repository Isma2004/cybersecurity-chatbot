# app/services/chat_service.py
"""
OpenAI-based chat service for French cybersecurity RAG
Zero memory usage - runs entirely on OpenAI servers
"""
import os
import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not installed. Run: pip install openai")

from app.models.schemas import ChatRequest, ChatResponse, SourceReference
from app.services.vector_service import vector_service
from app.utils.config import settings, FRENCH_SYSTEM_PROMPTS

logger = logging.getLogger(__name__)

class FrenchChatService:
    """French chat service using OpenAI API - NO LOCAL MEMORY USAGE!"""
    
    def __init__(self):
        self.client = None
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.pipeline = None  # For compatibility
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize OpenAI client or fallback"""
        # Check if we should use OpenAI
        use_openai = os.getenv("USE_OPENAI", "true").lower() == "true"
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        
        if use_openai and OPENAI_AVAILABLE and api_key and api_key != "sk-your-api-key-here":
            try:
                self.client = OpenAI(api_key=api_key)
                print(f"✅ OpenAI initialized with {self.model_name}")
                print("💾 Memory usage: 0 MB (cloud-based)")
                self._test_connection()
            except Exception as e:
                print(f"❌ OpenAI initialization failed: {e}")
                self._setup_fallback()
        else:
            if not OPENAI_AVAILABLE:
                print("❌ OpenAI package not installed")
            elif not api_key or api_key == "sk-your-api-key-here":
                print("❌ OpenAI API key not configured in .env file")
                print("📝 Please add your OpenAI API key to the .env file:")
                print("   OPENAI_API_KEY=sk-your-actual-key-here")
            self._setup_fallback()
    
    def _test_connection(self):
        """Test OpenAI connection"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            print("✅ OpenAI connection verified")
        except Exception as e:
            print(f"⚠️ OpenAI test failed: {e}")
            self._setup_fallback()
    
    def _setup_fallback(self):
        """Setup fallback when OpenAI is not available"""
        print("📝 Using simple extraction from documents (no AI model)")
        self.client = None
        # Set pipeline to None for compatibility with existing code
        self.pipeline = None
    
    def _construct_openai_messages(self, context_chunks: List[SourceReference], question: str) -> List[Dict[str, str]]:
        """Construct messages for OpenAI chat"""
        # System prompt in French
        system_content = """Tu es un assistant expert en cybersécurité et conformité ISO 27001.

Règles importantes:
1. Réponds TOUJOURS en français professionnel
2. Base tes réponses UNIQUEMENT sur le contexte fourni
3. Si l'information n'est pas dans le contexte, dis-le clairement
4. Cite le document source quand c'est pertinent
5. Sois précis et concis"""
        
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(context_chunks[:3]):  # Top 3 chunks
            context_parts.append(f"[Document: {chunk.document_id}]\n{chunk.chunk_content}")
        
        context_text = "\n\n".join(context_parts)
        
        # User message
        user_content = f"""Contexte des documents de cybersécurité:
{context_text}

Question: {question}

Réponds en te basant uniquement sur le contexte ci-dessus."""
        
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]
    
    def _generate_openai_response(self, messages: List[Dict], max_tokens: int) -> str:
        """Generate response using OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1,
                top_p=0.95
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return f"Erreur OpenAI: {str(e)}"
    
    def _extract_from_chunks(self, chunks: List[SourceReference], question: str) -> str:
        """Extract relevant information from chunks without AI"""
        if not chunks:
            return "Aucun document pertinent trouvé."
        
        question_lower = question.lower()
        response_parts = ["D'après les documents de cybersécurité:\n"]
        
        # Extract relevant sentences based on keywords
        for chunk in chunks[:2]:
            content = chunk.chunk_content
            sentences = content.split('. ')
            relevant = []
            
            # Password requirements
            if "mot de passe" in question_lower:
                for s in sentences:
                    if any(word in s.lower() for word in ["mot de passe", "caractère", "minimum", "renouvellement"]):
                        relevant.append(s.strip())
            
            # Incident reporting
            elif "incident" in question_lower:
                for s in sentences:
                    if any(word in s.lower() for word in ["incident", "signaler", "soc", "heure", "minute"]):
                        relevant.append(s.strip())
            
            # MFA/Authentication
            elif "authentification" in question_lower or "mfa" in question_lower:
                for s in sentences:
                    if any(word in s.lower() for word in ["authentification", "mfa", "multi-facteur", "obligatoire"]):
                        relevant.append(s.strip())
            
            # Add relevant sentences
            if relevant:
                for r in relevant[:2]:
                    if r and not r.endswith('.'):
                        r += '.'
                    response_parts.append(f"\n• {r}")
        
        # If no specific match, show first chunk
        if len(response_parts) == 1:
            response_parts.append(f"\n{chunks[0].chunk_content[:200]}...")
        
        response_parts.append(f"\n\n(Source: {len(chunks)} document(s) analysé(s))")
        return "".join(response_parts)
    
    def chat(self, request: ChatRequest) -> ChatResponse:
        """Main chat method - processes user query and returns French response"""
        start_time = time.time()
        
        try:
            print(f"💬 Processing: '{request.message[:50]}...'")
            
            # Step 1: Retrieve relevant chunks using FAISS
            relevant_chunks = vector_service.search_similar_chunks(
                query=request.message,
                top_k=settings.top_k_retrieval
            )
            
            if not relevant_chunks:
                return ChatResponse(
                    response="Je n'ai trouvé aucun document pertinent. Veuillez vérifier que des documents ont été téléchargés.",
                    sources=[],
                    processing_time=time.time() - start_time
                )
            
            print(f"🔍 Found {len(relevant_chunks)} relevant chunks")
            
            # Step 2: Generate response
            if self.client:
                # Use OpenAI
                messages = self._construct_openai_messages(relevant_chunks, request.message)
                response_text = self._generate_openai_response(
                    messages,
                    max_tokens=request.max_tokens or settings.max_tokens_generation
                )
            else:
                # Fallback to extraction
                response_text = self._extract_from_chunks(relevant_chunks, request.message)
            
            # Step 3: Create response
            processing_time = time.time() - start_time
            
            return ChatResponse(
                response=response_text,
                sources=relevant_chunks,
                processing_time=processing_time,
                tokens_used=len(response_text.split())
            )
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return ChatResponse(
                response=f"Erreur: {str(e)}",
                sources=[],
                processing_time=time.time() - start_time
            )
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get the status of the chat service"""
        if self.client:
            return {
                "model_loaded": True,
                "model_name": self.model_name,
                "device": "OpenAI Cloud",
                "status": "ready",
                "memory_usage": "0 MB (cloud-based)"
            }
        else:
            return {
                "model_loaded": False,
                "model_name": "extraction-only",
                "device": "local",
                "status": "fallback",
                "memory_usage": "0 MB"
            }
    
    def is_ready(self) -> bool:
        """Check if the chat service is ready"""
        return True  # Always ready with fallback

# Global chat service instance
print("🚀 Initializing chat service...")
chat_service = FrenchChatService()
print("✅ Chat service ready!")

__all__ = ['chat_service']
