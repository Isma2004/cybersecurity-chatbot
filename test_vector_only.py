import sys
sys.path.append('.')

from app.services.vector_service import vector_service
from app.models.schemas import DocumentChunk

def test_vector_service_only():
    print("🧪 Testing FAISS Vector Service (No OCR)...")
    
    # Get initial stats
    stats = vector_service.get_stats()
    print(f"📊 Initial stats: {stats}")
    
    # Create sample chunks manually (no document processing)
    sample_chunks = [
        DocumentChunk(
            chunk_id="policy_001_chunk_0",
            document_id="policy_001",
            content="Politique de Sécurité de l'Information. Cette politique établit les règles de sécurité informatique pour protéger les données de l'organisation. Elle s'applique à tous les employés et définit les responsabilités en matière de cybersécurité.",
            chunk_index=0,
            metadata={'filename': 'policy_001.pdf', 'chunk_length': 245}
        ),
        DocumentChunk(
            chunk_id="policy_001_chunk_1", 
            document_id="policy_001",
            content="Gestion des mots de passe. Les mots de passe doivent comporter au minimum 12 caractères avec majuscules, minuscules, chiffres et symboles. Le renouvellement est obligatoire tous les 90 jours pour les comptes administrateurs.",
            chunk_index=1,
            metadata={'filename': 'policy_001.pdf', 'chunk_length': 198}
        ),
        DocumentChunk(
            chunk_id="incident_002_chunk_0",
            document_id="incident_002", 
            content="Procédure de Gestion des Incidents de Sécurité. Tout incident de sécurité doit être signalé immédiatement à l'équipe SOC via le portail interne. Les types d'incidents incluent: tentatives d'intrusion, malware, fuite de données.",
            chunk_index=0,
            metadata={'filename': 'incident_002.docx', 'chunk_length': 221}
        ),
        DocumentChunk(
            chunk_id="incident_002_chunk_1",
            document_id="incident_002",
            content="Réponse et Confinement des incidents. L'équipe de réponse aux incidents doit intervenir dans les 30 minutes suivant la détection. Les mesures de confinement incluent l'isolation des systèmes affectés et la préservation des preuves.",
            chunk_index=1,
            metadata={'filename': 'incident_002.docx', 'chunk_length': 235}
        )
    ]
    
    print(f"\n📄 Adding {len(sample_chunks)} chunks to vector database...")
    
    # Add chunks to vector database
    success = vector_service.add_document_chunks(sample_chunks)
    print(f"   {'✅' if success else '❌'} Added to vector database")
    
    # Get updated stats
    stats = vector_service.get_stats()
    print(f"\n📊 Updated stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Test search queries
    test_queries = [
        "Quelles sont les exigences de mot de passe?",
        "Comment signaler un incident de sécurité?", 
        "Quel est le délai de réponse aux incidents?",
        "Qui doit appliquer cette politique de sécurité?"
    ]
    
    print(f"\n🔍 Testing search queries...")
    for query in test_queries:
        print(f"\n❓ Query: '{query}'")
        results = vector_service.search_similar_chunks(query, top_k=2)
        
        if results:
            for i, result in enumerate(results):
                print(f"   {i+1}. Score: {result.relevance_score:.3f}")
                print(f"      Document: {result.document_id}")
                print(f"      Content: {result.chunk_content[:80]}...")
        else:
            print("   ❌ No results found")
    
    print(f"\n🎉 Vector service testing completed successfully!")
    final_stats = vector_service.get_stats()
    print(f"📈 Final database size: {final_stats['total_vectors']} vectors")

if __name__ == "__main__":
    test_vector_service_only()
