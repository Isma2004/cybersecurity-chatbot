// src/components/GlobalDocumentUpload.tsx
import React, { useState, useCallback } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle, Loader, Shield, Tag, FileCheck } from 'lucide-react';
import { apiService } from '../services/api';

interface GlobalDocumentUploadProps {
  onUploadSuccess: () => void;
}

interface UploadStatus {
  document_id: string;
  status: 'uploading' | 'processing' | 'ready' | 'error';
  message: string;
  filename?: string;
}

const GlobalDocumentUpload: React.FC<GlobalDocumentUploadProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [uploadingFiles, setUploadingFiles] = useState<{[key: string]: UploadStatus}>({});

  const handleFileUpload = async (file: File) => {
    const fileId = `${file.name}-${Date.now()}`;
    
    // Initialize upload status
    setUploadingFiles(prev => ({
      ...prev,
      [fileId]: {
        document_id: fileId,
        status: 'uploading',
        message: 'Téléchargement sécurisé vers la base globale...',
        filename: file.name
      }
    }));

    try {
      // Upload file as global document
      const uploadResponse = await apiService.uploadGlobalDocument(file, description, tags);
      
      // Update status to processing
      setUploadingFiles(prev => ({
        ...prev,
        [fileId]: {
          document_id: uploadResponse.document_id,
          status: 'processing',
          message: uploadResponse.message,
          filename: file.name
        }
      }));

      // Poll for processing status
      pollProcessingStatus(fileId, uploadResponse.document_id, file.name);

    } catch (error: any) {
      console.error('Upload error:', error);
      setUploadingFiles(prev => ({
        ...prev,
        [fileId]: {
          document_id: fileId,
          status: 'error',
          message: error.response?.data?.detail || 'Erreur lors du téléchargement global',
          filename: file.name
        }
      }));
    }
  };

  const pollProcessingStatus = async (fileId: string, documentId: string, filename: string) => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = async () => {
      try {
        // Note: We might need to create a specific endpoint for global document status
        // For now, using the regular status endpoint
        const status = await apiService.getProcessingStatus(documentId);
        
        setUploadingFiles(prev => ({
          ...prev,
          [fileId]: {
            ...status,
            filename
          }
        }));

        if (status.status === 'ready') {
          // Success - remove from uploading list after 3 seconds
          setTimeout(() => {
            setUploadingFiles(prev => {
              const newState = { ...prev };
              delete newState[fileId];
              return newState;
            });
            onUploadSuccess();
          }, 3000);
          return;
        }

        if (status.status === 'error') {
          return; // Stop polling on error
        }

        // Continue polling if still processing
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000);
        } else {
          setUploadingFiles(prev => ({
            ...prev,
            [fileId]: {
              ...prev[fileId],
              status: 'error',
              message: 'Timeout: Le traitement global prend trop de temps'
            }
          }));
        }

      } catch (error) {
        console.error('Polling error:', error);
        setUploadingFiles(prev => ({
          ...prev,
          [fileId]: {
            ...prev[fileId],
            status: 'error',
            message: 'Erreur de communication avec le serveur global'
          }
        }));
      }
    };

    poll();
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    files.forEach(handleFileUpload);
  }, [handleFileUpload]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    files.forEach(handleFileUpload);
    e.target.value = ''; // Reset input
  }, [handleFileUpload]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploading':
      case 'processing':
        return <Loader className="w-5 h-5 animate-spin text-green-500" />;
      case 'ready':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <FileText className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'processing':
        return 'border-green-200 bg-green-50';
      case 'ready':
        return 'border-green-300 bg-green-100';
      case 'error':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg">
          <Upload className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Import Global de Documents
        </h2>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Téléchargez des documents qui seront accessibles à tous les utilisateurs de DocuSense. 
          Ces documents enrichiront la base de connaissances globale de Credit Agricole du Maroc.
        </p>
      </div>

      {/* Security Notice */}
      <div className="bg-gradient-to-r from-green-50 to-green-100 border border-green-200 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <Shield className="w-4 h-4 text-green-600" />
          </div>
          <div>
            <h4 className="font-semibold text-green-900 mb-1">Import Administrateur - Base Globale</h4>
            <p className="text-sm text-green-800">
              Ces documents seront disponibles pour tous les employés et traités selon les plus hauts standards de sécurité bancaire.
            </p>
          </div>
        </div>
      </div>

      {/* Metadata Form */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Informations du Document</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Description (optionnelle)
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Décrivez le contenu et l'objectif du document..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              rows={3}
            />
          </div>
          <div>
            <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-2">
              Tags (optionnels)
            </label>
            <input
              id="tags"
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="ISO27001, RGPD, Sécurité..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">Séparez les tags par des virgules</p>
          </div>
        </div>
      </div>

      {/* Upload Area */}
      <div
        className={`transition-all duration-300 rounded-2xl p-8 text-center border-2 border-dashed ${
          isDragging 
            ? 'border-green-500 bg-green-100/50' 
            : 'border-green-300 bg-green-50/30 hover:border-green-400 hover:bg-green-50/50'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center">
          <div className="w-16 h-16 bg-gradient-to-br from-green-100 to-green-200 rounded-xl flex items-center justify-center mb-4">
            <Upload className="w-8 h-8 text-green-600" />
          </div>
          
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Déposez vos documents globaux ici
            </h3>
            <p className="text-gray-600">
              ou cliquez pour sélectionner vos fichiers de sécurité
            </p>
          </div>
          
          <input
            type="file"
            multiple
            accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
            onChange={handleFileSelect}
            className="hidden"
            id="global-file-upload"
          />
          
          <label
            htmlFor="global-file-upload"
            className="btn-primary cursor-pointer"
          >
            <Upload className="w-4 h-4 mr-2" />
            Choisir Documents Globaux
          </label>
          
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-green-600" />
              <span>PDF, DOCX, TXT, Images</span>
            </div>
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-green-600" />
              <span>Taille max: 50 MB par fichier</span>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Progress */}
      {Object.keys(uploadingFiles).length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Loader className="w-5 h-5 animate-spin text-green-600" />
            Traitement Global en Cours
          </h3>
          <div className="space-y-3">
            {Object.entries(uploadingFiles).map(([fileId, status]) => (
              <div
                key={fileId}
                className={`p-4 rounded-xl border ${getStatusColor(status.status)} transition-all duration-200`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(status.status)}
                    <div>
                      <p className="font-semibold text-gray-900">
                        {status.filename || `Document ${status.document_id}`}
                      </p>
                      <p className="text-sm text-gray-600">
                        {status.message}
                      </p>
                    </div>
                  </div>
                  
                  {status.status === 'ready' && (
                    <div className="flex items-center gap-2">
                      <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full font-medium">
                        Global
                      </span>
                      <CheckCircle className="w-6 h-6 text-green-500" />
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Best Practices */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-6 border border-blue-200">
          <h4 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" />
            📋 Documents Recommandés
          </h4>
          <ul className="text-sm text-blue-800 space-y-2">
            <li>• Politiques de sécurité ISO 27001</li>
            <li>• Procédures RGPD et conformité</li>
            <li>• Guides de sécurité bancaire</li>
            <li>• Manuels de formation cybersécurité</li>
          </ul>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-6 border border-green-200">
          <h4 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
            <Tag className="w-5 h-5 text-green-600" />
            🏷️ Bonnes Pratiques
          </h4>
          <ul className="text-sm text-green-800 space-y-2">
            <li>• Nommez les fichiers de façon descriptive</li>
            <li>• Ajoutez des descriptions détaillées</li>
            <li>• Utilisez des tags pertinents</li>
            <li>• Vérifiez la qualité du contenu</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default GlobalDocumentUpload;