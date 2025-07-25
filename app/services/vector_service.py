# app/services/vector_service.py
import os
import pickle
import logging
import numpy as np
from datetime import datetime, timedelta  # ADD THIS MISSING IMPORT
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.models.schemas import DocumentChunk, SourceReference
from app.models.schemas import DocumentOwnership

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
        
        # Global documents storage
        self.global_documents = {}  # chunk_id -> DocumentChunk
        self.global_embeddings = {}  # chunk_id -> numpy array
        self.global_metadata_path = "global_vectors.pkl"
    
        # Session-based personal documents (expires after 24 hours)
        self.session_documents = {}  # session_id -> {chunks, embeddings, expires_at}
    
        # Query tracking for analytics
        self.query_log = []
    
        # Load existing data
        self._load_existing_data()
        self._load_global_documents()
        
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

    def _load_global_documents(self):
        """Load global documents from disk"""
        try:
            if os.path.exists(self.global_metadata_path):
                with open(self.global_metadata_path, 'rb') as f:
                    data = pickle.load(f)
                    self.global_documents = data.get('documents', {})
                    self.global_embeddings = data.get('embeddings', {})
                    print(f"📂 Loaded {len(self.global_documents)} global documents")
            else:
                self.global_documents = {}
                self.global_embeddings = {}
        except Exception as e:
            print(f"⚠️ Could not load global documents: {e}")
            self.global_documents = {}
            self.global_embeddings = {}

    def _save_global_documents(self):
        """Save global documents to disk"""
        try:
            data = {
                'documents': self.global_documents,
                'embeddings': self.global_embeddings,
                'embedding_dimension': self.embedding_dimension
            }
            
            with open(self.global_metadata_path, 'wb') as f:
                pickle.dump(data, f)
                
            print(f"💾 Saved {len(self.global_documents)} global documents")
            
        except Exception as e:
            print(f"❌ Error saving global documents: {e}")
    
    def add_document_chunks(self, chunks: List[DocumentChunk], 
                      ownership: DocumentOwnership = DocumentOwnership.PERSONAL,
                      session_id: Optional[str] = None) -> bool:
        """Add document chunks with ownership support"""
        try:
            if not chunks:
                return True
            
            # Check ownership type
            if ownership == DocumentOwnership.GLOBAL:
                return self._add_global_chunks(chunks)
            elif ownership == DocumentOwnership.PERSONAL and session_id:
                return self._add_personal_chunks(chunks, session_id)
            else:
                # Default behavior - add to regular store (backward compatibility)
                return self._add_regular_chunks(chunks)
                
        except Exception as e:
            print(f"❌ Error adding chunks: {str(e)}")
            return False

    def _add_regular_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Add chunks to regular document store (backward compatibility)"""
        try:
            print(f"➕ Adding {len(chunks)} chunks to regular store...")
            
            # Get embedding service
            embedding_service = self._get_embedding_service()
            if not embedding_service:
                print("❌ Embedding service not available")
                return False
            
            successful_chunks = 0
            
            for chunk in chunks:
                try:
                    # Generate embedding
                    embedding = embedding_service.embed_text(chunk.content)
                    
                    # Set dimension if not set
                    if self.embedding_dimension is None:
                        self.embedding_dimension = len(embedding)
                    
                    # Store chunk and embedding
                    self.document_store[chunk.chunk_id] = chunk
                    self.embeddings_store[chunk.chunk_id] = embedding
                    
                    successful_chunks += 1
                    
                except Exception as e:
                    print(f"⚠️ Error processing chunk: {e}")
                    continue
            
            # Save to disk
            self._save_data()
            
            print(f"✅ Added {successful_chunks} regular chunks")
            return successful_chunks > 0
            
        except Exception as e:
            print(f"❌ Error adding regular chunks: {e}")
            return False
    
    def _add_global_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Add chunks to global document store"""
        try:
            print(f"➕ Adding {len(chunks)} chunks to global store...")
            
            # Get embedding service
            embedding_service = self._get_embedding_service()
            if not embedding_service:
                print("❌ Embedding service not available")
                return False
            
            successful_chunks = 0
            
            for chunk in chunks:
                try:
                    # Generate embedding
                    embedding = embedding_service.embed_text(chunk.content)
                    
                    # Set dimension
                    if self.embedding_dimension is None:
                        self.embedding_dimension = len(embedding)
                    
                    # Store in global collections
                    chunk_id = f"global_{hash(chunk.chunk_id) % (2**31)}"
                    self.global_documents[chunk_id] = chunk
                    self.global_embeddings[chunk_id] = embedding
                    
                    successful_chunks += 1
                    
                except Exception as e:
                    print(f"⚠️ Error processing chunk: {e}")
                    continue
            
            # Save to disk
            self._save_global_documents()
            
            print(f"✅ Added {successful_chunks} global chunks")
            return successful_chunks > 0
            
        except Exception as e:
            print(f"❌ Error adding global chunks: {e}")
            return False

    def _add_personal_chunks(self, chunks: List[DocumentChunk], session_id: str) -> bool:
        """Add chunks to session-based personal store"""
        try:
            print(f"➕ Adding {len(chunks)} personal chunks for session {session_id[:8]}...")
            
            # Initialize session if needed
            if session_id not in self.session_documents:
                self.session_documents[session_id] = {
                    'chunks': {},
                    'embeddings': {},
                    'expires_at': datetime.now() + timedelta(hours=24)
                }
            
            # Get embedding service
            embedding_service = self._get_embedding_service()
            if not embedding_service:
                return False
            
            session_data = self.session_documents[session_id]
            successful_chunks = 0
            
            for chunk in chunks:
                try:
                    # Generate embedding
                    embedding = embedding_service.embed_text(chunk.content)
                    
                    # Store in session
                    chunk_id = f"personal_{session_id[:8]}_{hash(chunk.chunk_id) % (2**31)}"
                    session_data['chunks'][chunk_id] = chunk
                    session_data['embeddings'][chunk_id] = embedding
                    
                    successful_chunks += 1
                    
                except Exception as e:
                    print(f"⚠️ Error processing personal chunk: {e}")
                    continue
            
            # Update expiration
            session_data['expires_at'] = datetime.now() + timedelta(hours=24)
            
            print(f"✅ Added {successful_chunks} personal chunks")
            return successful_chunks > 0
            
        except Exception as e:
            print(f"❌ Error adding personal chunks: {e}")
            return False
    
    def search_similar_chunks(self, query: str, top_k: int = 3,
                        session_id: Optional[str] = None,
                        include_global: bool = True,
                        include_personal: bool = True) -> List[SourceReference]:
        """Search chunks from multiple sources"""
        try:
            print(f"🔍 Searching: '{query[:50]}...'")
            
            # Get embedding service
            embedding_service = self._get_embedding_service()
            if not embedding_service:
                return []
            
            # Generate query embedding
            query_embedding = embedding_service.embed_query(query)
            
            similarities = []
            
            # Search regular documents (backward compatibility)
            if not session_id and not include_global:
                # Original behavior
                for chunk_id, chunk in self.document_store.items():
                    if chunk_id in self.embeddings_store:
                        chunk_embedding = self.embeddings_store[chunk_id]
                        similarity = np.dot(query_embedding, chunk_embedding)
                        similarities.append((similarity, chunk_id, chunk, "regular"))
            
            # Search global documents
            if include_global:
                for chunk_id, chunk in self.global_documents.items():
                    if chunk_id in self.global_embeddings:
                        chunk_embedding = self.global_embeddings[chunk_id]
                        similarity = np.dot(query_embedding, chunk_embedding)
                        similarities.append((similarity, chunk_id, chunk, "global"))
            
            # Search personal documents
            if include_personal and session_id:
                self._cleanup_expired_sessions()
                
                if session_id in self.session_documents:
                    session_data = self.session_documents[session_id]
                    
                    for chunk_id, chunk in session_data['chunks'].items():
                        if chunk_id in session_data['embeddings']:
                            chunk_embedding = session_data['embeddings'][chunk_id]
                            similarity = np.dot(query_embedding, chunk_embedding)
                            similarities.append((similarity, chunk_id, chunk, "personal"))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            # Convert to SourceReference objects
            results = []
            for similarity, chunk_id, chunk, source_type in similarities[:top_k]:
                # Add source type to document name
                doc_name = chunk.metadata.get('filename', 'Unknown')
                if source_type != "regular":
                    doc_name = f"[{source_type.upper()}] {doc_name}"
                
                source_ref = SourceReference(
                    document_id=chunk.document_id,
                    document_name=doc_name,
                    chunk_content=chunk.content,
                    relevance_score=float(similarity),
                    page_number=chunk.metadata.get('page_number'),
                    section=chunk.metadata.get('section')
                )
                results.append(source_ref)
            
            # Log query
            self.query_log.append({
                'timestamp': datetime.now(),
                'query': query,
                'session_id': session_id,
                'results_count': len(results)
            })
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching chunks: {str(e)}")
            return []

    def _cleanup_expired_sessions(self):
        """Remove expired session documents"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, data in self.session_documents.items():
            if data['expires_at'] < now:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.session_documents[session_id]
            print(f"🗑️ Cleaned up expired session: {session_id[:8]}...")

    def get_documents_by_ownership(self, ownership: DocumentOwnership) -> List[Dict]:
        """Get documents by ownership type"""
        documents = {}
        
        if ownership == DocumentOwnership.GLOBAL:
            for chunk_id, chunk in self.global_documents.items():
                doc_id = chunk.document_id
                if doc_id not in documents:
                    documents[doc_id] = {
                        "document_id": doc_id,
                        "filename": chunk.metadata.get('filename', 'Unknown'),
                        "uploaded_by": chunk.metadata.get('uploaded_by', 'Unknown'),
                        "upload_date": chunk.metadata.get('upload_date', datetime.now().isoformat()),
                        "description": chunk.metadata.get('description', ''),
                        "tags": chunk.metadata.get('tags', []),
                        "chunks": 0,
                        "is_active": chunk.metadata.get('is_active', True)
                    }
                documents[doc_id]["chunks"] += 1
        
        return list(documents.values())

    def get_admin_stats(self) -> Dict[str, Any]:
        """Get statistics for admin dashboard"""
        try:
            # Count unique global documents
            global_doc_ids = set(chunk.document_id for chunk in self.global_documents.values())
            
            # Count personal documents across all sessions
            personal_doc_count = 0
            for session_data in self.session_documents.values():
                doc_ids = set(chunk.document_id for chunk in session_data['chunks'].values())
                personal_doc_count += len(doc_ids)
            
            return {
                "total_global_documents": len(global_doc_ids),
                "total_personal_documents": personal_doc_count,
                "active_users": len(self.session_documents),
                "queries_today": sum(1 for q in self.query_log 
                                if q['timestamp'].date() == datetime.now().date()),
                "popular_documents": [],  # Implement tracking if needed
                "recent_uploads": []  # Implement tracking if needed
            }
            
        except Exception as e:
            print(f"❌ Error getting admin stats: {e}")
            return {
                "total_global_documents": 0,
                "total_personal_documents": 0,
                "active_users": 0,
                "queries_today": 0,
                "popular_documents": [],
                "recent_uploads": []
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector database statistics"""
        try:
            # Count regular documents
            regular_unique_docs = len(set(chunk.document_id for chunk in self.document_store.values()))
            
            # Count global documents  
            global_unique_docs = len(set(chunk.document_id for chunk in self.global_documents.values()))
            
            # Count personal documents
            personal_unique_docs = 0
            for session_data in self.session_documents.values():
                doc_ids = set(chunk.document_id for chunk in session_data['chunks'].values())
                personal_unique_docs += len(doc_ids)
            
            total_vectors = len(self.embeddings_store) + len(self.global_embeddings)
            for session_data in self.session_documents.values():
                total_vectors += len(session_data['embeddings'])
            
            total_chunks = len(self.document_store) + len(self.global_documents)
            for session_data in self.session_documents.values():
                total_chunks += len(session_data['chunks'])
            
            return {
                "total_vectors": total_vectors,
                "embedding_dimension": self.embedding_dimension or 0,
                "total_documents": regular_unique_docs + global_unique_docs + personal_unique_docs,
                "regular_documents": regular_unique_docs,
                "global_documents": global_unique_docs,
                "personal_documents": personal_unique_docs,
                "total_chunks": total_chunks,
                "index_type": "Cloud Embeddings + Cosine Similarity",
                "status": "ready" if (self.document_store or self.global_documents) else "empty"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def remove_document(self, document_id: str) -> bool:
        """Remove all chunks for a specific document from all stores"""
        try:
            removed_count = 0
            
            # Remove from regular store
            chunks_to_remove = []
            for chunk_id, chunk in self.document_store.items():
                if chunk.document_id == document_id:
                    chunks_to_remove.append(chunk_id)
            
            for chunk_id in chunks_to_remove:
                if chunk_id in self.document_store:
                    del self.document_store[chunk_id]
                if chunk_id in self.embeddings_store:
                    del self.embeddings_store[chunk_id]
                removed_count += 1
            
            # Remove from global store
            global_chunks_to_remove = []
            for chunk_id, chunk in self.global_documents.items():
                if chunk.document_id == document_id:
                    global_chunks_to_remove.append(chunk_id)
            
            for chunk_id in global_chunks_to_remove:
                if chunk_id in self.global_documents:
                    del self.global_documents[chunk_id]
                if chunk_id in self.global_embeddings:
                    del self.global_embeddings[chunk_id]
                removed_count += 1
            
            # Remove from personal stores
            for session_id, session_data in self.session_documents.items():
                personal_chunks_to_remove = []
                for chunk_id, chunk in session_data['chunks'].items():
                    if chunk.document_id == document_id:
                        personal_chunks_to_remove.append(chunk_id)
                
                for chunk_id in personal_chunks_to_remove:
                    if chunk_id in session_data['chunks']:
                        del session_data['chunks'][chunk_id]
                    if chunk_id in session_data['embeddings']:
                        del session_data['embeddings'][chunk_id]
                    removed_count += 1
            
            if removed_count == 0:
                print(f"⚠️ No chunks found for document {document_id}")
                return False
            
            # Save updated data
            self._save_data()
            self._save_global_documents()
            
            print(f"🗑️ Removed {removed_count} chunks for document {document_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error removing document: {str(e)}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all documents and vectors"""
        try:
            self.document_store.clear()
            self.embeddings_store.clear()
            self.global_documents.clear()
            self.global_embeddings.clear()
            self.session_documents.clear()
            self.embedding_dimension = None
            
            # Save empty state
            self._save_data()
            self._save_global_documents()
            
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