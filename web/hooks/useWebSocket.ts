import { useEffect, useState, useCallback } from 'react';
import { wsManager } from '../lib/websocket';

export interface UseWebSocketReturn {
  socket: typeof wsManager | null;
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected';
  error: string | null;
  subscribe: (event: string, callback: (data: any) => void) => void;
  unsubscribe: (event: string, callback: (data: any) => void) => void;
  emit: (event: string, data: any) => void;
}

export const useWebSocket = (): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Set up connection status listeners
    const handleConnected = () => {
      setIsConnected(true);
      setConnectionStatus('connected');
      setError(null);
    };

    const handleDisconnected = () => {
      setIsConnected(false);
      setConnectionStatus('disconnected');
    };

    const handleConnectionError = (data: { error: any }) => {
      setIsConnected(false);
      setConnectionStatus('disconnected');
      setError(data.error?.message || 'Connection failed');
    };

    // Subscribe to connection events
    wsManager.subscribe('connected', handleConnected);
    wsManager.subscribe('disconnected', handleDisconnected);
    wsManager.subscribe('connection_error', handleConnectionError);

    // Initialize connection if not already connected
    if (!wsManager.isConnected()) {
      setConnectionStatus('connecting');
      wsManager.connect();
    } else {
      setIsConnected(true);
      setConnectionStatus('connected');
    }

    // Cleanup on unmount
    return () => {
      wsManager.unsubscribe('connected', handleConnected);
      wsManager.unsubscribe('disconnected', handleDisconnected);
      wsManager.unsubscribe('connection_error', handleConnectionError);
    };
  }, []);

  const subscribe = useCallback((event: string, callback: (data: any) => void) => {
    wsManager.subscribe(event, callback);
  }, []);

  const unsubscribe = useCallback((event: string, callback: (data: any) => void) => {
    wsManager.unsubscribe(event, callback);
  }, []);

  const emit = useCallback((event: string, data: any) => {
    wsManager.emit(event, data);
  }, []);

  return {
    socket: wsManager,
    isConnected,
    connectionStatus,
    error,
    subscribe,
    unsubscribe,
    emit
  };
};

export default useWebSocket;