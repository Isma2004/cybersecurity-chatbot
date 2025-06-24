from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime

# Import routers
from app.routers import upload, documents, chat, chat_sessions 
# Import services
from app.services.document_processor import document_processor
from app.services.vector_service import vector_service
from app.services.chat_service import chat_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    print("🚀 Starting Cybersecurity Chatbot Backend...")
    
    # Initialize document processor
    try:
        if hasattr(document_processor, 'is_ready'):
            doc_status = "✅ Ready" if document_processor.is_ready() else "❌ Failed"
        else:
            doc_status = "✅ Ready (loaded)"
        print("📄 Document processor:", doc_status)
    except Exception as e:
        print(f"📄 Document processor: ❌ Error - {e}")
    
    # Initialize vector service
    try:
        if hasattr(vector_service, 'is_ready'):
            vec_status = "✅ Ready" if vector_service.is_ready() else "❌ Failed"
        else:
            vec_status = "✅ Ready (loaded)"
        print("🔍 Vector service:", vec_status)
    except Exception as e:
        print(f"🔍 Vector service: ❌ Error - {e}")
    
    # Initialize chat service
    try:
        if hasattr(chat_service, 'is_ready'):
            chat_status = "✅ Ready" if chat_service.is_ready() else "❌ Failed"
        else:
            chat_status = "✅ Ready (loaded)"
        print("💬 Chat service:", chat_status)
    except Exception as e:
        print(f"💬 Chat service: ❌ Error - {e}")
    
    yield
    
    print("🔥 Shutting down...")

app = FastAPI(
    title="CyberSense API - French Cybersecurity Assistant",
    description="API for French cybersecurity AI assistant with RAG capabilities",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with proper prefixes
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(chat_sessions.router, prefix="/api", tags=["chat-sessions"])

@app.get("/", tags=["System"])
async def root():
    """Root endpoint"""
    return {
        "message": "CyberSense API - French Cybersecurity Assistant", 
        "status": "running",
        "version": "1.0.0",
        "docs": "/api/docs",
        "services": {
            "document_processor": _check_service_status(document_processor),
            "vector_service": _check_service_status(vector_service),
            "chat_service": _check_service_status(chat_service)
        }
    }

@app.get("/health", tags=["System"])
@app.get("/api/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    try:
        # Get detailed service status
        services = {}
        
        # Document processor status
        try:
            services["document_processor"] = {
                "status": "ready" if _check_service_status(document_processor) else "error",
                "ocr_initialized": getattr(document_processor, 'get_ocr_status', lambda: False)()
            }
        except Exception as e:
            services["document_processor"] = {"status": "error", "error": str(e)}
        
        # Vector service status
        try:
            vector_stats = vector_service.get_stats()
            services["vector_service"] = {
                "status": vector_stats.get("status", "unknown"),
                "total_vectors": vector_stats.get("total_vectors", 0),
                "total_documents": vector_stats.get("total_documents", 0)
            }
        except Exception as e:
            services["vector_service"] = {"status": "error", "error": str(e)}
        
        # Chat service status
        try:
            chat_status = chat_service.get_model_status()
            services["chat_service"] = chat_status
        except Exception as e:
            services["chat_service"] = {"status": "error", "error": str(e)}
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "services": services
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

def _check_service_status(service):
    """Helper function to check service status safely"""
    try:
        if hasattr(service, 'is_ready'):
            return service.is_ready()
        else:
            return True
    except Exception:
        return False

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting CyberSense API...")
    logger.info("French Cybersecurity Document Assistant")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )