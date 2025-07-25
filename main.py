from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime
from app.routers import auth, admin  # ADD THESE
from app.services.auth_service import auth_service  # ADD THIS
from app.routers import upload, documents, chat, chat_sessions

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
    title="CyberSense API - Credit Agricole du Maroc",  # UPDATE
    description="API for French cybersecurity AI assistant with multi-tenant document management",  # UPDATE
    version="2.0.0",  # UPDATE
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
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(chat_sessions.router, prefix="/api", tags=["chat-sessions"])

@app.get("/", tags=["System"])
async def root():
    """Root endpoint with system info"""
    return {
        "message": "CyberSense API - Credit Agricole du Maroc",  # UPDATE
        "status": "running",
        "version": "2.0.0",  # UPDATE
        "organization": "Credit Agricole du Maroc",  # ADD
        "docs": "/api/docs",
        "features": [  # ADD
            "Multi-tenant document management",
            "Role-based access (Admin/Employee)",
            "Global and personal document support"
        ],
        "services": {
            "document_processor": _check_service_status(document_processor),
            "vector_service": _check_service_status(vector_service),
            "chat_service": _check_service_status(chat_service),
            "auth_service": True  # ADD
        }
    }

@app.get("/api/quickstart", tags=["System"])
async def quickstart_guide():
    """Quick start guide for new users"""
    return {
        "steps": {
            "1": "Login as admin (admin/admin123) or employee (employee1/emp123)",
            "2": "Admins: Upload global documents via /api/admin/upload-global",
            "3": "Employees: Chat with global docs or upload personal docs",
            "4": "Use /api/chat with your auth token to ask questions"
        },
        "test_credentials": {
            "admin": {"username": "admin", "password": "admin123"},
            "director": {"username": "director", "password": "director123"},
            "employee": {"username": "employee1", "password": "emp123"}
        },
        "api_docs": "/api/docs",
        "anonymous_access": "Chat and upload work without login (backward compatible)"
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

@app.get("/api/diagnostic", tags=["System"])
async def comprehensive_diagnostic():
    """Comprehensive diagnostic endpoint to test all systems"""
    try:
        diagnostic_results = {
            "timestamp": datetime.now().isoformat(),
            "status": "running_diagnostics"
        }
        
        # 1. Test directory structure
        directories = {
            "upload_dir": settings.upload_dir,
            "global_docs_dir": settings.global_docs_dir,
            "personal_docs_dir": settings.personal_docs_dir,
            "documents_dir": settings.documents_dir
        }
        
        directory_status = {}
        for name, path in directories.items():
            directory_status[name] = {
                "path": path,
                "absolute_path": os.path.abspath(path),
                "exists": os.path.exists(path),
                "is_writable": os.access(path, os.W_OK) if os.path.exists(path) else False,
                "files_count": len(os.listdir(path)) if os.path.exists(path) else 0
            }
            
            # Try to create directory if it doesn't exist
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                    directory_status[name]["created"] = True
                except Exception as e:
                    directory_status[name]["creation_error"] = str(e)
        
        diagnostic_results["directories"] = directory_status
        
        # 2. Test vector service
        try:
            vector_stats = vector_service.get_stats()
            diagnostic_results["vector_service"] = {
                "status": "ok",
                "stats": vector_stats,
                "stores": {
                    "regular_documents": len(vector_service.document_store),
                    "global_documents": len(vector_service.global_documents),
                    "session_documents": len(vector_service.session_documents)
                }
            }
        except Exception as e:
            diagnostic_results["vector_service"] = {
                "status": "error",
                "error": str(e)
            }
        
        # 3. Test document processor
        try:
            processor_status = {
                "supported_extensions": settings.allowed_extensions,
                "max_file_size": settings.max_file_size,
                "ocr_available": document_processor.get_ocr_status()
            }
            diagnostic_results["document_processor"] = {
                "status": "ok",
                "details": processor_status
            }
        except Exception as e:
            diagnostic_results["document_processor"] = {
                "status": "error",
                "error": str(e)
            }
        
        # 4. Test auth service
        try:
            # Test token verification (without creating a real token)
            auth_status = {
                "users_file_exists": os.path.exists("./data/users.json"),
                "secret_key_configured": len(auth_service.secret_key) > 0
            }
            diagnostic_results["auth_service"] = {
                "status": "ok",
                "details": auth_status
            }
        except Exception as e:
            diagnostic_results["auth_service"] = {
                "status": "error",
                "error": str(e)
            }
        
        # 5. Test embedding service
        try:
            embedding_service = vector_service._get_embedding_service()
            if embedding_service:
                diagnostic_results["embedding_service"] = {
                    "status": "ok",
                    "model_loaded": embedding_service.is_model_loaded(),
                    "kaggle_available": getattr(embedding_service, 'kaggle_available', False)
                }
            else:
                diagnostic_results["embedding_service"] = {
                    "status": "not_available"
                }
        except Exception as e:
            diagnostic_results["embedding_service"] = {
                "status": "error",
                "error": str(e)
            }
        
        # 6. Test file upload simulation
        try:
            # Check if we can write a test file
            test_file_path = os.path.join(settings.upload_dir, "test_diagnostic.txt")
            with open(test_file_path, "w") as f:
                f.write("This is a test file for diagnostics")
            
            file_test = {
                "can_write": True,
                "test_file_created": os.path.exists(test_file_path)
            }
            
            # Clean up test file
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
                file_test["test_file_cleaned"] = True
            
            diagnostic_results["file_operations"] = {
                "status": "ok",
                "details": file_test
            }
        except Exception as e:
            diagnostic_results["file_operations"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Overall status
        errors = [k for k, v in diagnostic_results.items() 
                 if isinstance(v, dict) and v.get("status") == "error"]
        
        diagnostic_results["overall_status"] = "healthy" if not errors else "issues_found"
        diagnostic_results["errors_found"] = errors
        
        # Recommendations
        recommendations = []
        
        if not diagnostic_results["directories"]["global_docs_dir"]["exists"]:
            recommendations.append("Create global documents directory")
        
        if not diagnostic_results["directories"]["personal_docs_dir"]["exists"]:
            recommendations.append("Create personal documents directory")
        
        if diagnostic_results["vector_service"].get("status") == "error":
            recommendations.append("Check vector service configuration")
        
        if not diagnostic_results["embedding_service"].get("kaggle_available", False):
            recommendations.append("Configure Kaggle API for better performance")
        
        diagnostic_results["recommendations"] = recommendations
        
        return diagnostic_results
        
    except Exception as e:
        return {
            "status": "diagnostic_failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
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
    
    logger.info("🏦 CyberSense - Credit Agricole du Maroc")  # ADD
    logger.info("Starting CyberSense API...")
    logger.info("French Cybersecurity Document Assistant")
    logger.info("Multi-tenant document management enabled")  # ADD
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )
