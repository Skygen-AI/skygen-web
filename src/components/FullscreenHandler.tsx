"use client";

import { useEffect } from 'react';

export default function FullscreenHandler() {
  useEffect(() => {
    let isFullscreen = false;

    // Check if we're in Tauri
    const isTauri = typeof window !== 'undefined' && (window as any).__TAURI__;

    async function detectFullscreenState() {
      if (isTauri) {
        try {
          const { getCurrentWindow } = await import('@tauri-apps/api/window');
          const currentWindow = getCurrentWindow();
          
          // Monitor window state changes
          const unlisten = await currentWindow.listen('tauri://resize', async () => {
            try {
              const isFullscreenNow = await currentWindow.isFullscreen();
              
              if (isFullscreenNow !== isFullscreen) {
                isFullscreen = isFullscreenNow;
                
                if (isFullscreen) {
                  document.body.classList.add('fullscreen');
                  document.documentElement.style.height = '100vh';
                  document.documentElement.style.width = '100vw';
                  console.log('🖥️ Entered fullscreen mode');
                } else {
                  document.body.classList.remove('fullscreen');
                  document.documentElement.style.height = '';
                  document.documentElement.style.width = '';
                  console.log('🪟 Exited fullscreen mode');
                }
              }
            } catch (error) {
              console.error('Error checking fullscreen state:', error);
            }
          });

          // Check initial state
          try {
            const initialFullscreen = await currentWindow.isFullscreen();
            if (initialFullscreen) {
              document.body.classList.add('fullscreen');
              document.documentElement.style.height = '100vh';
              document.documentElement.style.width = '100vw';
            }
          } catch (error) {
            console.error('Error checking initial fullscreen state:', error);
          }

          // Cleanup function
          return () => {
            unlisten();
          };
        } catch (error) {
          console.error('Error setting up Tauri fullscreen detection:', error);
        }
      }
    }

    detectFullscreenState();
  }, []);

  return null; // This component doesn't render anything
}
