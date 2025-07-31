// src/App.tsx
import React, { useState, useEffect } from 'react';
import { Shield } from 'lucide-react';
import { authService, User } from './services/authService';
import Login from './components/Login';
import AdminDashboard from './components/AdminDashboard';
import EmployeeDashboard from './components/EmployeeDashboard';
import Header from './components/Header';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    initializeAuth();
    // Set up logout callback
    authService.setLogoutCallback(() => {
      setUser(null);
    });
  }, []);

  const initializeAuth = async () => {
    try {
      // Check if user is already logged in
      if (authService.isAuthenticated()) {
        const isValid = await authService.verifyToken();
        if (isValid) {
          setUser(authService.getCurrentUser());
        }
      }
    } catch (error) {
      console.error('Auth initialization error:', error);
      authService.logout();
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoginSuccess = () => {
    setUser(authService.getCurrentUser());
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
  };

  // Show loading spinner during initial auth check
  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 via-green-50/20 to-white">
        <div className="text-center">
          {/* Credit Agricole Loading Logo */}
          <div className="relative mb-6">
            <div className="w-20 h-20 bg-white rounded-2xl flex items-center justify-center shadow-lg mx-auto border border-gray-200">
              <div className="relative w-12 h-12">
                <div className="absolute top-1 left-1/2 transform -translate-x-1/2 w-3 h-6 bg-gradient-to-b from-green-600 to-green-700 rounded-full rotate-12 animate-pulse"></div>
                <div className="absolute top-2 right-1 w-4 h-7 bg-gradient-to-br from-green-500 to-green-600 rounded-full -rotate-12 animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                <div className="absolute top-2 left-1 w-4 h-7 bg-gradient-to-bl from-green-500 to-green-600 rounded-full rotate-12 animate-pulse" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
            <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 w-16 h-1.5 bg-gradient-to-r from-red-600 to-red-700 rounded-full"></div>
          </div>
          
          <div className="space-y-2 mb-4">
            <h2 className="text-2xl font-bold text-gray-900">DocuSense</h2>
            <p className="text-green-700 font-semibold">Assistant IA Cybersécurité</p>
            <p className="text-gray-600 text-sm">Credit Agricole du Maroc</p>
          </div>
          
          <LoadingSpinner size="lg" variant="primary" className="mx-auto mb-4" />
          <p className="text-gray-600">Initialisation sécurisée...</p>
          
          <div className="mt-6 flex items-center justify-center gap-2 text-xs text-gray-500">
            <Shield className="w-3 h-3 text-green-600" />
            <span>Authentification en cours</span>
          </div>
        </div>
      </div>
    );
  }

  // Show login page if not authenticated
  if (!user) {
    return (
      <ErrorBoundary>
        <Login onLoginSuccess={handleLoginSuccess} />
      </ErrorBoundary>
    );
  }

  // Show appropriate dashboard based on user role
  return (
    <ErrorBoundary>
      <div className="h-screen flex flex-col bg-gradient-to-br from-gray-50 via-white to-green-50/10">
        {/* Header */}
        <Header user={user} onLogout={handleLogout} />
        
        {/* Main Content */}
        <div className="flex-1 overflow-hidden">
          {user.role === 'admin' ? (
            <div className="h-full p-6 overflow-y-auto">
              <AdminDashboard />
            </div>
          ) : (
            <div className="h-full">
              <EmployeeDashboard />
            </div>
          )}
        </div>
      </div>
    </ErrorBoundary>
  );
}

export default App;