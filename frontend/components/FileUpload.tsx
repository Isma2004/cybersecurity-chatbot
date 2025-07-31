import React, { useState, useCallback } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle, Loader, Shield, Database } from 'lucide-react';
import { apiService } from '../services/api';
import { ProcessingStatus } from '../types/api';

interface FileUploadProps {
  onFileUploaded: () => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUploaded }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<{[key: string]: ProcessingStatus}>({});

  const handleFileUpload = async (file: File) => {
    const fileId = `${file.name}-${Date.now()}`;
    
    // Initialize upload status
    setUploadingFiles(prev => ({
      ...prev,
      [fileId]: {
        document_id: fileId,
        status: 'uploading',
        message: 'Téléchargement sécurisé en cours...'
      }
    }));

    try {
      // Upload file
      const uploadResponse = await apiService.uploadDocument(file);
      
      // Update status to processing
      setUploadingFiles(prev => ({
        ...prev,
        [fileId]: {
          document_id: uploadResponse.document_id,
          status: 'processing',
          message: uploadResponse.message
        }
      }));

      // Poll for processing status
      pollProcessingStatus(fileId, uploadResponse.document_id);

    } catch (error: any) {
      console.error('Upload error:', error);
      setUploadingFiles(prev => ({
        ...prev,
        [fileId]: {
          document_id: fileId,
          status: 'error',
          message: error.response?.data?.detail || 'Erreur lors du téléchargement sécurisé'
        }
      }));
    }
  };

  const pollProcessingStatus = async (fileId: string, documentId: string) => {
    const maxAttempts = 60; // 60 seconds max (cloud processing can take longer)
    let attempts = 0;

    const poll = async () => {
      try {
        const status = await apiService.getProcessingStatus(documentId);
        
        setUploadingFiles(prev => ({
          ...prev,
          [fileId]: status
        }));

        if (status.status === 'ready') {
          // Success - remove from uploading list after 3 seconds
          setTimeout(() => {
            setUploadingFiles(prev => {
              const newState = { ...prev };
              delete newState[fileId];
              return newState;
            });
            onFileUploaded();
          }, 3000);
          return;
        }

        if (status.status === 'error') {
          return; // Stop polling on error
        }

        // Continue polling if still processing
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000); // Poll every 2 seconds (cloud processing is slower)
        } else {
          // Timeout
          setUploadingFiles(prev => ({
            ...prev,
            [fileId]: {
              ...prev[fileId],
              status: 'error',
              message: 'Timeout: Le traitement sécurisé prend trop de temps'
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
            message: 'Erreur de communication sécurisée avec le serveur'
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
    <div className="p-6 overflow-y-auto">
      {/* Header Section */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center shadow-lg">
            <Upload className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Import de Documents Sécurisés
            </h2>
            <p className="text-sm text-green-700 font-medium">DocuSense • Credit Agricole du Maroc</p>
          </div>
        </div>
        <p className="text-gray-600 leading-relaxed">
          Téléchargez vos documents de cybersécurité pour enrichir la base de connaissances : 
          politiques ISO 27001, procédures RGPD, guides de sécurité, analyses de risques, etc.
        </p>
      </div>

      {/* Security Notice */}
      <div className="mb-6 bg-gradient-to-r from-green-50 to-green-100/50 border border-green-200 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <Shield className="w-4 h-4 text-green-600" />
          </div>
          <div>
            <h4 className="font-semibold text-green-900 mb-1">Sécurité et Confidentialité</h4>
            <p className="text-sm text-green-800 leading-relaxed">
              Vos documents sont traités de manière sécurisée et confidentielle. 
              Toutes les données sont chiffrées et stockées selon les standards bancaires de Credit Agricole.
            </p>
          </div>
        </div>
      </div>

      {/* Upload Area */}
      <div
        className={`transition-all duration-300 ${
          isDragging 
            ? 'ca-upload-zone-active' 
            : 'ca-upload-zone'
        } rounded-2xl p-8 text-center border-2 border-dashed`}
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
              Déposez vos documents ici
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
            id="file-upload"
          />
          
          <label
            htmlFor="file-upload"
            className="btn-primary cursor-pointer"
          >
            <Upload className="w-4 h-4 mr-2" />
            Choisir Documents
          </label>
          
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-green-600" />
              <span>PDF, DOCX, TXT, Images</span>
            </div>
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-green-600" />
              <span>Taille max: 50 MB par fichier</span>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Progress */}
      {Object.keys(uploadingFiles).length > 0 && (
        <div className="mt-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Loader className="w-5 h-5 animate-spin text-green-600" />
            Traitement Sécurisé en Cours
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
                        Document {status.document_id}
                      </p>
                      <p className="text-sm text-gray-600">
                        {status.message}
                      </p>
                      {status.metadata && (
                        <div className="mt-1 flex items-center gap-3 text-xs text-gray-500">
                          {status.metadata.file_size && (
                            <span>Taille: {Math.round(status.metadata.file_size / 1024)} KB</span>
                          )}
                          {status.metadata.ownership && (
                            <span>Type: {status.metadata.ownership}</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {status.status === 'ready' && (
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-6 h-6 text-green-500" />
                      <span className="text-sm font-medium text-green-700">Sécurisé</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Best Practices Section */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Tips */}
        <div className="bg-gradient-to-br from-blue-50 to-blue-100/50 rounded-xl p-6 border border-blue-200">
          <h4 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" />
            💡 Optimisation des Résultats
          </h4>
          <ul className="text-sm text-blue-800 space-y-2">
            <li className="flex items-start gap-2">
              <span className="text-blue-600 mt-1">•</span>
              <span>Privilégiez les documents structurés (politiques, procédures)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 mt-1">•</span>
              <span>Assurez-vous que le texte est lisible et de qualité</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 mt-1">•</span>
              <span>Documents en français recommandés pour de meilleurs résultats</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 mt-1">•</span>
              <span>Nommez vos fichiers de manière descriptive</span>
            </li>
          </ul>
        </div>

        {/* Document Types */}
        <div className="bg-gradient-to-br from-green-50 to-green-100/50 rounded-xl p-6 border border-green-200">
          <h4 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
            <Shield className="w-5 h-5 text-green-600" />
            📚 Types de Documents Recommandés
          </h4>
          <ul className="text-sm text-green-800 space-y-2">
            <li className="flex items-start gap-2">
              <span className="text-green-600 mt-1">•</span>
              <span>Politiques de sécurité ISO 27001</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 mt-1">•</span>
              <span>Procédures RGPD et protection des données</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 mt-1">•</span>
              <span>Guides de sécurité et bonnes pratiques</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 mt-1">•</span>
              <span>Analyses de risques et rapports d'audit</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
          <Shield className="w-4 h-4 text-green-600" />
          <span>Données traitées selon les standards de sécurité bancaire</span>
          <span className="w-1 h-1 bg-gray-400 rounded-full mx-2"></span>
          <span>Credit Agricole du Maroc</span>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;