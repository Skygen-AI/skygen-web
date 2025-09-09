"use client";

import React, { useState } from 'react';
import SkygenAuth from '@/components/SkygenAuth';
import { StatusResponse } from '@/services/skygenService';

export default function SkygenSetupPage() {
  const [status, setStatus] = useState<StatusResponse | null>(null);

  const handleStatusChange = (newStatus: StatusResponse) => {
    setStatus(newStatus);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Skygen Desktop Agent Setup
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            Connect your device to the Skygen AI automation platform
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Основная форма настройки */}
          <div>
            <SkygenAuth onStatusChange={handleStatusChange} />
          </div>

          {/* Информационная панель */}
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4">What happens next?</h3>
              <div className="space-y-3 text-sm text-gray-600 dark:text-gray-300">
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold">1</div>
                  <div>
                    <div className="font-medium">Install Dependencies</div>
                    <div>Python packages for desktop automation will be installed</div>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold">2</div>
                  <div>
                    <div className="font-medium">Authentication</div>
                    <div>Login or create an account on Skygen platform</div>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold">3</div>
                  <div>
                    <div className="font-medium">Device Registration</div>
                    <div>Your device will be registered and receive a secure token</div>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold">4</div>
                  <div>
                    <div className="font-medium">WebSocket Connection</div>
                    <div>Real-time connection to receive and execute tasks</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Системная информация */}
            {status && (
              <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold mb-4">System Information</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-300">Platform:</span>
                    <span className="font-medium">{status.platform}</span>
                  </div>
                  {status.device_id && (
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-300">Device ID:</span>
                      <span className="font-mono text-xs">{status.device_id}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-300">Desktop Env:</span>
                    <span className={`font-medium ${status.desktop_env_available ? 'text-green-600' : 'text-red-600'}`}>
                      {status.desktop_env_available ? 'Available' : 'Not Available'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Возможности системы */}
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Capabilities</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Screen Capture</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Mouse Control</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Keyboard Input</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>File Operations</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Window Management</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Accessibility Tree</span>
                </div>
              </div>
            </div>

            {/* Безопасность */}
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2 text-blue-800 dark:text-blue-200">Security</h3>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                All communications are encrypted and authenticated. Your device receives a unique token 
                that can be revoked at any time. Tasks are executed locally with full audit logging.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
