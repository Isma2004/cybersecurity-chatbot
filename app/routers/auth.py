# app/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid

from app.models.auth_schemas import LoginRequest, Token, User
from app.services.auth_service import auth_service

router = APIRouter()
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get current user from token"""
    token = credentials.credentials
    user = auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )
    
    return user

def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to require admin role"""
    user = get_current_user(credentials)
    
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    return user

@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """Login endpoint for both admin and employees"""
    user = auth_service.authenticate_user(request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Nom d'utilisateur ou mot de passe incorrect"
        )
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Create access token
    access_token = auth_service.create_access_token(user, session_id)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        username=user.username,
        session_id=session_id
    )

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.get("/verify-admin")
async def verify_admin_access(current_user: User = Depends(require_admin)):
    """Verify admin access"""
    return {
        "status": "authorized",
        "user": current_user.username,
        "role": current_user.role
    }