# app/models/auth_schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"

class DocumentOwnership(str, Enum):
    GLOBAL = "global"  # Admin-uploaded, available to all
    PERSONAL = "personal"  # User-uploaded, session-specific

class User(BaseModel):
    """User model"""
    username: str
    role: UserRole
    full_name: Optional[str] = None
    department: Optional[str] = None

class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str

class Token(BaseModel):
    """JWT token response model"""
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    session_id: str

class PopularDocument(BaseModel):
    """Popular document statistics"""
    document_id: str
    filename: str
    query_count: int
    last_accessed: datetime

class RecentUpload(BaseModel):
    """Recent upload information"""
    document_id: str
    filename: str
    uploaded_by: str
    upload_date: datetime
    file_size: int

class AdminDashboard(BaseModel):
    """Admin dashboard data model"""
    total_global_documents: int
    total_personal_documents: int
    active_users: int
    total_queries_today: int
    popular_documents: List[PopularDocument] = []
    recent_uploads: List[RecentUpload] = []