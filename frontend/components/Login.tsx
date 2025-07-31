// src/components/Login.tsx
import React, { useState } from 'react';
import { Eye, EyeOff, LogIn, Shield, AlertCircle } from 'lucide-react';
import { authService, LoginCredentials } from '../services/authService';

interface LoginProps {
  onLoginSuccess: () => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [credentials, setCredentials] = useState<LoginCredentials>({
    username: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (error) setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await authService.login(credentials);
      onLoginSuccess();
    } catch (error: any) {
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Demo credentials removed for security - use actual credentials

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-green-50/20 to-white flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo and Branding */}
        <div className="text-center mb-8">
          <div className="relative inline-block mb-4">
            <div className="w-20 h-20 bg-white rounded-2xl flex items-center justify-center shadow-lg mx-auto border border-gray-200">
              <div className="relative w-12 h-12">
                <div className="absolute top-1 left-1/2 transform -translate-x-1/2 w-3 h-6 bg-gradient-to-b from-green-600 to-green-700 rounded-full rotate-12"></div>
                <div className="absolute top-2 right-1 w-4 h-7 bg-gradient-to-br from-green-500 to-green-600 rounded-full -rotate-12"></div>
                <div className="absolute top-2 left-1 w-4 h-7 bg-gradient-to-bl from-green-500 to-green-600 rounded-full rotate-12"></div>
              </div>
            </div>
            <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 w-16 h-1.5 bg-gradient-to-r from-red-600 to-red-700 rounded-full"></div>
          </div>
          
          <h1 className="text-3xl font-bold text-gray-900 mb-2">DocuSense</h1>
          <p className="text-green-700 font-semibold">Assistant IA Cybersécurité</p>
          <p className="text-gray-600 text-sm">Credit Agricole du Maroc</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
          <div className="p-8">
            <div className="text-center mb-6">
              <h2 className="text-xl font-bold text-gray-900 mb-2">Connexion Sécurisée</h2>
              <p className="text-gray-600 text-sm">Accédez à votre espace cybersécurité</p>
            </div>

            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-red-800 text-sm font-medium">Erreur de connexion</p>
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="username" className="block text-sm font-semibold text-gray-700 mb-2">
                  Nom d'utilisateur
                </label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  value={credentials.username}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200"
                  placeholder="Saisissez votre nom d'utilisateur"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-semibold text-gray-700 mb-2">
                  Mot de passe
                </label>
                <div className="relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={credentials.password}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200"
                    placeholder="Saisissez votre mot de passe"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading || !credentials.username || !credentials.password}
                className="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white font-semibold py-3 px-4 rounded-xl transition-all duration-300 flex items-center justify-center gap-2 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <LogIn className="w-5 h-5" />
                )}
                {isLoading ? 'Connexion...' : 'Se connecter'}
              </button>
            </form>
          </div>

        </div>

        {/* Security Notice */}
        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500 flex items-center justify-center gap-1">
            <Shield className="w-3 h-3 text-green-600" />
            Connexion sécurisée SSL • Données confidentielles
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;