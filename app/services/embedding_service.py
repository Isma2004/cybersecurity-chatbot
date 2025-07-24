# app/services/embedding_service.py
import requests
import numpy as np
import logging
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class CloudEmbeddingService:
    """Embedding service that uses Kaggle for all ML operations"""
    
    def __init__(self):
        self.kaggle_url = os.getenv("KAGGLE_API_URL", "").strip()
        self.kaggle_key = os.getenv("KAGGLE_API_KEY", "").strip()
        self.embedding_dimension = 768  # multilingual-e5-base dimension
        self.model_name = "kaggle-cloud"
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to Kaggle service"""
        if not self.kaggle_url or not self.kaggle_key:
            print("⚠️ Kaggle not configured - using simple fallback")
            self.kaggle_available = False
            return
        
        try:
            print(f"🔗 Testing Kaggle embedding service: {self.kaggle_url}")
            response = requests.get(
                f"{self.kaggle_url}/health",
                headers={"Authorization": f"Bearer {self.kaggle_key}"},
                timeout=10
            )
            
            if response.status_code == 200:
                health_data = response.json()
                models_loaded = health_data.get('models_loaded', {})
                
                if models_loaded.get('embeddings', False):
                    self.kaggle_available = True
                    print("✅ Kaggle embedding service connected and ready")
                    print(f"🧮 Embedding model: {health_data.get('models', {}).get('embeddings', 'unknown')}")
                else:
                    print("❌ Kaggle embedding model not loaded")
                    self.kaggle_available = False
            else:
                print(f"❌ Kaggle health check failed: {response.status_code}")
                self.kaggle_available = False
                
        except requests.exceptions.Timeout:
            print("⏰ Kaggle connection timeout - is your notebook running?")
            self.kaggle_available = False
        except requests.exceptions.ConnectionError:
            print("🔌 Can't connect to Kaggle - check your URL")
            self.kaggle_available = False
        except Exception as e:
            print(f"❌ Kaggle connection error: {e}")
            self.kaggle_available = False
    
    def _call_kaggle_embeddings(self, texts: List[str], is_query: bool = False) -> List[np.ndarray]:
        """Call Kaggle for embeddings"""
        try:
            payload = {
                "texts": texts,
                "is_query": is_query
            }
            
            response = requests.post(
                f"{self.kaggle_url}/embeddings",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.kaggle_key}"
                },
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                embeddings = result["embeddings"]
                return [np.array(emb, dtype=np.float32) for emb in embeddings]
            else:
                print(f"❌ Kaggle embedding error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Kaggle embedding call failed: {e}")
            return None
    
    def _simple_fallback(self, text: str) -> np.ndarray:
        """Simple fallback when Kaggle unavailable"""
        import hashlib
        
        # Create simple deterministic embedding
        text_lower = text.lower().strip()
        
        # Hash-based features
        text_hash = hashlib.md5(text_lower.encode()).hexdigest()
        vector = np.zeros(50, dtype=np.float32)
        
        # Convert hash to features
        for i, char in enumerate(text_hash[:25]):
            vector[i] = ord(char) / 255.0
        
        # Text statistics features
        vector[25] = min(len(text) / 1000.0, 1.0)  # Length
        vector[26] = min(len(text.split()) / 100.0, 1.0)  # Word count
        vector[27] = min(text.count('.') / 10.0, 1.0)  # Sentence count
        
        # Cybersecurity keyword features
        cyber_keywords = [
            'mot de passe', 'password', 'sécurité', 'incident', 'authentification',
            'phishing', 'firewall', 'données', 'iso', 'conformité', 'audit',
            'sauvegarde', 'réseau', 'formation', 'employé', 'politique',
            'chiffrement', 'vpn', 'antivirus', 'malware', 'backup'
        ]
        
        for i, keyword in enumerate(cyber_keywords[:20]):
            if keyword in text_lower:
                vector[28 + i] = 1.0
        
        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector
    
    def embed_text(self, text: str) -> np.ndarray:
        """Embed text using Kaggle or fallback"""
        if not text or not text.strip():
            return np.zeros(self.get_embedding_dimension(), dtype=np.float32)
        
        if self.kaggle_available:
            embeddings = self._call_kaggle_embeddings([text], is_query=False)
            if embeddings:
                return embeddings[0]
        
        # Fallback
        return self._simple_fallback(text)
    
    def embed_query(self, query: str) -> np.ndarray:
        """Embed query using Kaggle or fallback"""
        if not query or not query.strip():
            return np.zeros(self.get_embedding_dimension(), dtype=np.float32)
        
        if self.kaggle_available:
            embeddings = self._call_kaggle_embeddings([query], is_query=True)
            if embeddings:
                return embeddings[0]
        
        # Fallback
        return self._simple_fallback(query)
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return self.embedding_dimension if self.kaggle_available else 50
    
    def is_model_loaded(self) -> bool:
        """Always ready with fallback"""
        return True

# Global service
print("🚀 Creating cloud embedding service...")
embedding_service = CloudEmbeddingService()
print("✅ Cloud embedding service ready!")