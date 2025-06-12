import sys
sys.path.append('.')

from app.services.vector_service import vector_service
from app.services.document_processor import document_processor

def test_vector_service():
    print("🧪 Testing FAISS Vector Service...")
    
    # Get initial stats
    stats = vector_service.get_stats()
    print(f"📊 Initial stats: {stats}")
    
    # Create sample French cybersecurity documents
    sample_documents = [
        {
            "id": "policy_001",
            "text": """
            Politique de Sécurité de l'Information
            
            Article 1: Objectifs
            Cette politique établit les règles de sécurité informatique pour protéger les données de l'organisation.
            Elle s'applique à tous les employés et définit les responsabilités en matière de cybersécurité.
            
            Article 2: Gestion des mots de passe
            Les mots de passe doivent comporter au minimum 12 caractères avec majuscules, minuscules, chiffres et symboles.
            Le renouvellement est obligatoire tous les 90 jours pour les comptes administrateurs.
            """
        },
        {
            "id": "procedure_002", 
            "text": """
            Procédure de Gestion des Incidents de Sécurité
            
            Section 1: Détection et Signalement
            Tout incident de sécurité doit être signalé immédiatement à l'équipe SOC via le portail interne.
            Les types d'incidents incluent: tentatives d'intrusion, malware, fuite de données, accès non autorisé.
            
            Section 2: Réponse et Confinement
            L'équipe de réponse aux incidents doit intervenir dans les 30 minutes suivant la détection.
            Les mesures de confinement incluent l'isolation des systèmes affectés et la préservation des preuves.
            """
        }
    ]
    
    # Process documents and add to vector database
    for doc in sample_documents:
        print(f"\n📄 Processing document: {doc['id']}")
        
        # Create chunks using our document processor
        chunks = document_processor.create_chunks(doc['text'], doc['id'])
        
        # Add chunks to vector database
        success = vector_service.add_document_chunks(chunks)
        print(f"   {'✅' if success else '❌'} Added to vector database")
    
    # Get updated stats
    stats = vector_service.get_stats()
    print(f"\n📊 Updated stats: {stats}")
    
    # Test search queries
    test_queries = [
        "Quelles sont les exigences de mot de passe?",
        "Comment signaler un incident de sécurité?", 
        "Qui est responsable de la cybersécurité?",
        "Quel est le délai de réponse aux incidents?"
    ]
    
    print(f"\n🔍 Testing search queries...")
    for query in test_queries:
        print(f"\n❓ Query: '{query}'")
        results = vector_service.search_similar_chunks(query, top_k=2)
        
        for i, result in enumerate(results):
            print(f"   {i+1}. Score: {result.relevance_score:.3f}")
            print(f"      Document: {result.document_id}")
            print(f"      Content: {result.chunk_content[:100]}...")
    
    print(f"\n🎉 Vector service testing completed!")
    print(f"📈 Final stats: {vector_service.get_stats()}")

if __name__ == "__main__":
    test_vector_service()
