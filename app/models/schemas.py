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
    """Chat request - using 'message' for compatibility with working version"""
    message: str  # Changed from 'question' to 'message' for compatibility
    context: Optional[str] = None  # Keep for backward compatibility
    document_ids: Optional[List[str]] = None
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    
    # Support both 'message' and 'question' for flexibility
    @property
    def question(self) -> str:
        """Alias for message to support both interfaces"""
        return self.message

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


class ChatSession(BaseModel):
    """Chat session model"""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    preview: Optional[str] = None  # First user message preview

class ChatMessage(BaseModel):
    """Chat message model"""
    id: str
    session_id: str
    type: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    sources: List[SourceReference] = []
    tokens_used: Optional[int] = None
    processing_time: Optional[float] = None

class CreateChatRequest(BaseModel):
    """Request to create a new chat"""
    title: Optional[str] = None

class ChatMessageRequest(BaseModel):
    """Request to send a message to a chat"""
    message: str
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7

class ChatSessionResponse(BaseModel):
    """Response with chat session and messages"""
    session: ChatSession
    messages: List[ChatMessage]

class ChatListResponse(BaseModel):
    """Response with list of chat sessions"""
    sessions: List[ChatSession]
    total: int