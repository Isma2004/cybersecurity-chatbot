import os
import uuid
import asyncio
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from datetime import datetime

from app.models.schemas import DocumentResponse, DocumentMetadata, ProcessingStatus, FileType
from app.services.document_processor import document_processor
from app.services.vector_service import vector_service
from app.utils.config import settings

router = APIRouter()

# Store for tracking document processing status
processing_status: dict = {}

async def process_document_background(document_id: str, file_path: str, filename: str):
    """Background task to process uploaded document"""
    try:
        print(f"🔄 Starting background processing for {filename}")
        
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
        
        if not chunks:
            raise Exception("Aucun chunk créé - le document pourrait être vide")
        
        # Add to vector database
        success = vector_service.add_document_chunks(chunks)
        
        if success:
            # Update final status
            processing_status[document_id] = {
                'status': ProcessingStatus.READY,
                'message': 'Document traité avec succès',
                'metadata': {
                    **metadata,
                    'chunk_count': len(chunks),
                    'processing_complete': True
                }
            }
            print(f"✅ Successfully processed {filename} - {len(chunks)} chunks created")
        else:
            raise Exception("Échec de l'ajout des chunks à la base de données vectorielle")
            
    except Exception as e:
        print(f"❌ Error processing {filename}: {str(e)}")
        processing_status[document_id] = {
            'status': ProcessingStatus.ERROR,
            'message': f'Erreur de traitement: {str(e)}',
            'error': str(e)
        }
    finally:
        # Clean up the uploaded file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️ Cleaned up temporary file: {file_path}")
        except Exception as cleanup_error:
            print(f"⚠️ Error cleaning up file {file_path}: {cleanup_error}")

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload and process a cybersecurity document
    
    Supports: PDF, DOCX, TXT, and images (PNG, JPG, JPEG) with French OCR
    """
    try:
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
        document_id = f"doc_{uuid.uuid4().hex[:8]}"
        
        # Save file to disk
        file_extension = Path(file.filename).suffix
        safe_filename = f"{document_id}{file_extension}"
        file_path = os.path.join(settings.upload_dir, safe_filename)
        
        # Ensure upload directory exists
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        # Write file content
        with open(file_path, "wb") as f:
            f.write(content)
        
        print(f"📁 Saved file to: {file_path}")
        
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
            'message': 'Fichier téléchargé, traitement en cours...'
        }
        
        # Start background processing
        background_tasks.add_task(
            process_document_background,
            document_id,
            file_path,
            file.filename
        )
        
        print(f"📁 Uploaded {file.filename} → Document ID: {document_id}")
        
        return DocumentResponse(
            document_id=document_id,
            metadata=metadata,
            message=f"Document '{file.filename}' téléchargé avec succès. Traitement en cours..."
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
            "Extraction de texte multi-pages PDF"
        ]
    }