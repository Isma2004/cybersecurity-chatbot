# app/services/auth_service.py
import os
import jwt
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path

# Try to import bcrypt, fallback to simple hashing if not available
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    print("⚠️ bcrypt not installed. Using simple hashing (NOT FOR PRODUCTION!)")
    print("   Install with: pip install bcrypt")
    BCRYPT_AVAILABLE = False
    import hashlib

from app.models.auth_schemas import User, UserRole, Token

class AuthService:
    """Simple authentication service for demo purposes"""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "credit-agricole-maroc-cybersense-2024")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 480  # 8 hours
        
        # User database (in production, use real database)
        self.users_file = Path("./data/users.json")
        self.users_file.parent.mkdir(exist_ok=True)
        self._init_default_users()
    
    def _init_default_users(self):
        """Initialize with default admin and test users"""
        if not self.users_file.exists():
            default_users = {
                "admin": {
                    "username": "admin",
                    "password": self._hash_password("admin123"),
                    "role": "admin",
                    "full_name": "Administrateur Cybersécurité",
                    "department": "DSI - Sécurité"
                },
                "director": {
                    "username": "director",
                    "password": self._hash_password("director123"),
                    "role": "admin",
                    "full_name": "Directeur Sécurité",
                    "department": "Direction"
                },
                "employee1": {
                    "username": "employee1",
                    "password": self._hash_password("emp123"),
                    "role": "employee",
                    "full_name": "Ahmed Benali",
                    "department": "IT Support"
                },
                "employee2": {
                    "username": "employee2",
                    "password": self._hash_password("emp123"),
                    "role": "employee",
                    "full_name": "Fatima Zahra",
                    "department": "Risk Management"
                }
            }
            
            with open(self.users_file, 'w') as f:
                json.dump(default_users, f, indent=2)
            
            print("✅ Default users created:")
            print("   Admin: admin/admin123")
            print("   Director: director/director123")
            print("   Employee: employee1/emp123")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt or fallback"""
        if BCRYPT_AVAILABLE:
            return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        else:
            # Simple SHA256 hash (NOT SECURE - only for development)
            return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        if BCRYPT_AVAILABLE:
            # Handle both bcrypt hashes and simple hashes
            if hashed_password.startswith('$2'):  # bcrypt hash
                return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
            else:  # fallback hash
                return hashlib.sha256(plain_password.encode('utf-8')).hexdigest() == hashed_password
        else:
            # Simple hash comparison
            return hashlib.sha256(plain_password.encode('utf-8')).hexdigest() == hashed_password
    
    def _load_users(self) -> Dict:
        """Load users from file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user and return user object"""
        users = self._load_users()
        
        if username not in users:
            return None
        
        user_data = users[username]
        if not self._verify_password(password, user_data["password"]):
            return None
        
        return User(
            username=username,
            role=UserRole(user_data["role"]),
            full_name=user_data.get("full_name"),
            department=user_data.get("department")
        )
    
    def create_access_token(self, user: User, session_id: str) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode = {
            "sub": user.username,
            "role": user.role,
            "session_id": session_id,
            "exp": expire
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from token"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        users = self._load_users()
        username = payload.get("sub")
        
        if username not in users:
            return None
        
        user_data = users[username]
        return User(
            username=username,
            role=UserRole(user_data["role"]),
            full_name=user_data.get("full_name"),
            department=user_data.get("department")
        )
    
    def is_admin(self, token: str) -> bool:
        """Check if token belongs to admin"""
        payload = self.verify_token(token)
        return payload and payload.get("role") == UserRole.ADMIN

# Global instance
auth_service = AuthService()
