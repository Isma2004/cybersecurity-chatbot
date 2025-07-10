# app/services/chat_session_service.py
import json
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from app.models.schemas import ChatSession, ChatMessage, SourceReference

class ChatSessionService:
    """Service to manage chat sessions and messages"""
    
    def __init__(self):
        self.sessions_dir = Path("./chat_sessions")
        self.sessions_dir.mkdir(exist_ok=True)
        self.sessions_index_file = self.sessions_dir / "sessions_index.json"
        self._load_sessions_index()
    
    def _load_sessions_index(self):
        """Load sessions index from file"""
        try:
            if self.sessions_index_file.exists():
                with open(self.sessions_index_file, 'r', encoding='utf-8') as f:
                    self.sessions_index = json.load(f)
            else:
                self.sessions_index = {}
        except Exception as e:
            print(f"Error loading sessions index: {e}")
            self.sessions_index = {}
    
    def _save_sessions_index(self):
        """Save sessions index to file"""
        try:
            with open(self.sessions_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving sessions index: {e}")
    
    def _save_session_messages(self, session_id: str, messages: List[Dict]):
        """Save messages for a session"""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving session messages: {e}")
    
    def _load_session_messages(self, session_id: str) -> List[Dict]:
        """Load messages for a session"""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading session messages: {e}")
            return []
    
    def create_session(self, title: Optional[str] = None) -> ChatSession:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        session = ChatSession(
            id=session_id,
            title=title or "Nouvelle conversation",
            created_at=now,
            updated_at=now,
            message_count=0,
            preview=None
        )
        
        # Add to index
        self.sessions_index[session_id] = {
            "id": session_id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "message_count": 0,
            "preview": None
        }
        
        self._save_sessions_index()
        self._save_session_messages(session_id, [])
        
        print(f"✅ Created new chat session: {session_id}")
        return session
    
    def get_sessions(self) -> List[ChatSession]:
        """Get all chat sessions"""
        sessions = []
        for session_data in self.sessions_index.values():
            sessions.append(ChatSession(
                id=session_data["id"],
                title=session_data["title"],
                created_at=datetime.fromisoformat(session_data["created_at"]),
                updated_at=datetime.fromisoformat(session_data["updated_at"]),
                message_count=session_data["message_count"],
                preview=session_data.get("preview")
            ))
        
        # Sort by updated_at descending (most recent first)
        sessions.sort(key=lambda x: x.updated_at, reverse=True)
        return sessions
    
    def get_session_with_messages(self, session_id: str) -> Optional[Dict]:
        """Get session with its messages"""
        if session_id not in self.sessions_index:
            return None
        
        session_data = self.sessions_index[session_id]
        session = ChatSession(
            id=session_data["id"],
            title=session_data["title"],
            created_at=datetime.fromisoformat(session_data["created_at"]),
            updated_at=datetime.fromisoformat(session_data["updated_at"]),
            message_count=session_data["message_count"],
            preview=session_data.get("preview")
        )
        
        # Load messages
        messages_data = self._load_session_messages(session_id)
        messages = []
        for msg_data in messages_data:
            # Convert sources
            sources = []
            for source_data in msg_data.get("sources", []):
                sources.append(SourceReference(**source_data))
            
            messages.append(ChatMessage(
                id=msg_data["id"],
                session_id=msg_data["session_id"],
                type=msg_data["type"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                sources=sources,
                tokens_used=msg_data.get("tokens_used"),
                processing_time=msg_data.get("processing_time")
            ))
        
        return {
            "session": session,
            "messages": messages
        }
    
    def add_message(self, session_id: str, message_type: str, content: str, 
                   sources: List[SourceReference] = None, tokens_used: int = None, 
                   processing_time: float = None) -> ChatMessage:
        """Add a message to a session"""
        if session_id not in self.sessions_index:
            raise ValueError(f"Session {session_id} not found")
        
        message_id = str(uuid.uuid4())
        now = datetime.now()
        
        message = ChatMessage(
            id=message_id,
            session_id=session_id,
            type=message_type,
            content=content,
            timestamp=now,
            sources=sources or [],
            tokens_used=tokens_used,
            processing_time=processing_time
        )
        
        # Load existing messages
        messages_data = self._load_session_messages(session_id)
        
        # Add new message
        message_dict = {
            "id": message.id,
            "session_id": message.session_id,
            "type": message.type,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "sources": [source.dict() for source in message.sources],
            "tokens_used": message.tokens_used,
            "processing_time": message.processing_time
        }
        messages_data.append(message_dict)
        
        # Update session info
        self.sessions_index[session_id]["updated_at"] = now.isoformat()
        self.sessions_index[session_id]["message_count"] = len(messages_data)
        
        # Update preview with first user message
        if message_type == "user" and not self.sessions_index[session_id].get("preview"):
            preview = content[:100] + "..." if len(content) > 100 else content
            self.sessions_index[session_id]["preview"] = preview
            
            # Auto-generate title from first message
            if self.sessions_index[session_id]["title"] == "Nouvelle conversation":
                title = content[:50] + "..." if len(content) > 50 else content
                self.sessions_index[session_id]["title"] = title
        
        # Save
        self._save_session_messages(session_id, messages_data)
        self._save_sessions_index()
        
        return message
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session"""
        if session_id not in self.sessions_index:
            return False
        
        try:
            # Remove from index
            del self.sessions_index[session_id]
            self._save_sessions_index()
            
            # Remove session file
            session_file = self.sessions_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
            
            print(f"🗑️ Deleted chat session: {session_id}")
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
    
    def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session title"""
        if session_id not in self.sessions_index:
            return False
        
        self.sessions_index[session_id]["title"] = title
        self.sessions_index[session_id]["updated_at"] = datetime.now().isoformat()
        self._save_sessions_index()
        return True

# Global instance
chat_session_service = ChatSessionService()