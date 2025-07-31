// src/components/Sidebar.tsx
import React, { useState } from 'react';
import { 
  Plus, 
  MessageSquare, 
  Upload, 
  Database, 
  Trash2, 
  Search,
  Shield,
  Clock
} from 'lucide-react';
import { ChatSession } from '../types/api';

interface SidebarProps {
  sessions: ChatSession[];
  currentSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onCreateNewChat: () => void;
  onDeleteSession: (sessionId: string) => void;
  onShowDocuments: () => void;
  onShowUpload: () => void;
  documentsCount: number;
}

const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  currentSessionId,
  onSelectSession,
  onCreateNewChat,
  onDeleteSession,
  onShowDocuments,
  onShowUpload,
  documentsCount
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [hoveredSession, setHoveredSession] = useState<string | null>(null);

  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    session.preview?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 24 * 7) {
      return date.toLocaleDateString('fr-FR', { weekday: 'short' });
    } else {
      return date.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' });
    }
  };

  const handleDeleteSession = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    if (window.confirm('Supprimer cette conversation ?')) {
      onDeleteSession(sessionId);
    }
  };

  return (
    <div className="w-80 bg-white text-gray-900 flex flex-col h-full border-r border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-3 mb-4">
          {/* Credit Agricole Mini Logo */}
          <div className="relative">
            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm border border-gray-200">
              <div className="relative w-6 h-6">
                <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-1.5 h-3 bg-gradient-to-b from-green-600 to-green-700 rounded-full rotate-12"></div>
                <div className="absolute top-0.5 right-0 w-2 h-3.5 bg-gradient-to-br from-green-500 to-green-600 rounded-full -rotate-12"></div>
                <div className="absolute top-0.5 left-0 w-2 h-3.5 bg-gradient-to-bl from-green-500 to-green-600 rounded-full rotate-12"></div>
              </div>
            </div>
            <div className="absolute -bottom-0.5 left-0 right-0 h-0.5 bg-gradient-to-r from-red-600 to-red-700 rounded-full"></div>
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">DocuSense</h1>
            <p className="text-xs text-gray-600">Assistant IA Cybersécurité</p>
          </div>
        </div>

        {/* New Chat Button */}
        <button
          onClick={onCreateNewChat}
          className="w-full flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 rounded-xl transition-all duration-300 group shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
        >
          <Plus className="w-5 h-5 text-white" />
          <span className="text-sm font-semibold text-white">Nouvelle conversation</span>
        </button>
      </div>

      {/* Search */}
      <div className="p-4 border-b border-gray-200">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher conversations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-300 rounded-lg text-sm text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200"
          />
        </div>
      </div>

      {/* Document Status Bar */}
      <div className="px-4 py-3 bg-green-50 border-b border-gray-200">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-green-700">
            <Database className="w-3 h-3" />
            <span>Base de connaissances</span>
          </div>
          <span className="bg-green-600 text-white px-2 py-0.5 rounded-full font-medium">
            {documentsCount}
          </span>
        </div>
      </div>

      {/* Chat Sessions */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        <div className="p-2">
          {filteredSessions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <MessageSquare className="w-8 h-8 mx-auto mb-3 opacity-50" />
              <p className="text-sm mb-1">
                {searchTerm ? 'Aucun résultat' : 'Aucune conversation'}
              </p>
              <p className="text-xs opacity-75">
                {searchTerm ? 'Essayez un autre terme' : 'Commencez une nouvelle conversation'}
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {filteredSessions.map((session) => (
                <div
                  key={session.id}
                  className={`group relative p-3 rounded-xl cursor-pointer transition-all duration-200 ${
                    currentSessionId === session.id
                      ? 'bg-gradient-to-r from-green-50 to-green-100 border border-green-200 text-green-900'
                      : 'hover:bg-gray-50 text-gray-700 border border-transparent'
                  }`}
                  onClick={() => onSelectSession(session.id)}
                  onMouseEnter={() => setHoveredSession(session.id)}
                  onMouseLeave={() => setHoveredSession(null)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <MessageSquare className="w-3 h-3 flex-shrink-0 opacity-60" />
                        <h3 className="text-sm font-medium truncate">
                          {session.title}
                        </h3>
                      </div>
                      {session.preview && (
                        <p className="text-xs opacity-70 line-clamp-2 mb-2 pl-5">
                          {session.preview}
                        </p>
                      )}
                      <div className="flex items-center gap-3 text-xs opacity-60 pl-5">
                        <div className="flex items-center gap-1">
                          <MessageSquare className="w-3 h-3" />
                          <span>{session.message_count}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          <span>{formatDate(session.updated_at)}</span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Actions */}
                    {(hoveredSession === session.id || currentSessionId === session.id) && (
                      <div className="flex items-center gap-1 ml-2">
                        <button
                          onClick={(e) => handleDeleteSession(e, session.id)}
                          className="p-1.5 hover:bg-red-100 rounded-lg opacity-70 hover:opacity-100 transition-all text-red-500 hover:text-red-600"
                          title="Supprimer la conversation"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    )}
                  </div>
                  
                  {/* Active indicator */}
                  {currentSessionId === session.id && (
                    <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-1 h-8 bg-gradient-to-b from-green-400 to-green-600 rounded-r-full"></div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t border-gray-200 space-y-2 bg-gray-50">
        <button
          onClick={onShowUpload}
          className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-gray-700 hover:text-gray-900 hover:bg-white rounded-lg transition-all duration-200 group border border-gray-200 hover:border-green-300"
        >
          <Upload className="w-4 h-4 group-hover:text-green-600 transition-colors" />
          <span>Importer documents</span>
        </button>
        
        <button
          onClick={onShowDocuments}
          className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-gray-700 hover:text-gray-900 hover:bg-white rounded-lg transition-all duration-200 group border border-gray-200 hover:border-green-300"
        >
          <Database className="w-4 h-4 group-hover:text-green-600 transition-colors" />
          <span>Gérer les documents</span>
          {documentsCount > 0 && (
            <span className="ml-auto bg-green-600 text-white text-xs px-2 py-0.5 rounded-full font-medium">
              {documentsCount}
            </span>
          )}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;