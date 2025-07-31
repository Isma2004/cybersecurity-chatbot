// src/components/DocumentManager.tsx
import React, { useState } from 'react';
import { Upload, Database, X, Shield } from 'lucide-react';
import FileUpload from './FileUpload';
import DocumentList from './DocumentList';
import { Document } from '../types/api';

interface DocumentManagerProps {
  documents: Document[];
  onDocumentChange: () => void;
  onClose: () => void;
  initialTab?: 'upload' | 'list';
}

const DocumentManager: React.FC<DocumentManagerProps> = ({
  documents,
  onDocumentChange,
  onClose,
  initialTab = 'upload'
}) => {
  const [activeTab, setActiveTab] = useState<'upload' | 'list'>(initialTab);

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col overflow-hidden border border-gray-200">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-green-50/30">
          <div className="flex items-center gap-4">
            {/* Credit Agricole Mini Logo */}
            <div className="relative">
              <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-sm border border-gray-200">
                <div className="relative w-7 h-7">
                  <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-1.5 h-4 bg-gradient-to-b from-green-600 to-green-700 rounded-full rotate-12"></div>
                  <div className="absolute top-0.5 right-0 w-2.5 h-4.5 bg-gradient-to-br from-green-500 to-green-600 rounded-full -rotate-12"></div>
                  <div className="absolute top-0.5 left-0 w-2.5 h-4.5 bg-gradient-to-bl from-green-500 to-green-600 rounded-full rotate-12"></div>
                </div>
              </div>
              <div className="absolute -bottom-1 left-0 right-0 h-1 bg-gradient-to-r from-red-600 to-red-700 rounded-full"></div>
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                Gestion Documentaire
                <span className="text-sm font-medium text-green-700 bg-green-100 px-2 py-1 rounded-full border border-green-200">
                  Sécurisé
                </span>
              </h2>
              <p className="text-sm text-gray-600">
                DocuSense • Credit Agricole du Maroc
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* Document Count Badge */}
            <div className="flex items-center gap-2 px-3 py-2 bg-green-50 rounded-lg border border-green-200">
              <Database className="w-4 h-4 text-green-600" />
              <span className="text-sm font-semibold text-green-900">
                {documents.length} documents
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-xl transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 bg-gray-50">
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-6 py-4 text-sm font-semibold transition-all duration-200 flex items-center gap-3 ${
              activeTab === 'upload'
                ? 'text-green-700 border-b-2 border-green-600 bg-white'
                : 'text-gray-600 hover:text-green-600 hover:bg-green-50/50'
            }`}
          >
            <Upload className="w-4 h-4" />
            Importer Documents
          </button>
          <button
            onClick={() => setActiveTab('list')}
            className={`px-6 py-4 text-sm font-semibold transition-all duration-200 flex items-center gap-3 ${
              activeTab === 'list'
                ? 'text-green-700 border-b-2 border-green-600 bg-white'
                : 'text-gray-600 hover:text-green-600 hover:bg-green-50/50'
            }`}
          >
            <Database className="w-4 h-4" />
            Base de Connaissances ({documents.length})
          </button>
        </div>

        {/* Tab Indicator */}
        <div className="h-1 bg-gradient-to-r from-transparent via-green-200 to-transparent"></div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto bg-gray-50/30">
          {activeTab === 'upload' ? (
            <FileUpload onFileUploaded={onDocumentChange} />
          ) : (
            <DocumentList documents={documents} onDocumentDeleted={onDocumentChange} />
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 text-sm text-gray-600">
              <Shield className="w-4 h-4 text-green-600" />
              <span>Tous les documents sont traités de manière sécurisée et confidentielle</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-sm text-gray-500">
                Total: <span className="font-semibold text-gray-900">{documents.length}</span> documents
              </div>
              <button
                onClick={onClose}
                className="btn-secondary"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentManager;