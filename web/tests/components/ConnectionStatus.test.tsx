import { render, screen, act } from '@testing-library/react';
import ConnectionStatus from '@/components/shared/ConnectionStatus';

// Mock the WebSocket manager
jest.mock('@/lib/websocket', () => ({
  wsManager: {
    isConnected: jest.fn(() => false),
    subscribe: jest.fn(),
    unsubscribe: jest.fn(),
    connect: jest.fn(),
  },
}));

describe('ConnectionStatus', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders connecting status by default when not connected', () => {
    render(<ConnectionStatus />);
    
    expect(screen.getByText(/connecting/i)).toBeInTheDocument();
  });

  it('shows connected status when WebSocket is connected', () => {
    const { wsManager } = require('@/lib/websocket');
    wsManager.isConnected.mockReturnValue(true);
    
    render(<ConnectionStatus />);
    
    expect(screen.getByText(/connected/i)).toBeInTheDocument();
  });

  it('updates status when connection changes', () => {
    const { wsManager } = require('@/lib/websocket');
    let connectionCallback: (data: any) => void;
    
    wsManager.subscribe.mockImplementation((event: string, callback: (data: any) => void) => {
      if (event === 'connected') {
        connectionCallback = callback;
      }
    });
    
    wsManager.isConnected.mockReturnValue(false);
    render(<ConnectionStatus />);
    
    expect(screen.getByText(/connecting/i)).toBeInTheDocument();
    
    // Simulate connection event
    act(() => {
      wsManager.isConnected.mockReturnValue(true);
      connectionCallback?.({ connected: true });
    });
    
    expect(screen.getByText(/connected/i)).toBeInTheDocument();
  });

  it('shows appropriate visual indicators for connection state', () => {
    const { wsManager } = require('@/lib/websocket');
    
    // Test connecting state (default when not connected)
    wsManager.isConnected.mockReturnValue(false);
    const { rerender } = render(<ConnectionStatus />);
    
    const connectingText = screen.getByText(/connecting/i);
    expect(connectingText).toBeInTheDocument();
    
    // Test connected state
    wsManager.isConnected.mockReturnValue(true);
    rerender(<ConnectionStatus />);
    
    const connectedText = screen.getByText(/connected/i);
    expect(connectedText).toBeInTheDocument();
  });

  it('handles reconnection attempts', () => {
    const { wsManager } = require('@/lib/websocket');
    let disconnectedCallback: (data: any) => void;
    
    wsManager.subscribe.mockImplementation((event: string, callback: (data: any) => void) => {
      if (event === 'disconnected') {
        disconnectedCallback = callback;
      }
    });
    
    render(<ConnectionStatus />);
    
    // Simulate disconnection with reconnection
    act(() => {
      disconnectedCallback?.({ reason: 'transport close' });
    });
    
    expect(screen.getByText(/reconnecting/i)).toBeInTheDocument();
  });
});
