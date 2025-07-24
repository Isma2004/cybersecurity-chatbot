# app/services/vector_service.py
import os
import pickle
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.models.schemas import DocumentChunk, SourceReference

logger = logging.getLogger(__name__)

class CloudVectorService:
    """Lightweight vector service using cloud embeddings and simple similarity"""
    
    def __init__(self):
        print("🚀 Creating cloud vector service...")
        
        # Initialize storage
        self.document_store = {}  # chunk_id -> DocumentChunk
        self.embeddings_store = {}  # chunk_id -> numpy array
        self.embedding_dimension = None  # Will be set dynamically
        
        # Storage paths
        self.metadata_path = "cloud_vectors.pkl"
        
        # Load existing data
        self._load_existing_data()
        
        print("✅ Cloud vector service ready!")
    
    def _get_embedding_service(self):
        """Get embedding service (lazy import to avoid circular dependency)"""
        try:
            from app.services.embedding_service import embedding_service
            return embedding_service
        except ImportError:
            print("⚠️ Embedding service not available")
            return None
    
    def _load_existing_data(self):
        """Load existing vectors and metadata"""
        try:
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'rb') as f:
                    data = pickle.load(f)
                    self.document_store = data.get('documents', {})
                    self.embeddings_store = data.get('embeddings', {})
                    self.embedding_dimension = data.get('embedding_dimension')
                    
                print(f"📂 Loaded {len(self.document_store)} existing chunks")
                if self.embedding_dimension:
                    print(f"📐 Embedding dimension: {self.embedding_dimension}")
        except Exception as e:
            print(f"⚠️ Could not load existing data: {e}")
    
    def _save_data(self):
        """Save vectors and metadata to disk"""
        try:
            # Ensure directory exists
            Path(self.metadata_path).parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'documents': self.document_store,
                'embeddings': self.embeddings_store,
                'embedding_dimension': self.embedding_dimension
            }
            
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(data, f)
                
            print(f"💾 Saved {len(self.document_store)} chunks to disk")
            
        except Exception as e:
            print(f"❌ Error saving data: {e}")
    
    def add_document_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Add document chunks using cloud embeddings"""
        try:
            if not chunks:
                return True
            
            print(f"➕ Adding {len(chunks)} chunks to cloud vector database...")
            
            # Get embedding service
            embedding_service = self._get_embedding_service()
            if not embedding_service:
                print("❌ Embedding service not available")
                return False
            
            # Process chunks
            successful_chunks = 0
            
            for i, chunk in enumerate(chunks):
                try:
                    # Generate embedding using cloud service
                    embedding = embedding_service.embed_text(chunk.content)
                    
                    # Set dimension from first embedding
                    if self.embedding_dimension is None:
                        self.embedding_dimension = len(embedding)
                        print(f"📐 Set embedding dimension: {self.embedding_dimension}")
                    
                    # Generate unique chunk ID
                    chunk_id = hash(chunk.chunk_id) % (2**31)  # Positive 32-bit int
                    
                    # Store chunk and embedding
                    self.document_store[chunk_id] = chunk
                    self.embeddings_store[chunk_id] = embedding
                    
                    successful_chunks += 1
                    
                    if (i + 1) % 10 == 0:
                        print(f"   📝 Processed {i + 1}/{len(chunks)} chunks")
                        
                except Exception as e:
                    print(f"⚠️ Error processing chunk {i}: {e}")
                    continue
            
            # Save to disk
            self._save_data()
            
            print(f"✅ Successfully added {successful_chunks}/{len(chunks)} chunks")
            print(f"📊 Total chunks in database: {len(self.document_store)}")
            
            return successful_chunks > 0
            
        except Exception as e:
            print(f"❌ Error adding chunks: {str(e)}")
            return False
    
    def search_similar_chunks(self, query: str, top_k: int = 3) -> List[SourceReference]:
        """Search for similar chunks using cloud embeddings"""
        try:
            if not self.document_store:
                print("⚠️ No documents in vector database yet")
                return []
            
            print(f"🔍 Searching for: '{query[:50]}...'")
            
            # Get embedding service
            embedding_service = self._get_embedding_service()
            if not embedding_service:
                print("❌ Embedding service not available")
                return []
            
            # Generate query embedding
            query_embedding = embedding_service.embed_query(query)
            
            # Calculate similarities
            similarities = []
            
            for chunk_id, chunk in self.document_store.items():
                if chunk_id in self.embeddings_store:
                    chunk_embedding = self.embeddings_store[chunk_id]
                    
                    # Cosine similarity
                    similarity = np.dot(query_embedding, chunk_embedding)
                    similarities.append((similarity, chunk_id, chunk))
            
            # Sort by similarity (highest first)
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            # Convert to SourceReference objects
            results = []
            for similarity, chunk_id, chunk in similarities[:top_k]:
                source_ref = SourceReference(
                    document_id=chunk.document_id,
                    document_name=chunk.metadata.get('filename', 'Unknown'),
                    chunk_content=chunk.content,
                    relevance_score=float(similarity),
                    page_number=chunk.metadata.get('page_number'),
                    section=chunk.metadata.get('section')
                )
                results.append(source_ref)
            
            print(f"🎯 Found {len(results)} relevant chunks")
            for i, result in enumerate(results):
                print(f"   {i+1}. Score: {result.relevance_score:.3f} - {result.chunk_content[:60]}...")
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching chunks: {str(e)}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector database statistics"""
        try:
            unique_docs = len(set(chunk.document_id for chunk in self.document_store.values()))
            
            return {
                "total_vectors": len(self.embeddings_store),
                "embedding_dimension": self.embedding_dimension or 0,
                "total_documents": unique_docs,
                "total_chunks": len(self.document_store),
                "index_type": "Cloud Embeddings + Cosine Similarity",
                "status": "ready" if self.document_store else "empty"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def remove_document(self, document_id: str) -> bool:
        """Remove all chunks for a specific document"""
        try:
            # Find chunks to remove
            chunks_to_remove = []
            for chunk_id, chunk in self.document_store.items():
                if chunk.document_id == document_id:
                    chunks_to_remove.append(chunk_id)
            
            if not chunks_to_remove:
                print(f"⚠️ No chunks found for document {document_id}")
                return False
            
            # Remove chunks and embeddings
            for chunk_id in chunks_to_remove:
                if chunk_id in self.document_store:
                    del self.document_store[chunk_id]
                if chunk_id in self.embeddings_store:
                    del self.embeddings_store[chunk_id]
            
            # Save updated data
            self._save_data()
            
            print(f"🗑️ Removed {len(chunks_to_remove)} chunks for document {document_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error removing document: {str(e)}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all documents and vectors"""
        try:
            self.document_store.clear()
            self.embeddings_store.clear()
            self.embedding_dimension = None
            
            # Save empty state
            self._save_data()
            
            print("🗑️ Cleared all vectors and documents")
            return True
            
        except Exception as e:
            print(f"❌ Error clearing database: {str(e)}")
            return False
    
    def is_ready(self) -> bool:
        """Check if vector service is ready"""
        return True  # Always ready

# Global vector service instance
print("🚀 Creating cloud vector service...")
vector_service = CloudVectorService()
print("✅ Vector service ready!")