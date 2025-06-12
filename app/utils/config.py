import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    # Application
    app_name: str = "Assistant IA Cybersécurité"
    app_version: str = "1.0.0"
    debug: bool = True

    use_openai: bool = os.getenv("USE_OPENAI", "true").lower() == "true"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # File Upload
    max_file_size: int = 5 * 1024 * 1024  # 50MB
    allowed_extensions: List[str] = ["pdf", "docx", "txt", "png", "jpg", "jpeg"]
    upload_dir: str = "./data/documents"
    
    # Vector Database
    vector_store_path: str = "./data/vector_store"
    faiss_index_path: str = "./data/vector_store/faiss_index"
    
    # French Language Models
    embedding_model: str = "intfloat/multilingual-e5-large"
    language_model: str = "microsoft/Phi-3-mini-4k-instruct"
    
    # RAG Settings
    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k_retrieval: int = 3
    max_tokens_generation: int = 512
    
    # Logging
    log_level: str = "INFO"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.vector_store_path).mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings()

# French system prompts for cybersecurity
FRENCH_SYSTEM_PROMPTS = {
    "cybersecurity": """
    Vous êtes un assistant IA spécialisé en cybersécurité et conformité ISO 27001.
    Répondez toujours en français professionnel et précis.
    Basez vos réponses uniquement sur les documents fournis dans le contexte.
    Citez les sections pertinentes avec précision.
    Si l'information n'est pas disponible dans le contexte, dites-le clairement.
    """,
    
    "document_analysis": """
    Analysez les documents de conformité et répondez aux questions sur :
    - Les politiques de sécurité de l'information
    - Les procédures ISO 27001
    - Les guides de cybersécurité
    - Les contrôles de sécurité
    - Les mesures de protection des données
    """
}

# ISO 27001 specific patterns for better French document chunking
ISO_27001_PATTERNS = [
    r'\n(?:Annexe|Annex)\s+[A-Z][\.\s]',
    r'\n(?:Contrôle|Control)\s+[A-Z]\.\d+',
    r'\n\d+\.\d+\s+',
    r'\n(?:Article|Section)\s+\d+',
    r'\n(?:Politique|Policy)\s+',
    r'\n(?:Procédure|Procedure)\s+',
]
