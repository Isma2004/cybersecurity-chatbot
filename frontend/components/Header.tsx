// src/components/Header.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Shield, LogOut, User, Settings, ChevronDown } from 'lucide-react';
import { User as UserType } from '../services/authService';

interface HeaderProps {
  user: UserType;
  onLogout: () => void;
}

const Header: React.FC<HeaderProps> = ({ user, onLogout }) => {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getRoleDisplay = (role: string) => {
    switch (role) {
      case 'admin':
        return 'Administrateur';
      case 'employee':
        return 'Employé';
      default:
        return role;
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'employee':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200/60 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Brand */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              {/* Credit Agricole Logo */}
              <div className="relative">
                <div className="w-12 h-12 bg-white rounded-lg flex items-center justify-center shadow-sm border border-gray-200">
                  <div className="relative w-8 h-8">
                    <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-2 h-4 bg-gradient-to-b from-green-600 to-green-700 rounded-full rotate-12"></div>
                    <div className="absolute top-1 right-0 w-3 h-5 bg-gradient-to-br from-green-500 to-green-600 rounded-full -rotate-12"></div>
                    <div className="absolute top-1 left-0 w-3 h-5 bg-gradient-to-bl from-green-500 to-green-600 rounded-full rotate-12"></div>
                  </div>
                </div>
                <div className="absolute -bottom-1 left-0 right-0 h-1 bg-gradient-to-r from-red-600 to-red-700 rounded-full"></div>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-bold text-gray-900">DocuSense</h1>
                  <span className="text-sm font-medium text-green-700 bg-green-50 px-2 py-0.5 rounded-full border border-green-200">AI</span>
                </div>
                <p className="text-xs text-gray-500 flex items-center gap-1">
                  <span>Credit Agricole du Maroc</span>
                  <span className="w-1 h-1 bg-gray-400 rounded-full"></span>
                  <span>Assistant Cybersécurité</span>
                </p>
              </div>
            </div>
          </div>

          {/* Right Side - User Menu */}
          <div className="flex items-center gap-4">
            {/* System Status */}
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-green-50 rounded-lg border border-green-200">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-green-700">Système actif</span>
            </div>

            {/* User Menu */}
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="w-8 h-8 bg-gradient-to-br from-gray-600 to-gray-700 rounded-lg flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
                <div className="hidden sm:block text-left">
                  <p className="text-sm font-medium text-gray-900">
                    {user.full_name || user.username}
                  </p>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${getRoleColor(user.role)}`}>
                      {getRoleDisplay(user.role)}
                    </span>
                  </div>
                </div>
                <ChevronDown className="w-4 h-4 text-gray-400" />
              </button>

              {/* Dropdown Menu */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-lg border border-gray-200 py-2 z-50">
                  {/* User Info */}
                  <div className="px-4 py-3 border-b border-gray-100">
                    <p className="font-medium text-gray-900">{user.full_name || user.username}</p>
                    <p className="text-sm text-gray-600">@{user.username}</p>
                    {user.department && (
                      <p className="text-xs text-gray-500">{user.department}</p>
                    )}
                    <div className="mt-2">
                      <span className={`inline-flex text-xs px-2 py-1 rounded-full border font-medium ${getRoleColor(user.role)}`}>
                        {getRoleDisplay(user.role)}
                      </span>
                    </div>
                  </div>

                  {/* Menu Items */}
                  <div className="py-2">
                    <button
                      className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <Settings className="w-4 h-4" />
                      Paramètres
                    </button>
                    
                    <button
                      onClick={() => {
                        onLogout();
                        setShowUserMenu(false);
                      }}
                      className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                    >
                      <LogOut className="w-4 h-4" />
                      Se déconnecter
                    </button>
                  </div>

                  {/* Footer */}
                  <div className="px-4 py-2 border-t border-gray-100">
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <Shield className="w-3 h-3 text-green-600" />
                      <span>Session sécurisée</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Subtle gradient line */}
      <div className="h-px bg-gradient-to-r from-transparent via-green-200 to-transparent"></div>
    </header>
  );
};

export default Header;