"use client";

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { SkygenService, StatusResponse } from '@/services/skygenService';
import { CheckCircle, XCircle, AlertCircle, Loader2, Wifi, WifiOff, Monitor, User } from 'lucide-react';

interface SkygenAuthProps {
  onStatusChange?: (status: StatusResponse) => void;
}

export const SkygenAuth: React.FC<SkygenAuthProps> = ({ onStatusChange }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSignup, setIsSignup] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isInstalling, setIsInstalling] = useState(false);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const skygenService = SkygenService.getInstance();

  // Загружаем статус при монтировании
  useEffect(() => {
    loadStatus();
  }, []);

  // Уведомляем родительский компонент об изменении статуса
  useEffect(() => {
    if (status && onStatusChange) {
      onStatusChange(status);
    }
  }, [status, onStatusChange]);

  const loadStatus = async () => {
    try {
      const currentStatus = await skygenService.getStatus();
      setStatus(currentStatus);
    } catch (error) {
      console.error('Failed to load status:', error);
      setError('Failed to load system status');
    }
  };

  const handleInstallDependencies = async () => {
    setIsInstalling(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await skygenService.installDependencies();
      setSuccess(result);
      
      // Обновляем статус после установки
      setTimeout(() => {
        loadStatus();
      }, 1000);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Installation failed');
    } finally {
      setIsInstalling(false);
    }
  };

  const handleAuth = async () => {
    if (!email || !password) {
      setError('Please enter email and password');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await skygenService.fullSetup(email, password, isSignup);
      
      setSuccess(
        `Successfully ${isSignup ? 'registered and' : ''} logged in! Device enrolled and connected.`
      );
      
      // Обновляем статус
      await loadStatus();
      
      // Очищаем форму
      setEmail('');
      setPassword('');
      
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    skygenService.logout();
    setStatus(null);
    setSuccess('Logged out successfully');
    setError(null);
    loadStatus();
  };

  const handleConnect = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const connected = await skygenService.connect();
      if (connected) {
        setSuccess('Connected to Skygen backend!');
        await loadStatus();
      } else {
        setError('Failed to connect');
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Connection failed');
    } finally {
      setIsLoading(false);
    }
  };

  const StatusIndicator: React.FC<{ 
    label: string; 
    status: boolean; 
    icon: React.ReactNode;
    color?: string;
  }> = ({ label, status, icon, color }) => (
    <div className="flex items-center space-x-2 p-2 rounded-lg bg-gray-50 dark:bg-gray-800">
      <div className={`p-1 rounded-full ${status ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}>
        {icon}
      </div>
      <span className="text-sm font-medium">{label}</span>
      <div className="ml-auto">
        {status ? (
          <CheckCircle className="h-4 w-4 text-green-600" />
        ) : (
          <XCircle className="h-4 w-4 text-red-600" />
        )}
      </div>
    </div>
  );

  return (
    <div className="max-w-md mx-auto p-6 bg-white dark:bg-gray-900 rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold text-center mb-6">Skygen Setup</h2>

      {/* Статус системы */}
      {status && (
        <div className="mb-6 space-y-2">
          <h3 className="text-lg font-semibold mb-3">System Status</h3>
          
          <StatusIndicator
            label="Desktop Environment"
            status={status.desktop_env_available}
            icon={<Monitor className="h-4 w-4" />}
          />
          
          <StatusIndicator
            label="Authenticated"
            status={status.authenticated}
            icon={<User className="h-4 w-4" />}
          />
          
          <StatusIndicator
            label="Device Enrolled"
            status={status.device_enrolled}
            icon={<Monitor className="h-4 w-4" />}
          />
          
          <StatusIndicator
            label="Connected"
            status={status.connected}
            icon={status.connected ? <Wifi className="h-4 w-4" /> : <WifiOff className="h-4 w-4" />}
          />

          {status.device_id && (
            <div className="text-xs text-gray-500 mt-2">
              Device ID: {status.device_id.slice(0, 8)}...
            </div>
          )}
        </div>
      )}

      {/* Сообщения об ошибках и успехе */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center">
            <AlertCircle className="h-4 w-4 text-red-600 mr-2" />
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
          <div className="flex items-center">
            <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
            <p className="text-sm text-green-600">{success}</p>
          </div>
        </div>
      )}

      {/* Установка зависимостей */}
      {!status?.desktop_env_available && (
        <div className="mb-6">
          <p className="text-sm text-gray-600 mb-3">
            Desktop environment is not available. Install Python dependencies first.
          </p>
          <Button
            onClick={handleInstallDependencies}
            disabled={isInstalling}
            className="w-full"
            variant="outline"
          >
            {isInstalling && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Install Dependencies
          </Button>
        </div>
      )}

      {/* Форма авторизации */}
      {!status?.authenticated && status?.desktop_env_available && (
        <div className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600"
              placeholder="your@email.com"
              disabled={isLoading}
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600"
              placeholder="••••••••"
              disabled={isLoading}
              onKeyPress={(e) => e.key === 'Enter' && handleAuth()}
            />
          </div>

          <div className="flex items-center">
            <input
              id="signup"
              type="checkbox"
              checked={isSignup}
              onChange={(e) => setIsSignup(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              disabled={isLoading}
            />
            <label htmlFor="signup" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
              Create new account
            </label>
          </div>

          <Button
            onClick={handleAuth}
            disabled={isLoading}
            className="w-full"
          >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isSignup ? 'Sign Up & Connect' : 'Login & Connect'}
          </Button>
        </div>
      )}

      {/* Управление подключением */}
      {status?.authenticated && (
        <div className="space-y-3">
          {!status.connected && (
            <Button
              onClick={handleConnect}
              disabled={isLoading}
              className="w-full"
            >
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Connect to Backend
            </Button>
          )}

          <Button
            onClick={handleLogout}
            variant="outline"
            className="w-full"
          >
            Logout
          </Button>
        </div>
      )}

      {/* Кнопка обновления статуса */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <Button
          onClick={loadStatus}
          variant="ghost"
          size="sm"
          className="w-full text-xs"
        >
          Refresh Status
        </Button>
      </div>
    </div>
  );
};

export default SkygenAuth;
