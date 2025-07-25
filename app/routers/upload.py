import os
import uuid
import asyncio
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from datetime import datetime

from app.models.schemas import DocumentResponse, DocumentMetadata, ProcessingStatus, FileType
from app.services.document_processor import document_processor
from app.services.vector_service import vector_service
from app.utils.config import settings
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.schemas import DocumentOwnership
from app.services.auth_service import auth_service

router = APIRouter()
security = HTTPBearer(auto_error=False)

# Store for tracking document processing status
processing_status: dict = {}

def get_storage_directory(ownership: DocumentOwnership) -> str:
    """Get the appropriate storage directory based on ownership"""
    if ownership == DocumentOwnership.GLOBAL:
        return settings.global_docs_dir
    elif ownership == DocumentOwnership.PERSONAL:
        return settings.personal_docs_dir
    else:
        return settings.upload_dir

async def process_document_background(
    document_id: str, 
    file_path: str, 
    filename: str,
    ownership: DocumentOwnership = DocumentOwnership.PERSONAL,
    session_id: Optional[str] = None,
    username: str = "anonymous"
):
    """Background task to process uploaded document"""
    try:
        print(f"🔄 Processing {filename} ({ownership.value} document)")
        
        # Update status to processing
        processing_status[document_id] = {
            'status': ProcessingStatus.PROCESSING,
            'message': 'Extraction du texte en cours...'
        }
        
        # Extract text from document
        extracted_text, metadata = document_processor.process_document(file_path, filename)
        
        # Update status
        processing_status[document_id] = {
            'status': ProcessingStatus.PROCESSING,
            'message': 'Création des chunks et embeddings...'
        }
        
        # Create chunks
        chunks = document_processor.create_chunks(extracted_text, document_id, filename)
        
        # Add metadata to chunks
        for chunk in chunks:
            chunk.metadata.update({
                "ownership": ownership,
                "uploaded_by": username,
                "session_id": session_id,
                "upload_date": datetime.now().isoformat(),
                "filename": filename,  # Original filename
                "file_extension": Path(filename).suffix  # Store file extension for deletion
            })
        
        # Add to vector database with ownership
        if ownership == DocumentOwnership.PERSONAL and session_id:
            success = vector_service.add_document_chunks(
                chunks, 
                ownership=ownership,
                session_id=session_id
            )
        elif ownership == DocumentOwnership.GLOBAL:
            success = vector_service.add_document_chunks(
                chunks,
                ownership=ownership
            )
        else:
            # Backward compatibility - add normally
            success = vector_service.add_document_chunks(chunks)
        
        if success:
            # Move file to permanent storage instead of deleting
            permanent_dir = get_storage_directory(ownership)
            os.makedirs(permanent_dir, exist_ok=True)
            
            file_extension = Path(filename).suffix
            permanent_filename = f"{document_id}{file_extension}"
            permanent_path = os.path.join(permanent_dir, permanent_filename)
            
            # Move file to permanent location
            if os.path.exists(file_path) and file_path != permanent_path:
                os.rename(file_path, permanent_path)
                print(f"📁 Moved file to permanent storage: {permanent_path}")
            
            processing_status[document_id] = {
                'status': ProcessingStatus.READY,
                'message': 'Document traité avec succès',
                'metadata': {
                    'text_length': len(extracted_text),
                    'chunks_created': len(chunks),
                    'ownership': ownership.value,
                    'stored_at': permanent_path
                }
            }
            print(f"✅ Successfully processed {filename}")
        else:
            raise Exception("Failed to add chunks to vector database")
            
    except Exception as e:
        print(f"❌ Error processing {filename}: {str(e)}")
        processing_status[document_id] = {
            'status': ProcessingStatus.ERROR,
            'message': f'Erreur de traitement: {str(e)}',
            'error': str(e)
        }
        
        # Clean up the uploaded file only on error
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️ Cleaned up temporary file after error: {file_path}")
        except Exception as cleanup_error:
            print(f"⚠️ Error cleaning up file {file_path}: {cleanup_error}")

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Upload and process a document
    - With auth: Document is personal (session-based)
    - Without auth: Document is stored normally (backward compatibility)
    """
    try:
        # Check authentication
        session_id = None
        username = "anonymous"
        ownership = DocumentOwnership.PERSONAL  # Default for backward compatibility
        
        if credentials:
            token = credentials.credentials
            payload = auth_service.verify_token(token)
            if payload:
                session_id = payload.get("session_id")
                username = payload.get("sub")
                ownership = DocumentOwnership.PERSONAL
                print(f"👤 Authenticated upload by {username} (session: {session_id[:8] if session_id else 'None'})")
        else:
            print("👤 Anonymous upload (backward compatibility)")

        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nom de fichier manquant")
        
        # Check file type
        if not document_processor.is_supported_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"Type de fichier non supporté. Extensions autorisées: {', '.join(settings.allowed_extensions)}"
            )
        
        # Check file size by reading content
        content = await file.read()
        await file.seek(0)  # Reset file pointer
        
        if len(content) > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"Fichier trop volumineux. Taille maximum: {settings.max_file_size // (1024*1024)} MB"
            )
        
        # Generate unique document ID
        if ownership == DocumentOwnership.PERSONAL and session_id:
            document_id = f"personal_{session_id[:8]}_{uuid.uuid4().hex[:8]}"
        else:
            document_id = f"doc_{uuid.uuid4().hex[:8]}"
        
        # Determine storage directory
        if ownership == DocumentOwnership.PERSONAL and session_id:
            storage_dir = settings.personal_docs_dir
        else:
            storage_dir = settings.upload_dir  # Temporary storage for processing
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
        
        # Save file to temporary/processing location
        file_extension = Path(file.filename).suffix
        safe_filename = f"{document_id}{file_extension}"
        file_path = os.path.join(storage_dir, safe_filename)
        
        # Write file content
        with open(file_path, "wb") as f:
            f.write(content)
        
        print(f"📁 Saved file to: {file_path}")
        print(f"📊 File size: {len(content)} bytes")
        print(f"🏷️ Ownership: {ownership.value}")
        
        # Create initial metadata
        file_type = document_processor.detect_file_type(file.filename)
        metadata = DocumentMetadata(
            filename=file.filename,
            file_type=file_type,
            file_size=len(content),
            upload_date=datetime.now(),
            processing_status=ProcessingStatus.PROCESSING
        )
        
        # Initialize processing status
        processing_status[document_id] = {
            'status': ProcessingStatus.PROCESSING,
            'message': 'Fichier téléchargé, traitement en cours...',
            'metadata': {
                'filename': file.filename,
                'file_size': len(content),
                'ownership': ownership.value,
                'uploaded_by': username
            }
        }
        
        # Start background processing
        background_tasks.add_task(
            process_document_background,
            document_id,
            file_path,
            file.filename,
            ownership,
            session_id,
            username
        )
        
        response_message = f"Document '{file.filename}' téléchargé avec succès. Traitement en cours..."
        if ownership == DocumentOwnership.PERSONAL and session_id:
            response_message += f" (Document personnel - Session: {session_id[:8]})"
        
        return DocumentResponse(
            document_id=document_id,
            metadata=metadata,
            message=response_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/upload/status/{document_id}")
async def get_processing_status(document_id: str):
    """Get the processing status of an uploaded document"""
    
    if document_id not in processing_status:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    status_info = processing_status[document_id]
    
    return {
        "document_id": document_id,
        "status": status_info['status'],
        "message": status_info['message'],
        "metadata": status_info.get('metadata', {}),
        "error": status_info.get('error')
    }

@router.get("/upload/supported-types")
async def get_supported_file_types():
    """Get list of supported file types"""
    return {
        "supported_extensions": settings.allowed_extensions,
        "max_file_size_mb": settings.max_file_size // (1024 * 1024),
        "supported_types": {
            "pdf": "Documents PDF",
            "docx": "Documents Word", 
            "txt": "Fichiers texte",
            "png": "Images PNG (OCR français)",
            "jpg": "Images JPEG (OCR français)",
            "jpeg": "Images JPEG (OCR français)"
        },
        "features": [
            "Traitement de texte français optimisé",
            "OCR pour images avec support français/anglais",
            "Chunking intelligent pour documents de cybersécurité",
            "Support des tableaux Word",
            "Extraction de texte multi-pages PDF",
            "Support multi-tenant (documents personnels et globaux)"
        ]
    }

@router.post("/test-upload-simple")
async def test_upload_simple(file: UploadFile = File(...)):
    """Minimal test endpoint"""
    try:
        content = await file.read()
        return {
            "status": "received",
            "filename": file.filename,
            "size": len(content),
            "content_type": file.content_type,
            "is_supported": document_processor.is_supported_file(file.filename) if file.filename else False
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/upload/directories")
async def get_upload_directories():
    """Debug endpoint to check directory structure"""
    try:
        directories = {
            "upload_dir": {
                "path": settings.upload_dir,
                "exists": os.path.exists(settings.upload_dir),
                "files": os.listdir(settings.upload_dir) if os.path.exists(settings.upload_dir) else []
            },
            "global_docs_dir": {
                "path": settings.global_docs_dir,
                "exists": os.path.exists(settings.global_docs_dir),
                "files": os.listdir(settings.global_docs_dir) if os.path.exists(settings.global_docs_dir) else []
            },
            "personal_docs_dir": {
                "path": settings.personal_docs_dir,
                "exists": os.path.exists(settings.personal_docs_dir),
                "files": os.listdir(settings.personal_docs_dir) if os.path.exists(settings.personal_docs_dir) else []
            }
        }
        
        return {
            "directories": directories,
            "current_working_directory": os.getcwd(),
            "vector_service_stats": vector_service.get_stats()
        }
    except Exception as e:
        return {
            "error": str(e),
            "current_working_directory": os.getcwd()
        }