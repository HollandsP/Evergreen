import React, { useState, useEffect } from 'react';
import { 
  WifiIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import { wsManager } from '@/lib/websocket';
import { cn } from '@/lib/utils';

interface ConnectionStatusProps {
  className?: string;
}

type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error';

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ className }) => {
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  useEffect(() => {
    // Set initial state
    setConnectionState(wsManager.isConnected() ? 'connected' : 'connecting');

    // Attempt to connect
    wsManager.connect();

    // Subscribe to connection events
    const handleConnected = () => {
      setConnectionState('connected');
      setReconnectAttempts(0);
    };

    const handleDisconnected = () => {
      setConnectionState('disconnected');
    };

    const handleConnecting = () => {
      setConnectionState('connecting');
      setReconnectAttempts(prev => prev + 1);
    };

    const handleError = () => {
      setConnectionState('error');
    };

    wsManager.subscribe('connected', handleConnected);
    wsManager.subscribe('disconnected', handleDisconnected);
    wsManager.subscribe('connecting', handleConnecting);
    wsManager.subscribe('error', handleError);

    // Cleanup
    return () => {
      wsManager.unsubscribe('connected', handleConnected);
      wsManager.unsubscribe('disconnected', handleDisconnected);
      wsManager.unsubscribe('connecting', handleConnecting);
      wsManager.unsubscribe('error', handleError);
    };
  }, []);

  const getStatusConfig = () => {
    switch (connectionState) {
      case 'connected':
        return {
          icon: CheckCircleIcon,
          text: 'Connected',
          color: 'text-green-400',
          bgColor: 'bg-green-900/20',
          borderColor: 'border-green-600/50',
        };
      case 'connecting':
        return {
          icon: WifiIcon,
          text: reconnectAttempts > 0 ? `Reconnecting... (${reconnectAttempts})` : 'Connecting...',
          color: 'text-yellow-400',
          bgColor: 'bg-yellow-900/20',
          borderColor: 'border-yellow-600/50',
        };
      case 'error':
        return {
          icon: ExclamationTriangleIcon,
          text: 'Connection Error',
          color: 'text-red-400',
          bgColor: 'bg-red-900/20',
          borderColor: 'border-red-600/50',
        };
      case 'disconnected':
      default:
        return {
          icon: WifiIcon,
          text: 'Disconnected',
          color: 'text-zinc-400',
          bgColor: 'bg-zinc-800',
          borderColor: 'border-zinc-700',
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  const handleRetryConnection = () => {
    setConnectionState('connecting');
    wsManager.disconnect();
    setTimeout(() => {
      wsManager.connect();
    }, 1000);
  };

  return (
    <div className={cn('flex items-center space-x-2', className)}>
      <div
        className={cn(
          'flex items-center space-x-2 px-3 py-1 rounded-full border text-sm',
          config.color,
          config.bgColor,
          config.borderColor,
        )}
      >
        <Icon 
          className={cn(
            'h-4 w-4',
            connectionState === 'connecting' && 'animate-pulse',
          )} 
        />
        <span className="font-medium">{config.text}</span>
        
        {connectionState === 'error' && (
          <button
            onClick={handleRetryConnection}
            className="ml-2 text-xs underline hover:no-underline"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
};

export default ConnectionStatus;
