import type { AppProps } from 'next/app';
import { useEffect, useState } from 'react';
import '@/styles/globals.css';
import { wsManager } from '@/lib/websocket';
import ErrorBoundary from '@/components/ErrorBoundary';

export default function App({ Component, pageProps }: AppProps) {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Initialize WebSocket connection
    wsManager.connect();

    // Listen for connection status
    const handleConnected = () => setIsConnected(true);
    const handleDisconnected = () => setIsConnected(false);

    wsManager.subscribe('connected', handleConnected);
    wsManager.subscribe('disconnected', handleDisconnected);

    // Cleanup on unmount
    return () => {
      wsManager.unsubscribe('connected', handleConnected);
      wsManager.unsubscribe('disconnected', handleDisconnected);
    };
  }, []);

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        {/* Connection Status */}
        {!isConnected && (
          <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-2">
            <div className="flex items-center justify-center">
              <div className="flex items-center space-x-2 text-yellow-800">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600"></div>
                <span className="text-sm">Connecting to server...</span>
              </div>
            </div>
          </div>
        )}

        <Component {...pageProps} />
      </div>
    </ErrorBoundary>
  );
}