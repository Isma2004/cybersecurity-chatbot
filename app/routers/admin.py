# app/routers/admin.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
import os
import uuid
from datetime import datetime
from pathlib import Path

from app.models.auth_schemas import User, DocumentOwnership, AdminDashboard
from app.models.schemas import DocumentResponse, DocumentMetadata, ProcessingStatus, FileType
from app.routers.auth import require_admin
from app.routers.upload import processing_status  # Import the shared processing status
from app.services.document_processor import document_processor
from app.services.vector_service import vector_service
from app.utils.config import settings

router = APIRouter()

@router.get("/dashboard", response_model=AdminDashboard)
async def get_admin_dashboard(admin: User = Depends(require_admin)):
    """Get admin dashboard with statistics"""
    try:
        stats = vector_service.get_admin_stats()
        
        return AdminDashboard(
            total_global_documents=stats["total_global_documents"],
            total_personal_documents=stats["total_personal_documents"],
            active_users=stats["active_users"],
            total_queries_today=stats["queries_today"],
            popular_documents=stats["popular_documents"],
            recent_uploads=stats["recent_uploads"]
        )
    except Exception as e:
        print(f"❌ Error getting admin dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-global")
async def upload_global_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated tags
    admin: User = Depends(require_admin)
):
    """Upload a global document (admin only)"""
    try:
        print(f"🔍 Admin upload endpoint called")
        print(f"🔍 Admin user: {admin.username}")
        print(f"🔍 File received: {file.filename if file else 'NO FILE'}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nom de fichier manquant")
            
        if not document_processor.is_supported_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Type de fichier non supporté. Extensions autorisées: {', '.join(settings.allowed_extensions)}"
            )
        
        # Read file content
        content = await file.read()
        await file.seek(0)
        
        # Check file size
        if len(content) > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"Fichier trop volumineux. Taille maximum: {settings.max_file_size // (1024*1024)} MB"
            )
        
        # Generate document ID
        document_id = f"global_doc_{uuid.uuid4().hex[:8]}"
        
        # Ensure global docs directory exists
        os.makedirs(settings.global_docs_dir, exist_ok=True)
        
        # Save file
        file_extension = Path(file.filename).suffix
        safe_filename = f"{document_id}{file_extension}"
        file_path = os.path.join(settings.global_docs_dir, safe_filename)
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        print(f"📁 Admin uploaded global document: {file.filename} to {file_path}")
        print(f"📊 File size: {len(content)} bytes")
        
        # Initialize processing status
        processing_status[document_id] = {
            'status': ProcessingStatus.PROCESSING,
            'message': 'Traitement du document global en cours...'
        }
        
        # Process in background
        background_tasks.add_task(
            process_global_document,
            document_id,
            file_path,
            file.filename,
            admin.username,
            description,
            tags.split(",") if tags else []
        )
        
        return {
            "document_id": document_id,
            "filename": file.filename,
            "message": "Document global téléchargé avec succès. Traitement en cours...",
            "uploaded_by": admin.username,
            "ownership": "global",
            "file_path": file_path,
            "file_size": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Admin upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_global_document(
    document_id: str, 
    file_path: str, 
    filename: str,
    uploaded_by: str,
    description: Optional[str],
    tags: List[str]
):
    """Process global document in background"""
    try:
        print(f"🔄 Processing global document: {filename}")
        
        # Update status to processing
        processing_status[document_id] = {
            'status': ProcessingStatus.PROCESSING,
            'message': 'Extraction du texte en cours...'
        }
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise Exception(f"File not found: {file_path}")
        
        # Extract text
        extracted_text, metadata = document_processor.process_document(file_path, filename)
        print(f"📄 Extracted {len(extracted_text)} characters from {filename}")
        
        # Update status
        processing_status[document_id] = {
            'status': ProcessingStatus.PROCESSING,
            'message': 'Création des segments de texte...'
        }
        
        # Create chunks with global ownership
        chunks = document_processor.create_chunks(extracted_text, document_id, filename)
        print(f"📝 Created {len(chunks)} chunks for {filename}")
        
        # Update status
        processing_status[document_id] = {
            'status': ProcessingStatus.PROCESSING,
            'message': 'Ajout à la base de connaissances globale...'
        }
        
        # Add ownership metadata to each chunk
        for chunk in chunks:
            chunk.metadata.update({
                "ownership": DocumentOwnership.GLOBAL,
                "uploaded_by": uploaded_by,
                "description": description,
                "tags": tags,
                "upload_date": datetime.now().isoformat(),
                "file_path": file_path,
                "filename": filename
            })
        
        # Add to vector database with global ownership
        success = vector_service.add_document_chunks(
            chunks, 
            ownership=DocumentOwnership.GLOBAL
        )
        
        if success:
            print(f"✅ Global document processed successfully: {filename}")
            # Update status to ready
            processing_status[document_id] = {
                'status': ProcessingStatus.READY,
                'message': 'Document global prêt et ajouté à la base de connaissances',
                'metadata': {
                    'filename': filename,
                    'chunks_count': len(chunks),
                    'characters_extracted': len(extracted_text),
                    'ownership': 'global',
                    'uploaded_by': uploaded_by,
                    'description': description,
                    'tags': tags
                }
            }
        else:
            print(f"❌ Failed to process global document: {filename}")
            processing_status[document_id] = {
                'status': ProcessingStatus.ERROR,
                'message': 'Erreur lors de l\'ajout à la base de connaissances',
                'error': 'Failed to add chunks to vector database'
            }
            raise Exception("Failed to add chunks to vector database")
            
    except Exception as e:
        print(f"❌ Error processing global document {filename}: {str(e)}")
        # Update status to error
        processing_status[document_id] = {
            'status': ProcessingStatus.ERROR,
            'message': f'Erreur lors du traitement: {str(e)}',
            'error': str(e)
        }
        # Don't delete the file on error - keep it for manual investigation
        raise

@router.get("/documents/global")
async def list_global_documents(admin: User = Depends(require_admin)):
    """List all global documents"""
    try:
        # Get global documents from vector service
        global_docs = vector_service.get_documents_by_ownership(DocumentOwnership.GLOBAL)
        
        # Also check what's in the global directory
        global_files = []
        if os.path.exists(settings.global_docs_dir):
            for filename in os.listdir(settings.global_docs_dir):
                file_path = os.path.join(settings.global_docs_dir, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    global_files.append({
                        "filename": filename,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        return {
            "documents": global_docs,
            "total": len(global_docs),
            "files_on_disk": global_files,
            "global_docs_directory": settings.global_docs_dir,
            "directory_exists": os.path.exists(settings.global_docs_dir)
        }
    except Exception as e:
        print(f"❌ Error in list_global_documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/global/{document_id}")
async def delete_global_document(
    document_id: str,
    admin: User = Depends(require_admin)
):
    """Delete a global document"""
    try:
        # Remove from vector database
        success = vector_service.remove_document(document_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document non trouvé")
        
        # Remove file from disk
        files_removed = []
        if os.path.exists(settings.global_docs_dir):
            for filename in os.listdir(settings.global_docs_dir):
                if filename.startswith(document_id):
                    file_path = os.path.join(settings.global_docs_dir, filename)
                    try:
                        os.remove(file_path)
                        files_removed.append(filename)
                        print(f"🗑️ Removed file: {file_path}")
                    except Exception as e:
                        print(f"⚠️ Error removing file {file_path}: {e}")
        
        return {
            "message": f"Document global {document_id} supprimé avec succès",
            "deleted_by": admin.username,
            "files_removed": files_removed
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting global document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/documents/global/{document_id}/status")
async def toggle_document_status(
    document_id: str,
    is_active: bool,
    admin: User = Depends(require_admin)
):
    """Enable/disable a global document"""
    try:
        # This would require implementing status tracking in vector service
        # For now, return success
        return {
            "message": f"Document {document_id} {'activé' if is_active else 'désactivé'}",
            "updated_by": admin.username,
            "note": "Status tracking not fully implemented yet"
        }
        
    except Exception as e:
        print(f"❌ Error toggling document status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-upload")
async def test_upload(file: UploadFile = File(...)):
    """Test file upload without auth"""
    try:
        content = await file.read()
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "is_supported": document_processor.is_supported_file(file.filename) if file.filename else False,
            "global_docs_dir": settings.global_docs_dir,
            "directory_exists": os.path.exists(settings.global_docs_dir)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/debug/all-chunks")
async def debug_all_chunks(admin: User = Depends(require_admin)):
    """Debug: Show all chunks and their metadata"""
    try:
        # Get stats from vector service
        stats = vector_service.get_stats()
        
        # Get sample global documents
        global_chunks = []
        count = 0
        for chunk_id, chunk in vector_service.global_documents.items():
            if count < 5:  # Show first 5 for debugging
                global_chunks.append({
                    "chunk_id": chunk_id,
                    "document_id": chunk.document_id,
                    "metadata": chunk.metadata,
                    "content_preview": chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content
                })
                count += 1
        
        # Get sample regular documents
        regular_chunks = []
        count = 0
        for chunk_id, chunk in vector_service.document_store.items():
            if count < 5:  # Show first 5 for debugging
                regular_chunks.append({
                    "chunk_id": chunk_id,
                    "document_id": chunk.document_id,
                    "metadata": chunk.metadata,
                    "content_preview": chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content
                })
                count += 1
        
        return {
            "vector_service_stats": stats,
            "global_chunks_sample": global_chunks,
            "regular_chunks_sample": regular_chunks,
            "global_docs_directory": {
                "path": settings.global_docs_dir,
                "exists": os.path.exists(settings.global_docs_dir),
                "files": os.listdir(settings.global_docs_dir) if os.path.exists(settings.global_docs_dir) else []
            }
        }
    except Exception as e:
        print(f"❌ Error in debug endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity-log")
async def get_activity_log(
    limit: int = 50,
    admin: User = Depends(require_admin)
):
    """Get recent activity log"""
    try:
        # In production, this would query a real activity log
        # For now, return some sample data plus real stats
        stats = vector_service.get_stats()
        
        sample_activities = [
            {
                "timestamp": datetime.now().isoformat(),
                "user": "system",
                "action": "stats_check",
                "details": f"Total documents: {stats.get('total_documents', 0)}, Total chunks: {stats.get('total_chunks', 0)}"
            }
        ]
        
        # Add entries from vector service query log if available
        if hasattr(vector_service, 'query_log'):
            for entry in vector_service.query_log[-5:]:  # Last 5 queries
                sample_activities.append({
                    "timestamp": entry['timestamp'].isoformat(),
                    "user": entry.get('session_id', 'anonymous')[:8] if entry.get('session_id') else 'anonymous',
                    "action": "query",
                    "details": f"Query: '{entry['query'][:50]}...' - {entry['results_count']} results"
                })
        
        return {
            "activities": sample_activities[-limit:],
            "total": len(sample_activities),
            "vector_service_stats": stats
        }
    except Exception as e:
        print(f"❌ Error getting activity log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/directories")
async def debug_directories(admin: User = Depends(require_admin)):
    """Debug endpoint to check all directories"""
    try:
        directories_info = {}
        
        # Check all configured directories
        dirs_to_check = {
            "upload_dir": settings.upload_dir,
            "global_docs_dir": settings.global_docs_dir,
            "personal_docs_dir": settings.personal_docs_dir,
            "documents_dir": settings.documents_dir
        }
        
        for dir_name, dir_path in dirs_to_check.items():
            directories_info[dir_name] = {
                "path": dir_path,
                "absolute_path": os.path.abspath(dir_path),
                "exists": os.path.exists(dir_path),
                "is_directory": os.path.isdir(dir_path) if os.path.exists(dir_path) else False,
                "files": []
            }
            
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                try:
                    files = os.listdir(dir_path)
                    for filename in files:
                        file_path = os.path.join(dir_path, filename)
                        stat = os.stat(file_path)
                        directories_info[dir_name]["files"].append({
                            "name": filename,
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "is_file": os.path.isfile(file_path)
                        })
                except Exception as e:
                    directories_info[dir_name]["error"] = str(e)
        
        return {
            "current_working_directory": os.getcwd(),
            "directories": directories_info,
            "vector_service_stats": vector_service.get_stats()
        }
        
    except Exception as e:
        print(f"❌ Error in debug directories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))