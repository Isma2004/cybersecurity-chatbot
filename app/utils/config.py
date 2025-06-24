"""
Configuration settings for the application
"""
import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    """Application settings with proper field definitions"""
    
    # Paths
    upload_dir: str = Field(default="./uploads")
    vector_db_path: str = Field(default="./data/vector_store")
    
    # File upload settings
    max_file_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    allowed_extensions: List[str] = Field(default=["pdf", "docx", "doc", "txt", "png", "jpg", "jpeg"])
    
    # Text processing
    chunk_size: int = Field(default=800)
    chunk_overlap: int = Field(default=150)
    
    # Embedding model
    embedding_model: str = Field(default="intfloat/multilingual-e5-base")
    
    # RAG settings
    top_k_retrieval: int = Field(default=3)
    max_tokens_generation: int = Field(default=512)
    
    # OpenAI Configuration
    use_openai: bool = Field(default=False)
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-3.5-turbo")
    
    # Kaggle Configuration
    use_kaggle: bool = Field(default=False)
    kaggle_api_url: str = Field(default="")
    kaggle_api_key: str = Field(default="")
    
    # For local LLM (if needed)
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama2")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Allow extra fields from .env that aren't defined
        extra = "ignore"

# French system prompts for better responses
FRENCH_SYSTEM_PROMPTS = {
    "cybersecurity": """Tu es un assistant expert en cybersécurité et conformité ISO 27001.

Règles importantes:
1. Réponds TOUJOURS en français professionnel
2. Base tes réponses UNIQUEMENT sur le contexte fourni
3. Si l'information n'est pas dans le contexte, dis-le clairement
4. Cite le document source quand c'est pertinent
5. Sois précis et concis"""
}

# Initialize settings
settings = Settings()

# Create necessary directories
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.vector_db_path, exist_ok=True)

# Print configuration summary
print(f"⚙️ Configuration loaded:")
print(f"   📁 Upload dir: {settings.upload_dir}")
print(f"   🧮 Embedding model: {settings.embedding_model}")
print(f"   📊 Chunk size: {settings.chunk_size}")
print(f"   🎯 Top-K retrieval: {settings.top_k_retrieval}")