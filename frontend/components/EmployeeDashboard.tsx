// src/components/EmployeeDashboard.tsx
import React, { useState, useEffect } from 'react';
import Sidebar from './sidebar';
import ChatInterface from './ChatInterface';
import DocumentManager from './documentManager';
import LoadingSpinner from './LoadingSpinner';
import { ChatSession, ChatMessage, Document } from '../services/api';
import { apiService } from '../services/api';

const EmployeeDashboard: React.FC = () => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [showDocumentManager, setShowDocumentManager] = useState(false);
  const [documentManagerTab, setDocumentManagerTab] = useState<'upload' | 'list'>('upload');

  // Load initial data
  useEffect(() => {
    loadInitialData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadInitialData = async () => {
    try {
      const [sessionsResponse, documentsResponse] = await Promise.all([
        apiService.getChatSessions(),
        apiService.getDocuments()
      ]);
      
      setSessions(sessionsResponse.sessions);
      setDocuments(documentsResponse.documents);
      
      // Auto-select the most recent session
      if (sessionsResponse.sessions.length > 0) {
        loadSession(sessionsResponse.sessions[0].id);
      }
    } catch (error) {
      console.error('Error loading initial data:', error);
    } finally {
      setIsInitialLoading(false);
    }
  };

  const loadSession = async (sessionId: string) => {
    try {
      const sessionData = await apiService.getChatSession(sessionId);
      setCurrentSession(sessionData.session);
      setMessages(sessionData.messages);
    } catch (error) {
      console.error('Error loading session:', error);
    }
  };

  const createNewChat = async () => {
    try {
      const newSession = await apiService.createChatSession();
      setSessions(prev => [newSession, ...prev]);
      setCurrentSession(newSession);
      setMessages([]);
    } catch (error) {
      console.error('Error creating new chat:', error);
    }
  };

  const sendMessage = async (content: string) => {
    if (!currentSession) return;

    setIsLoading(true);
    
    try {
      await apiService.sendMessageToSession(currentSession.id, content);
      
      // Reload the session to get updated messages
      await loadSession(currentSession.id);
      
      // Update sessions list to reflect new activity
      await loadSessions();
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadSessions = async () => {
    try {
      const sessionsResponse = await apiService.getChatSessions();
      setSessions(sessionsResponse.sessions);
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  };

  const deleteSession = async (sessionId: string) => {
    try {
      await apiService.deleteChatSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      
      // If deleted session was current, clear current session
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  const loadDocuments = async () => {
    try {
      const documentsResponse = await apiService.getDocuments();
      setDocuments(documentsResponse.documents);
    } catch (error) {
      console.error('Error loading documents:', error);
    }
  };

  if (isInitialLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" variant="primary" className="mx-auto mb-4" />
          <p className="text-gray-600">Chargement de votre espace...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex">
      {/* Sidebar */}        <Sidebar
          sessions={sessions}
          currentSessionId={currentSession?.id || null}
          onSelectSession={loadSession}
          onCreateNewChat={createNewChat}
          onDeleteSession={deleteSession}
          onShowDocuments={() => {
            setDocumentManagerTab('list');
            setShowDocumentManager(true);
          }}
          onShowUpload={() => {
            setDocumentManagerTab('upload');
            setShowDocumentManager(true);
          }}
          documentsCount={documents.length}
        />

      {/* Main Content */}
      <div className="flex-1">
        <ChatInterface
          sessionId={currentSession?.id || null}
          messages={messages}
          onSendMessage={sendMessage}
          isLoading={isLoading}
          documentsCount={documents.length}
        />
      </div>        {/* Document Manager Modal */}
        {showDocumentManager && (
          <DocumentManager
            documents={documents}
            initialTab={documentManagerTab}
            onDocumentChange={() => {
              loadDocuments();
              setShowDocumentManager(false);
            }}
            onClose={() => setShowDocumentManager(false)}
          />
        )}
    </div>
  );
};

export default EmployeeDashboard;