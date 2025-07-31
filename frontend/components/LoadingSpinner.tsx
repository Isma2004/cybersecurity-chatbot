import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  variant?: 'primary' | 'secondary' | 'white';
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  className = '',
  variant = 'primary'
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-6 h-6 border-2',
    lg: 'w-8 h-8 border-3',
    xl: 'w-12 h-12 border-4'
  };

  const variantClasses = {
    primary: 'border-gray-200 border-t-red-600',
    secondary: 'border-red-200 border-t-red-600',
    white: 'border-white/30 border-t-white'
  };

  return (
    <div className={`animate-spin rounded-full ${sizeClasses[size]} ${variantClasses[variant]} ${className}`} />
  );
};

export default LoadingSpinner;