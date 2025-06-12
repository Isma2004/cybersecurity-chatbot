import logging
import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer
import torch
from app.utils.config import settings

logger = logging.getLogger(__name__)

class FrenchEmbeddingService:
    """Service for generating French-optimized embeddings"""
    
    def __init__(self):
        self.model = None
        self.model_name = settings.embedding_model
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()
    
    def _load_model(self):
        """Load the French multilingual embedding model"""
        try:
            logger.info(f"Loading French embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            
            if self.device == "cuda":
                self.model = self.model.to(self.device)
                logger.info("Model loaded on GPU")
            else:
                logger.info("Model loaded on CPU")
                
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            # Fallback to smaller French model
            try:
                fallback_model = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
                logger.info(f"Trying fallback model: {fallback_model}")
                self.model = SentenceTransformer(fallback_model)
                self.model_name = fallback_model
            except Exception as fallback_error:
                logger.error(f"Fallback model failed: {str(fallback_error)}")
                raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """Convert French text to embedding vector"""
        try:
            if not text or not text.strip():
                return np.zeros(self.get_embedding_dimension())
            
            # Add French prefix for better performance
            prefixed_text = f"passage: {text.strip()}"
            
            with torch.no_grad():
                embedding = self.model.encode(prefixed_text, convert_to_tensor=False)
            
            return np.array(embedding, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return np.zeros(self.get_embedding_dimension())
    
    def embed_query(self, query: str) -> np.ndarray:
        """Convert French query to embedding vector"""
        try:
            if not query or not query.strip():
                return np.zeros(self.get_embedding_dimension())
            
            # Add query prefix for better retrieval
            prefixed_query = f"query: {query.strip()}"
            
            with torch.no_grad():
                embedding = self.model.encode(prefixed_query, convert_to_tensor=False)
            
            return np.array(embedding, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            return np.zeros(self.get_embedding_dimension())
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embedding vectors"""
        if self.model is None:
            return 1024  # Default for multilingual-e5-large
        return self.model.get_sentence_embedding_dimension()
    
    def is_model_loaded(self) -> bool:
        """Check if the embedding model is properly loaded"""
        return self.model is not None

# Global embedding service instance
embedding_service = FrenchEmbeddingService()
