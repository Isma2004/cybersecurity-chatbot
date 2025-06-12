import os
import pickle
import logging
import numpy as np
import faiss
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import psutil

from app.models.schemas import DocumentChunk, SourceReference
from app.services.embedding_service import embedding_service
from app.utils.config import settings

logger = logging.getLogger(__name__)

class FAISSVectorService:
    def __init__(self):
        print(f"🔍 Memory before vector service init: {psutil.virtual_memory().used / (1024**3):.1f} GB")
        # ... existing code ...
        print(f"🔍 Memory after vector service init: {psutil.virtual_memory().used / (1024**3):.1f} GB")
    
    def _initialize_embeddings(self):
        """Initialize embedding model with memory optimization"""
        try:
            print("🧮 Loading embedding model...")
            print(f"💾 Memory before embedding model: {psutil.virtual_memory().used / (1024**3):.1f} GB")
            
            # Use a smaller, more memory-efficient model
            from sentence_transformers import SentenceTransformer
            
            # Try smaller models first
            model_options = [
                "all-MiniLM-L6-v2",  # ~90MB, 384 dimensions
                "paraphrase-MiniLM-L3-v2",  # ~61MB, 384 dimensions
                "all-distilroberta-v1"  # ~290MB, 768 dimensions
            ]
            
            for model_name in model_options:
                try:
                    print(f"🔄 Trying model: {model_name}")
                    self.embedding_model = SentenceTransformer(model_name)
                    print(f"✅ Successfully loaded: {model_name}")
                    print(f"💾 Memory after loading {model_name}: {psutil.virtual_memory().used / (1024**3):.1f} GB")
                    break
                except Exception as e:
                    print(f"❌ Failed to load {model_name}: {e}")
                    continue
            
            if not hasattr(self, 'embedding_model'):
                raise Exception("Failed to load any embedding model")
                
        except Exception as e:
            print(f"❌ Error initializing embeddings: {e}")
            raise
    
    def _create_new_index(self):
        """Create a new FAISS index optimized for medium-scale document collections"""
        try:
            # For small/medium datasets: use exact search (IndexFlatL2)
            # This gives perfect accuracy for our use case
            self.index = faiss.IndexFlatL2(self.embedding_dimension)
            
            # Wrap with ID map to track document chunk IDs
            self.index = faiss.IndexIDMap(self.index)
            
            print(f"🎯 Created FAISS IndexFlatL2 with dimension {self.embedding_dimension}")
            
        except Exception as e:
            print(f"❌ Error creating FAISS index: {str(e)}")
            raise
    
    def _load_existing_index(self) -> bool:
        """Load existing FAISS index and metadata"""
        try:
            if not os.path.exists(self.index_path) or not os.path.exists(self.metadata_path):
                return False
            
            # Load FAISS index
            self.index = faiss.read_index(self.index_path)
            
            # Load document metadata
            with open(self.metadata_path, 'rb') as f:
                self.document_store = pickle.load(f)
            
            print(f"📂 Loaded {self.index.ntotal} vectors from existing index")
            return True
            
        except Exception as e:
            print(f"⚠️ Error loading existing index: {str(e)}")
            return False
    
    def _save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            # Ensure directory exists
            Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, self.index_path)
            
            # Save document metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.document_store, f)
            
            print(f"💾 Saved index with {self.index.ntotal} vectors")
            
        except Exception as e:
            print(f"❌ Error saving index: {str(e)}")
    
    def add_document_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Add document chunks to the vector database"""
        try:
            if not chunks:
                return True
            
            print(f"➕ Adding {len(chunks)} chunks to vector database...")
            
            # Generate embeddings for all chunks
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = []
            
            for i, text in enumerate(chunk_texts):
                embedding = embedding_service.embed_text(text)
                embeddings.append(embedding)
                if (i + 1) % 10 == 0:
                    print(f"   📝 Processed {i + 1}/{len(chunk_texts)} chunks")
            
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Generate unique IDs for each chunk
            chunk_ids = []
            for chunk in chunks:
                # Use hash of chunk_id to create unique integer ID
                chunk_id = hash(chunk.chunk_id) % (2**31)  # Keep it positive 32-bit int
                chunk_ids.append(chunk_id)
                
                # Store chunk in document store
                self.document_store[chunk_id] = chunk
            
            chunk_ids_array = np.array(chunk_ids, dtype=np.int64)
            
            # Add to FAISS index
            self.index.add_with_ids(embeddings_array, chunk_ids_array)
            
            # Save to disk
            self._save_index()
            
            print(f"✅ Successfully added {len(chunks)} chunks to vector database")
            print(f"📊 Total vectors in database: {self.index.ntotal}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding chunks to vector database: {str(e)}")
            return False
    
    def search_similar_chunks(self, query: str, top_k: int = 3) -> List[SourceReference]:
        """Search for similar chunks using the query"""
        try:
            if self.index.ntotal == 0:
                print("⚠️ No documents in vector database yet")
                return []
            
            print(f"🔍 Searching for: '{query[:50]}...'")
            
            # Generate query embedding
            query_embedding = embedding_service.embed_query(query)
            query_vector = np.array([query_embedding], dtype=np.float32)
            
            # Search in FAISS
            similarities, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))
            
            # Convert results to SourceReference objects
            results = []
            for i in range(len(similarities[0])):
                if indices[0][i] != -1:  # Valid result
                    chunk_id = indices[0][i]
                    similarity = float(similarities[0][i])
                    
                    # Convert L2 distance to similarity score (0-1)
                    # Lower L2 distance = higher similarity
                    similarity_score = 1.0 / (1.0 + similarity)
                    
                    if chunk_id in self.document_store:
                        chunk = self.document_store[chunk_id]
                        
                        source_ref = SourceReference(
                            document_id=chunk.document_id,
                            document_name=chunk.metadata.get('filename', 'Unknown'),
                            chunk_content=chunk.content,
                            relevance_score=similarity_score,
                            page_number=chunk.metadata.get('page_number'),
                            section=chunk.metadata.get('section')
                        )
                        results.append(source_ref)
            
            print(f"🎯 Found {len(results)} relevant chunks")
            for i, result in enumerate(results):
                print(f"   {i+1}. Score: {result.relevance_score:.3f} - {result.chunk_content[:60]}...")
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching vector database: {str(e)}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector database statistics"""
        try:
            return {
                "total_vectors": self.index.ntotal if self.index else 0,
                "embedding_dimension": self.embedding_dimension,
                "total_documents": len(set(chunk.document_id for chunk in self.document_store.values())),
                "total_chunks": len(self.document_store),
                "index_type": "IndexFlatL2 (Exact Search)",
                "status": "ready" if self.index and self.index.ntotal > 0 else "empty"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def remove_document(self, document_id: str) -> bool:
        """Remove all chunks for a specific document"""
        try:
            # Find chunks for this document
            chunks_to_remove = [
                chunk_id for chunk_id, chunk in self.document_store.items() 
                if chunk.document_id == document_id
            ]
            
            if not chunks_to_remove:
                print(f"⚠️ No chunks found for document {document_id}")
                return False
            
            # Remove from document store
            for chunk_id in chunks_to_remove:
                del self.document_store[chunk_id]
            
            # Note: FAISS doesn't support easy removal of specific vectors
            # For now, we'll rebuild the index without these chunks
            print(f"🗑️ Removed {len(chunks_to_remove)} chunks for document {document_id}")
            
            # Save updated metadata
            self._save_index()
            
            return True
            
        except Exception as e:
            print(f"❌ Error removing document: {str(e)}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all vectors and documents"""
        try:
            self._create_new_index()
            self.document_store.clear()
            self._save_index()
            print("🗑️ Cleared all vectors and documents")
            return True
        except Exception as e:
            print(f"❌ Error clearing database: {str(e)}")
            return False

# Global vector service instance
print("🚀 Creating FAISS vector service...")
vector_service = FAISSVectorService()
print("✅ Vector service ready!")
