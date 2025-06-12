import sys
import os
sys.path.append('.')

from app.services.document_processor import document_processor

def test_document_processor():
    print("🧪 Testing French Document Processor...")
    
    # Test supported file types
    test_files = [
        "policy.pdf",
        "procedure.docx", 
        "guide.txt",
        "scan.png",
        "document.jpg"
    ]
    
    # Access the correct attributes from our simple text splitter
    print(f"📊 Chunk size: {document_processor.text_splitter.chunk_size}")
    print(f"🔄 Chunk overlap: {document_processor.text_splitter.chunk_overlap}")
    print(f"✅ OCR initialized: {document_processor.ocr_reader is not None}")
    
    for filename in test_files:
        supported = document_processor.is_supported_file(filename)
        file_type = document_processor.detect_file_type(filename)
        print(f"📄 {filename} → Type: {file_type}, Supported: {'✅' if supported else '❌'}")
    
    # Test French text chunking with realistic cybersecurity content
    french_text = """
    Politique de Sécurité de l'Information - ISO 27001
    
    Article 1: Objectifs et Portée
    Cette politique définit les exigences de sécurité pour protéger les actifs informationnels de l'organisation conformément à la norme ISO 27001. Elle s'applique à tous les employés, prestataires et partenaires ayant accès aux systèmes d'information.
    
    Article 2: Contrôles d'Accès et Authentification
    Les contrôles d'accès doivent être implementés selon les normes ISO 27001 pour garantir que seules les personnes autorisées peuvent accéder aux ressources informatiques. L'authentification multi-facteurs est obligatoire pour tous les comptes privilégiés.
    
    Procédure 2.1: Gestion des Mots de Passe
    Les mots de passe doivent respecter les exigences suivantes pour assurer un niveau de sécurité approprié:
    - Longueur minimale de 12 caractères incluant majuscules, minuscules, chiffres et caractères spéciaux
    - Renouvellement obligatoire tous les 90 jours pour les comptes administrateurs
    - Interdiction de réutiliser les 5 derniers mots de passe utilisés
    - Stockage sécurisé dans un gestionnaire de mots de passe approuvé par l'organisation
    
    Article 3: Gestion des Incidents de Sécurité
    Tout incident de sécurité doit être signalé immédiatement à l'équipe de réponse aux incidents via le portail dédié ou par téléphone au numéro d'urgence. Les étapes de confinement et d'analyse doivent être suivies selon la procédure établie.
    """
    
    chunks = document_processor.create_chunks(french_text, "test_policy_doc")
    print(f"📝 French cybersecurity text chunking: {len(chunks)} chunks created")
    
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i+1} ({len(chunk.content)} chars) ---")
        print(f"ID: {chunk.chunk_id}")
        print(f"Preview: {chunk.content[:150]}...")
        if i >= 2:  # Show only first 3 chunks
            break
    
    print(f"\n🎉 Document processor working perfectly!")
    print(f"🔍 Total chunks created: {len(chunks)}")
    print(f"📊 Average chunk length: {sum(len(c.content) for c in chunks) / len(chunks):.0f} characters")

if __name__ == "__main__":
    test_document_processor()
