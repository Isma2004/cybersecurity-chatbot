from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import upload, documents, chat  # Make sure chat is imported
from app.services.document_processor import document_processor
from app.services.vector_service import vector_service
from app.services.chat_service import chat_service  # Make sure chat_service is imported

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
    title="Cybersecurity Chatbot API",
    description="French RAG chatbot for cybersecurity documents",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - MAKE SURE CHAT IS INCLUDED
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(chat.router, prefix="/api", tags=["chat"])  # This must be here

@app.get("/")
async def root():
    return {
        "message": "Cybersecurity Chatbot API", 
        "status": "running",
        "services": {
            "document_processor": _check_service_status(document_processor),
            "vector_service": _check_service_status(vector_service),
            "chat_service": _check_service_status(chat_service)
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "document_processor": _check_service_status(document_processor),
            "vector_service": _check_service_status(vector_service),
            "chat_service": _check_service_status(chat_service)
        }
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
    uvicorn.run(app, host="0.0.0.0", port=8000)