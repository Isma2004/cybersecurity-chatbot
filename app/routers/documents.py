from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from app.services.vector_service import vector_service

router = APIRouter()

@router.get("/documents")
async def list_documents():
    """List all uploaded and processed documents"""
    
    try:
        stats = vector_service.get_stats()
        
        # Get document information from vector store
        documents_info = {}
        
        # Extract document info from stored chunks
        for chunk_id, chunk in vector_service.document_store.items():
            doc_id = chunk.document_id
            
            if doc_id not in documents_info:
                documents_info[doc_id] = {
                    "document_id": doc_id,
                    "filename": chunk.metadata.get('filename', 'Unknown'),
                    "chunks": 0,
                    "total_length": 0,
                    "status": "ready"
                }
            
            documents_info[doc_id]["chunks"] += 1
            documents_info[doc_id]["total_length"] += chunk.metadata.get('chunk_length', 0)
        
        documents_list = list(documents_info.values())
        
        return {
            "documents": documents_list,
            "total_documents": len(documents_list),
            "total_chunks": stats.get('total_chunks', 0),
            "database_stats": stats
        }
        
    except Exception as e:
        print(f"❌ Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its chunks"""
    
    try:
        # Check if document exists
        document_exists = any(
            chunk.document_id == document_id 
            for chunk in vector_service.document_store.values()
        )
        
        if not document_exists:
            raise HTTPException(status_code=404, detail="Document non trouvé")
        
        # Remove from vector database
        success = vector_service.remove_document(document_id)
        
        if success:
            return {
                "message": f"Document {document_id} supprimé avec succès",
                "document_id": document_id
            }
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la suppression")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.post("/documents/clear")
async def clear_all_documents():
    """Clear all documents and reset the database"""
    
    try:
        success = vector_service.clear_all()
        
        if success:
            return {
                "message": "Tous les documents ont été supprimés",
                "status": "database_cleared"
            }
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la suppression")
            
    except Exception as e:
        print(f"❌ Error clearing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(document_id: str):
    """Get all chunks for a specific document"""
    
    try:
        # Find chunks for this document
        document_chunks = [
            {
                "chunk_id": chunk.chunk_id,
                "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                "chunk_index": chunk.chunk_index,
                "metadata": chunk.metadata
            }
            for chunk in vector_service.document_store.values()
            if chunk.document_id == document_id
        ]
        
        if not document_chunks:
            raise HTTPException(status_code=404, detail="Document non trouvé")
        
        # Sort by chunk index
        document_chunks.sort(key=lambda x: x["chunk_index"])
        
        return {
            "document_id": document_id,
            "chunks": document_chunks,
            "total_chunks": len(document_chunks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting document chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
