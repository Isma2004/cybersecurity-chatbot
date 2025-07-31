// src/components/AdminDashboard.tsx
import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Upload, 
  Database, 
  BarChart3, 
  FileText, 
  TrendingUp,
  Globe,
  Trash2,
  Search,
  Filter
} from 'lucide-react';
import { apiService, Document, AdminStats } from '../services/api';
import { authService } from '../services/authService';
import GlobalDocumentUpload from './GlobalDocumentUpload';
import LoadingSpinner from './LoadingSpinner';

const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [globalDocuments, setGlobalDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'documents' | 'upload'>('overview');
  const [searchTerm, setSearchTerm] = useState('');

  const user = authService.getCurrentUser();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      const [dashboardStats, globalDocs] = await Promise.all([
        apiService.getAdminDashboard(),
        apiService.getGlobalDocuments()
      ]);
      setStats(dashboardStats);
      setGlobalDocuments(globalDocs.documents);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce document global ?')) {
      try {
        await apiService.deleteGlobalDocument(documentId);
        await loadDashboardData();
      } catch (error) {
        console.error('Error deleting document:', error);
        alert('Erreur lors de la suppression du document');
      }
    }
  };

  const filteredDocuments = globalDocuments.filter(doc =>
    doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" variant="primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-2xl p-6 border border-green-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-gradient-to-br from-green-600 to-green-700 rounded-xl flex items-center justify-center shadow-lg">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-green-900">Tableau de Bord Administrateur</h1>
              <p className="text-green-700">
                Bienvenue, {user?.full_name || user?.username}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {[
              { id: 'overview', label: 'Vue d\'ensemble', icon: BarChart3 },
              { id: 'documents', label: 'Documents Globaux', icon: Database },
              { id: 'upload', label: 'Importer Global', icon: Upload }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-green-500 text-green-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'overview' && stats && (
            <div className="space-y-6">
              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-xl border border-blue-200">
                  <div className="flex items-center">
                    <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                      <Globe className="w-6 h-6 text-blue-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-blue-900">Documents Globaux</p>
                      <p className="text-2xl font-bold text-blue-700">{stats.total_global_documents}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-xl border border-green-200">
                  <div className="flex items-center">
                    <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                      <FileText className="w-6 h-6 text-green-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-green-900">Total Documents</p>
                      <p className="text-2xl font-bold text-green-700">{stats.total_global_documents + stats.total_personal_documents}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-6 rounded-xl border border-orange-200">
                  <div className="flex items-center">
                    <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
                      <TrendingUp className="w-6 h-6 text-orange-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-orange-900">Requêtes Aujourd'hui</p>
                      <p className="text-2xl font-bold text-orange-700">{stats.total_queries_today}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-gray-50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions Rapides</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <button
                    onClick={() => setActiveTab('upload')}
                    className="p-4 bg-white rounded-lg border border-gray-200 hover:border-green-300 hover:bg-green-50 transition-all duration-200 text-left group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center group-hover:bg-green-200 transition-colors">
                        <Upload className="w-5 h-5 text-green-600" />
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900">Importer Document Global</h4>
                        <p className="text-sm text-gray-600">Ajouter à la base commune</p>
                      </div>
                    </div>
                  </button>

                  <button
                    onClick={() => setActiveTab('documents')}
                    className="p-4 bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all duration-200 text-left group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center group-hover:bg-blue-200 transition-colors">
                        <Database className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900">Gérer Documents</h4>
                        <p className="text-sm text-gray-600">Consulter et organiser</p>
                      </div>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'documents' && (
            <div className="space-y-6">
              {/* Search and Filters */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Rechercher des documents..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    />
                  </div>
                  <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                    <Filter className="w-4 h-4" />
                    Filtres
                  </button>
                </div>
                <div className="text-sm text-gray-600">
                  {filteredDocuments.length} document(s) global(aux)
                </div>
              </div>

              {/* Documents List */}
              {filteredDocuments.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-xl">
                  <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    {searchTerm ? 'Aucun document trouvé' : 'Aucun document global'}
                  </h3>
                  <p className="text-gray-600 mb-4">
                    {searchTerm 
                      ? 'Essayez avec un autre terme de recherche'
                      : 'Commencez par importer des documents dans la base globale'
                    }
                  </p>
                  {!searchTerm && (
                    <button
                      onClick={() => setActiveTab('upload')}
                      className="btn-primary"
                    >
                      <Upload className="w-4 h-4 mr-2" />
                      Importer Premier Document
                    </button>
                  )}
                </div>
              ) : (
                <div className="grid gap-4">
                  {filteredDocuments.map((doc) => (
                    <div
                      key={doc.document_id}
                      className="bg-white border border-gray-200 rounded-lg p-4 hover:border-green-300 hover:bg-green-50/30 transition-all duration-200"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                            <FileText className="w-5 h-5 text-green-600" />
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900">{doc.filename}</h4>
                            <div className="flex items-center gap-4 text-sm text-gray-600">
                              <span>{doc.chunks} segments</span>
                              <span>{(doc.total_length / 1000).toFixed(1)}K caractères</span>
                              {doc.uploaded_by && <span>Par {doc.uploaded_by}</span>}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full font-medium">
                            Global
                          </span>
                          <button
                            onClick={() => handleDeleteDocument(doc.document_id)}
                            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Supprimer"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'upload' && (
            <GlobalDocumentUpload onUploadSuccess={loadDashboardData} />
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;