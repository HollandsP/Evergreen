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
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
        };
      case 'connecting':
        return {
          icon: WifiIcon,
          text: reconnectAttempts > 0 ? `Reconnecting... (${reconnectAttempts})` : 'Connecting...',
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
        };
      case 'error':
        return {
          icon: ExclamationTriangleIcon,
          text: 'Connection Error',
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
        };
      case 'disconnected':
      default:
        return {
          icon: WifiIcon,
          text: 'Disconnected',
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
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
