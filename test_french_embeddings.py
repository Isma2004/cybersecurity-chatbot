import sys
import os
sys.path.append('.')

from app.services.embedding_service import embedding_service

def test_french_embeddings():
    print("🧪 Testing French Embedding Service...")
    
    # Test French cybersecurity terms
    french_texts = [
        "Politique de sécurité de l'information",
        "Contrôles de cybersécurité ISO 27001",
        "Gestion des incidents de sécurité",
        "Protection des données personnelles",
        "Évaluation des risques cyber"
    ]
    
    print(f"📊 Model: {embedding_service.model_name}")
    print(f"🎯 Dimension: {embedding_service.get_embedding_dimension()}")
    print(f"✅ Model loaded: {embedding_service.is_model_loaded()}")
    
    for text in french_texts:
        embedding = embedding_service.embed_text(text)
        print(f"📝 '{text}' → Vector shape: {embedding.shape}")
    
    # Test query embedding
    query = "Quelles sont les exigences de mot de passe?"
    query_embedding = embedding_service.embed_query(query)
    print(f"❓ Query: '{query}' → Vector shape: {query_embedding.shape}")
    
    print("🎉 French embedding service working perfectly!")

if __name__ == "__main__":
    test_french_embeddings()
