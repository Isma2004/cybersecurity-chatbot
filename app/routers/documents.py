from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import os

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
                    "status": "ready",
                    "file_type": getattr(chunk, 'file_type', 'unknown'),
                    "upload_date": getattr(chunk, 'upload_date', None)
                }
            
            documents_info[doc_id]["chunks"] += 1
            documents_info[doc_id]["total_length"] += chunk.metadata.get('chunk_length', 0)
        
        documents_list = list(documents_info.values())
        
        return {
            "documents": documents_list,
            "total_documents": len(documents_list),
            "total_chunks": stats.get('total_chunks', 0),
            "database_stats": stats,
            "status": "success"
        }
        
    except Exception as e:
        print(f"❌ Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération des documents: {str(e)}"
        )

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its chunks, and remove the file from disk"""
    try:
        # Check if document exists
        document_exists = any(
            chunk.document_id == document_id 
            for chunk in vector_service.document_store.values()
        )
        
        if not document_exists:
            raise HTTPException(
                status_code=404, 
                detail=f"Document {document_id} non trouvé"
            )
        
        # Get document info before deletion
        doc_info = None
        for chunk in vector_service.document_store.values():
            if chunk.document_id == document_id:
                doc_info = {
                    "filename": chunk.metadata.get('filename', 'Unknown'),
                    "chunks": sum(1 for c in vector_service.document_store.values() if c.document_id == document_id)
                }
                break

        # Remove from vector database
        success = vector_service.remove_document(document_id)

        # Remove from disk (documents folder)
        documents_dir = "./documents"
        file_deleted = False
        for filename in os.listdir(documents_dir):
            if filename.startswith(document_id):
                file_path = os.path.join(documents_dir, filename)
                try:
                    os.remove(file_path)
                    file_deleted = True
                except Exception as e:
                    print(f"❌ Error deleting file from disk: {file_path} - {e}")
                break  # Remove only the first matching file

        if success:
            return {
                "message": f"Document '{doc_info['filename']}' supprimé avec succès",
                "document_id": document_id,
                "deleted_chunks": doc_info['chunks'],
                "file_deleted": file_deleted,
                "status": "deleted"
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail="Erreur lors de la suppression du document"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la suppression: {str(e)}"
        )

@router.post("/documents/clear")
async def clear_all_documents():
    """Clear all documents and reset the database"""
    
    try:
        # Get current stats before clearing
        stats = vector_service.get_stats()
        total_docs = stats.get('total_documents', 0)
        total_chunks = stats.get('total_chunks', 0)
        
        # Clear the database
        success = vector_service.clear_all()
        
        if success:
            return {
                "message": "Tous les documents ont été supprimés",
                "status": "database_cleared",
                "deleted_documents": total_docs,
                "deleted_chunks": total_chunks
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail="Erreur lors de la suppression de tous les documents"
            )
            
    except Exception as e:
        print(f"❌ Error clearing documents: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la suppression: {str(e)}"
        )

@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(document_id: str, limit: int = 10):
    """Get all chunks for a specific document"""
    
    try:
        # Find chunks for this document
        document_chunks = []
        
        for chunk_id, chunk in vector_service.document_store.items():
            if chunk.document_id == document_id:
                document_chunks.append({
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    "full_content": chunk.content,  # Include full content
                    "chunk_index": chunk.chunk_index,
                    "metadata": chunk.metadata,
                    "length": len(chunk.content)
                })
        
        if not document_chunks:
            raise HTTPException(
                status_code=404, 
                detail=f"Document {document_id} non trouvé"
            )
        
        # Sort by chunk index
        document_chunks.sort(key=lambda x: x["chunk_index"])
        
        # Apply limit
        if limit > 0:
            document_chunks = document_chunks[:limit]
        
        return {
            "document_id": document_id,
            "chunks": document_chunks,
            "total_chunks": len(document_chunks),
            "filename": document_chunks[0]["metadata"].get("filename", "Unknown") if document_chunks else "Unknown",
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting document chunks: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération des chunks: {str(e)}"
        )