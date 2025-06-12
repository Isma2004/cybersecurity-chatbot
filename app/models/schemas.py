from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    IMAGE = "image"

class ProcessingStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

class DocumentChunk(BaseModel):
    """Individual chunk of a processed document"""
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: Dict[str, Any] = {}

class DocumentMetadata(BaseModel):
    filename: str
    file_type: FileType
    file_size: int
    upload_date: datetime
    processing_status: ProcessingStatus
    text_length: Optional[int] = None
    chunk_count: Optional[int] = None
    error_message: Optional[str] = None

class DocumentResponse(BaseModel):
    document_id: str
    metadata: DocumentMetadata
    message: str

class ChatRequest(BaseModel):
    message: str
    document_ids: Optional[List[str]] = None
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7

class SourceReference(BaseModel):
    document_id: str
    document_name: str
    chunk_content: str
    relevance_score: float
    page_number: Optional[int] = None
    section: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sources: List[SourceReference]
    processing_time: float
    tokens_used: Optional[int] = None

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str
    models_loaded: Dict[str, bool]
