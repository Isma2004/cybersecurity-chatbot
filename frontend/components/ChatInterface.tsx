// src/components/ChatInterface.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, FileText, Clock, Sparkles, Copy, ThumbsUp, ThumbsDown, MessageSquare, Shield, Database } from 'lucide-react';
import { ChatMessage, SourceReference } from '../types/api';

interface ChatInterfaceProps {
  sessionId: string | null;
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  documentsCount: number;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  sessionId,
  messages,
  onSendMessage,
  isLoading,
  documentsCount
}) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading && sessionId) {
      onSendMessage(inputValue.trim());
      setInputValue('');
      if (inputRef.current) {
        inputRef.current.style.height = 'auto';
      }
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
    
    // Auto-resize textarea
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 120)}px`;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('fr-FR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const SourceCard: React.FC<{ source: SourceReference }> = ({ source }) => (
    <div className="bg-gradient-to-r from-green-50 to-green-50/50 border border-green-200 rounded-xl p-4 hover:bg-green-100/50 transition-all duration-200 group">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-green-100 rounded-lg flex items-center justify-center">
            <FileText className="w-3 h-3 text-green-600" />
          </div>
          <span className="text-sm font-semibold text-green-900">
            {source.document_name}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded-full font-medium">
            {Math.round(source.relevance_score * 100)}% pertinent
          </span>
        </div>
      </div>
      <p className="text-sm text-green-800 leading-relaxed">
        {source.chunk_content.length > 200 
          ? source.chunk_content.substring(0, 200) + '...'
          : source.chunk_content
        }
      </p>
    </div>
  );

  const suggestions = [
    "Quelles sont les exigences de mots de passe selon ISO 27001?",
    "Comment signaler un incident de sécurité au SOC?",
    "Qu'est-ce que l'authentification multi-facteurs MFA?",
    "Quels sont les contrôles d'accès obligatoires en banque?",
    "Comment mettre en place une politique de sécurité RGPD?",
    "Procédures de sauvegarde et plan de continuité?"
  ];

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-white via-gray-50/30 to-green-50/20">
      {/* Header */}
      <div className="border-b border-gray-200/60 p-4 bg-white/80 backdrop-blur-sm shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* AI Assistant Icon */}
            <div className="relative">
              <div className="w-12 h-12 bg-gradient-to-br from-green-500 via-green-600 to-green-700 rounded-xl flex items-center justify-center shadow-lg">
                <div className="relative">
                  <Sparkles className="w-6 h-6 text-white" />
                  <div className="absolute -top-1 -right-1 w-3 h-3 bg-gradient-to-r from-green-400 to-green-500 rounded-full animate-pulse"></div>
                </div>
              </div>
              <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-gradient-to-r from-red-600 to-red-700 rounded-full"></div>
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                Assistant DocuSense
                <span className="text-xs font-medium text-green-700 bg-green-100 px-2 py-1 rounded-full border border-green-200">
                  IA Cybersécurité
                </span>
              </h2>
              <p className="text-sm text-gray-600 flex items-center gap-2">
                <Shield className="w-3 h-3 text-green-600" />
                {documentsCount > 0 
                  ? `${documentsCount} documents de sécurité disponibles`
                  : 'Aucun document chargé - Importez vos politiques de sécurité'
                }
              </p>
            </div>
          </div>
          
          {isLoading && (
            <div className="flex items-center gap-3 text-sm text-gray-600 bg-green-50 px-3 py-2 rounded-lg border border-green-200">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
              <span className="font-medium">Analyse en cours...</span>
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin">
        {!sessionId ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md">
              <div className="w-20 h-20 bg-gradient-to-br from-green-100 to-green-200 rounded-full flex items-center justify-center mx-auto mb-6">
                <MessageSquare className="w-10 h-10 text-green-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">
                Créez une nouvelle conversation
              </h3>
              <p className="text-gray-600 mb-4">
                Commencez par créer une nouvelle conversation pour poser vos questions sur la cybersécurité.
              </p>
              <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
                <Shield className="w-4 h-4 text-green-600" />
                <span>Protection des données • Conformité • Sécurité</span>
              </div>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center py-12">
            <div className="relative mb-8">
              <div className="w-20 h-20 bg-gradient-to-br from-green-100 via-green-200 to-green-300 rounded-full flex items-center justify-center mx-auto shadow-lg">
                <Bot className="w-10 h-10 text-green-700" />
              </div>
              <div className="absolute -top-1 -right-1 w-6 h-6 bg-gradient-to-r from-green-500 to-green-600 rounded-full flex items-center justify-center">
                <Sparkles className="w-3 h-3 text-white" />
              </div>
            </div>
            
            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              Bonjour ! Comment puis-je vous aider ?
            </h3>
            <p className="text-gray-600 mb-8 max-w-lg mx-auto leading-relaxed">
              Je suis votre assistant IA spécialisé en cybersécurité pour Credit Agricole du Maroc. 
              Posez-moi vos questions sur les politiques de sécurité, la conformité et les bonnes pratiques.
            </p>
            
            {documentsCount === 0 ? (
              <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-xl p-6 max-w-lg mx-auto mb-8">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">
                    <FileText className="w-4 h-4 text-yellow-600" />
                  </div>
                  <h4 className="font-semibold text-yellow-900">Documents manquants</h4>
                </div>
                <p className="text-yellow-800 text-sm leading-relaxed">
                  💡 Pour des réponses précises et personnalisées, importez vos documents de cybersécurité : 
                  politiques ISO 27001, procédures RGPD, guides de sécurité, etc.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl mx-auto">
                {suggestions.slice(0, 6).map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => onSendMessage(suggestion)}
                    className="p-4 text-left bg-white hover:bg-green-50 rounded-xl border border-gray-200 hover:border-green-300 transition-all duration-200 hover:shadow-md group"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-green-200 transition-colors">
                        <MessageSquare className="w-3 h-3 text-green-600" />
                      </div>
                      <p className="text-sm text-gray-700 group-hover:text-gray-900 font-medium">
                        {suggestion}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            )}
            
            {documentsCount > 0 && (
              <div className="mt-8 flex items-center justify-center gap-2 text-sm text-green-700 bg-green-50 px-4 py-2 rounded-lg border border-green-200 max-w-fit mx-auto">
                <Database className="w-4 h-4" />
                <span className="font-medium">{documentsCount} documents de sécurité disponibles</span>
              </div>
            )}
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-4 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {/* Avatar */}
                {message.type === 'assistant' && (
                  <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center shadow-md">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}
                
                {/* Message Content */}
                <div className={`max-w-4xl ${message.type === 'user' ? 'order-2' : 'order-1'}`}>
                  <div className={`flex items-center gap-3 mb-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <span className="text-sm font-semibold text-gray-900">
                      {message.type === 'user' ? 'Vous' : 'Assistant DocuSense'}
                    </span>
                    <span className="text-xs text-gray-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatTimestamp(message.timestamp)}
                    </span>
                    {message.processing_time && (
                      <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded-full">
                        {message.processing_time.toFixed(2)}s
                      </span>
                    )}
                  </div>
                  
                  <div
                    className={`p-4 rounded-2xl shadow-sm ${
                      message.type === 'user'
                        ? 'ca-chat-bubble-user text-white'
                        : 'ca-chat-bubble-ai text-gray-900'
                    }`}
                  >
                    <div className="whitespace-pre-wrap leading-relaxed">
                      {message.content}
                    </div>
                    
                    {/* Message Actions */}
                    {message.type === 'assistant' && (
                      <div className="flex items-center gap-2 mt-4 pt-3 border-t border-gray-200">
                        <button
                          onClick={() => copyToClipboard(message.content)}
                          className="p-2 hover:bg-green-100 rounded-lg text-gray-500 hover:text-green-600 transition-colors"
                          title="Copier la réponse"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                        <button
                          className="p-2 hover:bg-green-100 rounded-lg text-gray-500 hover:text-green-600 transition-colors"
                          title="Réponse utile"
                        >
                          <ThumbsUp className="w-4 h-4" />
                        </button>
                        <button
                          className="p-2 hover:bg-red-100 rounded-lg text-gray-500 hover:text-red-600 transition-colors"
                          title="Réponse non utile"
                        >
                          <ThumbsDown className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                    
                    {/* Sources */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-4 space-y-3">
                        <h4 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                          <FileText className="w-4 h-4 text-green-600" />
                          Sources consultées ({message.sources.length}):
                        </h4>
                        <div className="grid gap-3">
                          {message.sources.slice(0, 3).map((source, index) => (
                            <SourceCard key={index} source={source} />
                          ))}
                        </div>
                        {message.sources.length > 3 && (
                          <p className="text-xs text-gray-500 text-center">
                            +{message.sources.length - 3} autres sources consultées
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                
                {/* User Avatar */}
                {message.type === 'user' && (
                  <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-gray-600 to-gray-700 rounded-xl flex items-center justify-center shadow-md">
                    <User className="w-5 h-5 text-white" />
                  </div>
                )}
              </div>
            ))}
            
            {isLoading && (
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center shadow-md">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div className="max-w-4xl">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-sm font-semibold text-gray-900">Assistant DocuSense</span>
                    <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded-full font-medium">
                      Analyse en cours...
                    </span>
                  </div>
                  <div className="ca-chat-bubble-ai p-4 rounded-2xl shadow-sm">
                    <div className="flex items-center gap-3">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                      <span className="text-sm text-gray-600 font-medium">
                        Consultation des documents de sécurité...
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      {sessionId && (
        <div className="border-t border-gray-200/60 p-4 bg-white/80 backdrop-blur-sm">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder={
                  documentsCount === 0 
                    ? "Importez d'abord vos documents de sécurité pour des réponses personnalisées..." 
                    : "Posez votre question sur la cybersécurité... (Shift + Entrée pour une nouvelle ligne)"
                }
                disabled={isLoading}
                rows={1}
                className="w-full resize-none border border-gray-300 rounded-xl px-4 py-3 pr-16 focus:ring-2 focus:ring-green-500 focus:border-transparent disabled:bg-gray-50 disabled:cursor-not-allowed transition-all duration-200 placeholder-gray-500"
                style={{ minHeight: '52px', maxHeight: '120px' }}
              />
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center gap-2">
                {documentsCount > 0 && (
                  <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded-full font-medium border border-green-200">
                    {documentsCount} docs
                  </span>
                )}
              </div>
            </div>
            <button
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              className="px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white rounded-xl disabled:bg-gray-300 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2 h-fit shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none"
            >
              <Send className="w-4 h-4" />
              <span className="font-semibold">Envoyer</span>
            </button>
          </form>
          
          {/* Status Bar */}
          <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                🤖 <strong>DocuSense AI</strong> • Cybersécurité Credit Agricole
              </span>
              <span className="flex items-center gap-1">
                🔒 Données confidentielles et sécurisées
              </span>
            </div>
            {inputValue.length > 0 && (
              <span className="text-gray-400">{inputValue.length} caractères</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatInterface;