import React, { useState } from 'react';
import { FileText, Trash2, Eye, Hash, Database, Shield, Upload } from 'lucide-react';
import { Document } from '../types/api';
import { apiService } from '../services/api';

interface DocumentListProps {
  documents: Document[];
  onDocumentDeleted: () => void;
}

const DocumentList: React.FC<DocumentListProps> = ({ documents, onDocumentDeleted }) => {
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());

  const handleDelete = async (documentId: string) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce document de la base de connaissances sécurisée?')) {
      setDeletingIds(prev => new Set(prev).add(documentId));
      
      try {
        await apiService.deleteDocument(documentId);
        onDocumentDeleted();
      } catch (error) {
        console.error('Error deleting document:', error);
        alert('Erreur lors de la suppression du document');
      } finally {
        setDeletingIds(prev => {
          const newSet = new Set(prev);
          newSet.delete(documentId);
          return newSet;
        });
      }
    }
  };


  const getFileIcon = (filename: string) => {
    const extension = filename.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf':
        return '📄';
      case 'docx':
      case 'doc':
        return '📝';
      case 'txt':
        return '📋';
      case 'png':
      case 'jpg':
      case 'jpeg':
        return '🖼️';
      default:
        return '📁';
    }
  };

  const getDocumentTypeColor = (filename: string) => {
    const extension = filename.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'docx':
      case 'doc':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'txt':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'png':
      case 'jpg':
      case 'jpeg':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      default:
        return 'bg-green-100 text-green-800 border-green-200';
    }
  };

  return (
    <div className="p-6 overflow-y-auto h-full">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center shadow-lg">
            <Database className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Base de Connaissances Sécurisée
            </h2>
            <p className="text-sm text-green-700 font-medium">Documents de cybersécurité • Credit Agricole</p>
          </div>
        </div>
        <p className="text-gray-600 leading-relaxed">
          Gérez vos documents de cybersécurité, politiques de sécurité et procédures de conformité 
          dans un environnement sécurisé et confidentiel.
        </p>
      </div>

      {documents.length === 0 ? (
        <div className="text-center py-16">
          <div className="relative mb-8">
            <div className="w-20 h-20 bg-gradient-to-br from-gray-100 to-gray-200 rounded-2xl flex items-center justify-center mx-auto">
              <FileText className="w-10 h-10 text-gray-400" />
            </div>
            <div className="absolute -top-2 -right-2 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center border-2 border-white">
              <Shield className="w-4 h-4 text-green-600" />
            </div>
          </div>
          
          <h3 className="text-xl font-bold text-gray-900 mb-3">
            Aucun document dans la base
          </h3>
          <p className="text-gray-600 mb-8 max-w-md mx-auto leading-relaxed">
            Commencez par télécharger vos documents de cybersécurité pour enrichir 
            la base de connaissances de DocuSense.
          </p>
          
          <button
            onClick={() => window.location.hash = '#upload'}
            className="btn-primary"
          >
            <Upload className="w-4 h-4 mr-2" />
            Importer Premiers Documents
          </button>
          
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto text-sm">
            <div className="bg-green-50 rounded-xl p-4 border border-green-200">
              <h4 className="font-semibold text-green-900 mb-2">Documents Recommandés</h4>
              <ul className="text-green-800 space-y-1 text-left">
                <li>• Politiques ISO 27001</li>
                <li>• Procédures RGPD</li>
                <li>• Guides de sécurité</li>
              </ul>
            </div>
            <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
              <h4 className="font-semibold text-blue-900 mb-2">Formats Supportés</h4>
              <ul className="text-blue-800 space-y-1 text-left">
                <li>• PDF, DOCX, TXT</li>
                <li>• Images (PNG, JPG)</li>
                <li>• Taille max: 50 MB</li>
              </ul>
            </div>
          </div>
        </div>
      ) : (
        <>
          {/* Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4 border border-green-200">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
                    <FileText className="w-5 h-5 text-green-600" />
                  </div>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-semibold text-green-900">
                    Total Documents
                  </p>
                  <p className="text-2xl font-bold text-green-700">
                    {documents.length}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 border border-blue-200">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                    <Hash className="w-5 h-5 text-blue-600" />
                  </div>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-semibold text-blue-900">
                    Segments Texte
                  </p>
                  <p className="text-2xl font-bold text-blue-700">
                    {documents.reduce((sum, doc) => sum + doc.chunks, 0)}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4 border border-purple-200">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                    <Eye className="w-5 h-5 text-purple-600" />
                  </div>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-semibold text-purple-900">
                    Contenu Total
                  </p>
                  <p className="text-xl font-bold text-purple-700">
                    {(documents.reduce((sum, doc) => sum + doc.total_length, 0) / 1000).toFixed(0)}K
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-4 border border-gray-200">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center">
                    <Shield className="w-5 h-5 text-gray-600" />
                  </div>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-semibold text-gray-900">
                    Statut Sécurité
                  </p>
                  <p className="text-sm font-bold text-green-600">
                    ✓ Sécurisé
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Documents Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {documents.map((document) => (
              <div
                key={document.document_id}
                className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200 hover:border-green-300 group"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3 min-w-0 flex-1">
                      <div className="flex-shrink-0">
                        <span className="text-2xl">
                          {getFileIcon(document.filename)}
                        </span>
                      </div>
                      <div className="min-w-0 flex-1">
                        <h3 className="font-semibold text-gray-900 truncate mb-1">
                          {document.filename}
                        </h3>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2 py-1 rounded-full border font-medium ${getDocumentTypeColor(document.filename)}`}>
                            {document.filename.split('.').pop()?.toUpperCase()}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2 ml-2">
                      <button
                        onClick={() => handleDelete(document.document_id)}
                        disabled={deletingIds.has(document.document_id)}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                        title="Supprimer le document"
                      >
                        {deletingIds.has(document.document_id) ? (
                          <div className="w-4 h-4 animate-spin border-2 border-red-600 border-t-transparent rounded-full"></div>
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Segments:</span>
                        <div className="font-semibold text-gray-900">{document.chunks}</div>
                      </div>
                      <div>
                        <span className="text-gray-500">Contenu:</span>
                        <div className="font-semibold text-gray-900">
                          {(document.total_length / 1000).toFixed(1)}K
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center pt-3 border-t border-gray-100">
                      <span className="text-xs text-gray-500">Document ID:</span>
                      <span className="text-xs font-mono text-gray-600 bg-gray-100 px-2 py-1 rounded">
                        {document.document_id.slice(0, 8)}...
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-gray-500">Statut:</span>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        document.status === 'ready'
                          ? 'bg-green-100 text-green-800 border border-green-200'
                          : 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                      }`}>
                        {document.status === 'ready' ? (
                          <>
                            <div className="w-1.5 h-1.5 bg-green-500 rounded-full mr-1"></div>
                            Prêt
                          </>
                        ) : (
                          <>
                            <div className="w-1.5 h-1.5 bg-yellow-500 rounded-full mr-1 animate-pulse"></div>
                            Traitement
                          </>
                        )}
                      </span>
                    </div>
                  </div>
                </div>
                
                {/* Security Badge */}
                <div className="px-6 py-3 bg-green-50 border-t border-green-100 group-hover:bg-green-100 transition-colors">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1 text-green-700">
                      <Shield className="w-3 h-3" />
                      <span className="font-medium">Sécurisé CAM</span>
                    </div>
                    <span className="text-green-600">Confidentiel</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default DocumentList;