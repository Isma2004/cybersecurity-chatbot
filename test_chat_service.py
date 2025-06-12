import sys
import psutil
sys.path.append('.')

def test_chat_service():

    print("🧪 Testing French Chat Service...")
    
    # Import after memory check
    from app.services.chat_service import chat_service
    from app.services.vector_service import vector_service
    from app.models.schemas import ChatRequest, DocumentChunk
    
    # Check model status
    status = chat_service.get_model_status()
    print(f"�� Model status: {status}")
    
    if not chat_service.is_ready():
        print("⚠️ Chat model not ready, using fallback responses")
    
    # Make sure we have some data in the vector database
    # Add sample chunks if database is empty
    if vector_service.get_stats()['total_vectors'] == 0:
        print("📄 Adding sample cybersecurity data...")
        
        sample_chunks = [
            DocumentChunk(
                chunk_id="security_policy_chunk_0",
                document_id="security_policy",
                content="Politique de Sécurité des Mots de Passe: Les mots de passe doivent contenir au minimum 12 caractères incluant des majuscules, minuscules, chiffres et caractères spéciaux. Le renouvellement est obligatoire tous les 90 jours pour les comptes administrateurs et tous les 180 jours pour les utilisateurs standard.",
                chunk_index=0,
                metadata={'filename': 'politique_securite.pdf'}
            ),
            DocumentChunk(
                chunk_id="incident_procedure_chunk_0", 
                document_id="incident_procedure",
                content="Procédure de Signalement d'Incidents: Tout incident de sécurité doit être signalé dans les 30 minutes via le portail SOC ou par téléphone au 2456. Les incidents incluent: tentatives d'intrusion, malware détecté, accès non autorisé, fuite de données. L'équipe de réponse intervient sous 1 heure.",
                chunk_index=0,
                metadata={'filename': 'procedure_incidents.docx'}
            ),
            DocumentChunk(
                chunk_id="access_control_chunk_0",
                document_id="access_control", 
                content="Contrôles d'Accès ISO 27001: L'authentification multi-facteurs (MFA) est obligatoire pour tous les comptes privilégiés. Les droits d'accès sont révisés trimestriellement. Les comptes inactifs sont automatiquement désactivés après 30 jours. Seuls les administrateurs autorisés peuvent créer de nouveaux comptes utilisateurs.",
                chunk_index=0,
                metadata={'filename': 'controles_acces.pdf'}
            )
        ]
        
        vector_service.add_document_chunks(sample_chunks)
        print("✅ Sample data added to vector database")
    
    # Test various French cybersecurity questions
    test_questions = [
        "Quelles sont les exigences de mot de passe?",
        "Comment signaler un incident de sécurité?",
        "Qu'est-ce que l'authentification multi-facteurs?",
        "Combien de temps pour répondre aux incidents?",
        "Qui peut créer des comptes utilisateurs?",
        "Quelle est la fréquence de révision des accès?"
    ]
    
    print(f"\n💬 Testing {len(test_questions)} cybersecurity questions...")
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- Question {i}/{len(test_questions)} ---")
        print(f"❓ Question: {question}")
        
        # Create chat request
        request = ChatRequest(
            message=question,
            max_tokens=300,
            temperature=0.7
        )
        
        # Get response
        response = chat_service.chat(request)
        
        print(f"⏱️ Processing time: {response.processing_time:.2f}s")
        print(f"📝 Response length: {len(response.response)} characters")
        print(f"📚 Sources found: {len(response.sources)}")
        
        # Show the response
        print(f"🤖 Response: {response.response[:200]}...")
        
        # Show top source
        if response.sources:
            top_source = response.sources[0]
            print(f"📄 Top source: {top_source.document_id} (score: {top_source.relevance_score:.3f})")
    
    print(f"\n🎉 Chat service testing completed!")
    
    # Final statistics
    final_stats = vector_service.get_stats()
    chat_status = chat_service.get_model_status()
    
    print(f"\n📊 Final Statistics:")
    print(f"   Vector Database: {final_stats['total_vectors']} vectors")
    print(f"   Chat Model: {chat_status['status']}")
    print(f"   Device: {chat_status['device']}")

if __name__ == "__main__":
    test_chat_service()
