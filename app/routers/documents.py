from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any, Optional
import os
from datetime import datetime

from app.services.vector_service import vector_service
from app.services.auth_service import auth_service
from app.models.schemas import DocumentOwnership
from app.utils.config import settings

router = APIRouter()
security = HTTPBearer(auto_error=False)

@router.get("/documents")
async def list_documents(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """List all available documents based on user authentication"""
    
    try:
        # Check authentication
        session_id = None
        username = "anonymous"
        is_authenticated = False
        
        if credentials:
            token = credentials.credentials
            payload = auth_service.verify_token(token)
            if payload:
                session_id = payload.get("session_id")
                username = payload.get("sub")
                is_authenticated = True
        
        # Get comprehensive stats
        stats = vector_service.get_stats()
        
        # Collect documents from all sources
        all_documents = []
        
        # 1. Regular documents (backward compatibility)
        regular_docs = {}
        for chunk_id, chunk in vector_service.document_store.items():
            doc_id = chunk.document_id
            if doc_id not in regular_docs:
                regular_docs[doc_id] = {
                    "document_id": doc_id,
                    "filename": chunk.metadata.get('filename', 'Unknown'),
                    "chunks": 0,
                    "total_length": 0,
                    "status": "ready",
                    "ownership": "regular",
                    "source": "regular_store",
                    "uploaded_by": chunk.metadata.get('uploaded_by', 'unknown'),
                    "upload_date": chunk.metadata.get('upload_date', 'unknown')
                }
            regular_docs[doc_id]["chunks"] += 1
            regular_docs[doc_id]["total_length"] += len(chunk.content)
        
        all_documents.extend(list(regular_docs.values()))
        
        # 2. Global documents (always visible)
        global_docs = {}
        for chunk_id, chunk in vector_service.global_documents.items():
            doc_id = chunk.document_id
            if doc_id not in global_docs:
                global_docs[doc_id] = {
                    "document_id": doc_id,
                    "filename": chunk.metadata.get('filename', 'Unknown'),
                    "chunks": 0,
                    "total_length": 0,
                    "status": "ready",
                    "ownership": "global",
                    "source": "global_store",
                    "uploaded_by": chunk.metadata.get('uploaded_by', 'admin'),
                    "upload_date": chunk.metadata.get('upload_date', 'unknown'),
                    "description": chunk.metadata.get('description', ''),
                    "tags": chunk.metadata.get('tags', [])
                }
            global_docs[doc_id]["chunks"] += 1
            global_docs[doc_id]["total_length"] += len(chunk.content)
        
        all_documents.extend(list(global_docs.values()))
        
        # 3. Personal documents (only if authenticated)
        personal_docs = {}
        if is_authenticated and session_id and session_id in vector_service.session_documents:
            session_data = vector_service.session_documents[session_id]
            for chunk_id, chunk in session_data['chunks'].items():
                doc_id = chunk.document_id
                if doc_id not in personal_docs:
                    personal_docs[doc_id] = {
                        "document_id": doc_id,
                        "filename": chunk.metadata.get('filename', 'Unknown'),
                        "chunks": 0,
                        "total_length": 0,
                        "status": "ready",
                        "ownership": "personal",
                        "source": "personal_store",
                        "session_id": session_id[:8],
                        "uploaded_by": username,
                        "upload_date": chunk.metadata.get('upload_date', 'unknown'),
                        "expires_at": session_data['expires_at'].isoformat()
                    }
                personal_docs[doc_id]["chunks"] += 1
                personal_docs[doc_id]["total_length"] += len(chunk.content)
        
        all_documents.extend(list(personal_docs.values()))
        
        # Check files on disk
        disk_files = {
            "global": [],
            "personal": [],
            "uploads": []
        }
        
        # Check global directory
        if os.path.exists(settings.global_docs_dir):
            for filename in os.listdir(settings.global_docs_dir):
                file_path = os.path.join(settings.global_docs_dir, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    disk_files["global"].append({
                        "filename": filename,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "path": file_path
                    })
        
        # Check personal directory
        if os.path.exists(settings.personal_docs_dir):
            for filename in os.listdir(settings.personal_docs_dir):
                file_path = os.path.join(settings.personal_docs_dir, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    disk_files["personal"].append({
                        "filename": filename,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "path": file_path
                    })
        
        # Check uploads directory
        if os.path.exists(settings.upload_dir):
            for filename in os.listdir(settings.upload_dir):
                file_path = os.path.join(settings.upload_dir, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    disk_files["uploads"].append({
                        "filename": filename,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "path": file_path
                    })
        
        return {
            "documents": all_documents,
            "total_documents": len(all_documents),
            "breakdown": {
                "regular": len(regular_docs),
                "global": len(global_docs),
                "personal": len(personal_docs)
            },
            "user_info": {
                "authenticated": is_authenticated,
                "username": username,
                "session_id": session_id[:8] if session_id else None
            },
            "vector_database_stats": stats,
            "files_on_disk": disk_files,
            "directories": {
                "global_docs_dir": {
                    "path": settings.global_docs_dir,
                    "exists": os.path.exists(settings.global_docs_dir)
                },
                "personal_docs_dir": {
                    "path": settings.personal_docs_dir,
                    "exists": os.path.exists(settings.personal_docs_dir)
                },
                "upload_dir": {
                    "path": settings.upload_dir,
                    "exists": os.path.exists(settings.upload_dir)
                }
            },
            "status": "success"
        }
        
    except Exception as e:
        print(f"❌ Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération des documents: {str(e)}"
        )

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str, 
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Delete a document and all its chunks, and remove the file from disk"""
    try:
        # Check if document exists in any store
        document_exists = False
        doc_info = {"filename": "Unknown", "chunks": 0, "ownership": "unknown"}
        
        # Check regular store
        for chunk in vector_service.document_store.values():
            if chunk.document_id == document_id:
                document_exists = True
                doc_info = {
                    "filename": chunk.metadata.get('filename', 'Unknown'),
                    "chunks": sum(1 for c in vector_service.document_store.values() if c.document_id == document_id),
                    "ownership": "regular"
                }
                break
        
        # Check global store
        if not document_exists:
            for chunk in vector_service.global_documents.values():
                if chunk.document_id == document_id:
                    document_exists = True
                    doc_info = {
                        "filename": chunk.metadata.get('filename', 'Unknown'),
                        "chunks": sum(1 for c in vector_service.global_documents.values() if c.document_id == document_id),
                        "ownership": "global"
                    }
                    break
        
        # Check personal stores
        if not document_exists and credentials:
            token = credentials.credentials
            payload = auth_service.verify_token(token)
            if payload:
                session_id = payload.get("session_id")
                if session_id in vector_service.session_documents:
                    session_data = vector_service.session_documents[session_id]
                    for chunk in session_data['chunks'].values():
                        if chunk.document_id == document_id:
                            document_exists = True
                            doc_info = {
                                "filename": chunk.metadata.get('filename', 'Unknown'),
                                "chunks": sum(1 for c in session_data['chunks'].values() if c.document_id == document_id),
                                "ownership": "personal"
                            }
                            break
        
        if not document_exists:
            raise HTTPException(
                status_code=404, 
                detail=f"Document {document_id} non trouvé"
            )

        # Remove from vector database (handles all stores)
        success = vector_service.remove_document(document_id)

        # Remove from disk based on ownership and document metadata
        files_deleted = []
        
        # Get file extension from document metadata
        file_extension = ""
        ownership = doc_info['ownership']
        
        # Find file extension from chunk metadata
        if ownership == "regular":
            for chunk in vector_service.document_store.values():
                if chunk.document_id == document_id:
                    file_extension = chunk.metadata.get('file_extension', '')
                    break
        elif ownership == "global":
            for chunk in vector_service.global_documents.values():
                if chunk.document_id == document_id:
                    file_extension = chunk.metadata.get('file_extension', '')
                    break
        elif ownership == "personal" and credentials:
            token = credentials.credentials
            payload = auth_service.verify_token(token)
            if payload:
                session_id = payload.get("session_id")
                if session_id in vector_service.session_documents:
                    session_data = vector_service.session_documents[session_id]
                    for chunk in session_data['chunks'].values():
                        if chunk.document_id == document_id:
                            file_extension = chunk.metadata.get('file_extension', '')
                            break
        
        # Determine the correct directory based on ownership
        target_directories = []
        if ownership == "global":
            target_directories = [settings.global_docs_dir]
        elif ownership == "personal":
            target_directories = [settings.personal_docs_dir]
        elif ownership == "regular":
            target_directories = [settings.upload_dir]
        else:
            # Fallback: check all directories
            target_directories = [
                settings.global_docs_dir,
                settings.personal_docs_dir,
                settings.upload_dir
            ]
        
        # Look for the specific file
        expected_filename = f"{document_id}{file_extension}"
        
        for documents_dir in target_directories:
            if os.path.exists(documents_dir):
                file_path = os.path.join(documents_dir, expected_filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        files_deleted.append({
                            "filename": expected_filename,
                            "path": file_path,
                            "directory": documents_dir
                        })
                        print(f"✅ Deleted file from disk: {file_path}")
                    except Exception as e:
                        print(f"❌ Error deleting file from disk: {file_path} - {e}")
                
                # Also check for files that start with document_id (backup search)
                for filename in os.listdir(documents_dir):
                    if filename.startswith(document_id) and filename != expected_filename:
                        file_path = os.path.join(documents_dir, filename)
                        try:
                            os.remove(file_path)
                            files_deleted.append({
                                "filename": filename,
                                "path": file_path,
                                "directory": documents_dir
                            })
                            print(f"✅ Deleted backup file from disk: {file_path}")
                        except Exception as e:
                            print(f"❌ Error deleting backup file from disk: {file_path} - {e}")

        if success:
            return {
                "message": f"Document '{doc_info['filename']}' supprimé avec succès",
                "document_id": document_id,
                "deleted_chunks": doc_info['chunks'],
                "ownership": doc_info['ownership'],
                "files_deleted": files_deleted,
                "files_deleted_count": len(files_deleted),
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
async def clear_all_documents(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Clear all documents and reset the database"""
    
    try:
        # Check if user is admin (optional - could allow anyone to clear their own)
        is_admin = False
        if credentials:
            token = credentials.credentials
            payload = auth_service.verify_token(token)
            if payload and payload.get("role") == "admin":
                is_admin = True
        
        # Get current stats before clearing
        stats = vector_service.get_stats()
        total_docs = stats.get('total_documents', 0)
        total_chunks = stats.get('total_chunks', 0)
        
        # Clear the database
        success = vector_service.clear_all()
        
        # Optionally clear files from disk (only if admin)
        files_cleared = []
        if is_admin:
            directories_to_clear = [
                settings.global_docs_dir,
                settings.personal_docs_dir,
                settings.upload_dir
            ]
            
            for dir_path in directories_to_clear:
                if os.path.exists(dir_path):
                    for filename in os.listdir(dir_path):
                        file_path = os.path.join(dir_path, filename)
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                files_cleared.append(file_path)
                        except Exception as e:
                            print(f"⚠️ Could not remove {file_path}: {e}")
        
        if success:
            return {
                "message": "Tous les documents ont été supprimés",
                "status": "database_cleared",
                "deleted_documents": total_docs,
                "deleted_chunks": total_chunks,
                "files_cleared": len(files_cleared) if is_admin else "N/A (requires admin)",
                "admin_action": is_admin
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
    """Get all chunks for a specific document from all stores"""
    
    try:
        # Find chunks for this document across all stores
        document_chunks = []
        
        # Search regular store
        for chunk_id, chunk in vector_service.document_store.items():
            if chunk.document_id == document_id:
                document_chunks.append({
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    "full_content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "metadata": chunk.metadata,
                    "length": len(chunk.content),
                    "source": "regular_store"
                })
        
        # Search global store
        for chunk_id, chunk in vector_service.global_documents.items():
            if chunk.document_id == document_id:
                document_chunks.append({
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    "full_content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "metadata": chunk.metadata,
                    "length": len(chunk.content),
                    "source": "global_store"
                })
        
        # Search personal stores
        for session_id, session_data in vector_service.session_documents.items():
            for chunk_id, chunk in session_data['chunks'].items():
                if chunk.document_id == document_id:
                    document_chunks.append({
                        "chunk_id": chunk.chunk_id,
                        "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                        "full_content": chunk.content,
                        "chunk_index": chunk.chunk_index,
                        "metadata": chunk.metadata,
                        "length": len(chunk.content),
                        "source": f"personal_store_{session_id[:8]}"
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
            limited_chunks = document_chunks[:limit]
        else:
            limited_chunks = document_chunks
        
        return {
            "document_id": document_id,
            "chunks": limited_chunks,
            "total_chunks": len(document_chunks),
            "showing_chunks": len(limited_chunks),
            "filename": document_chunks[0]["metadata"].get("filename", "Unknown") if document_chunks else "Unknown",
            "sources_found": list(set(chunk["source"] for chunk in document_chunks)),
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

@router.get("/documents/stats")
async def get_detailed_stats():
    """Get detailed statistics about documents and storage"""
    try:
        # Get vector service stats
        vector_stats = vector_service.get_stats()
        
        # Count files on disk
        disk_stats = {}
        directories = {
            "global": settings.global_docs_dir,
            "personal": settings.personal_docs_dir,
            "uploads": settings.upload_dir
        }
        
        total_disk_files = 0
        total_disk_size = 0
        
        for dir_name, dir_path in directories.items():
            disk_stats[dir_name] = {
                "path": dir_path,
                "exists": os.path.exists(dir_path),
                "file_count": 0,
                "total_size": 0,
                "files": []
            }
            
            if os.path.exists(dir_path):
                for filename in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, filename)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        disk_stats[dir_name]["file_count"] += 1
                        disk_stats[dir_name]["total_size"] += size
                        disk_stats[dir_name]["files"].append({
                            "name": filename,
                            "size": size
                        })
                        total_disk_files += 1
                        total_disk_size += size
        
        return {
            "vector_database": vector_stats,
            "disk_storage": disk_stats,
            "summary": {
                "total_files_on_disk": total_disk_files,
                "total_disk_size_bytes": total_disk_size,
                "total_disk_size_mb": round(total_disk_size / (1024 * 1024), 2)
            }
        }
        
    except Exception as e:
        print(f"❌ Error getting detailed stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )