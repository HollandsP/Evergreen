import { io, Socket } from 'socket.io-client';

class WebSocketManager {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  connect(url?: string): void {
    // Use the Next.js server for Socket.io connection
    const socketUrl = url || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000');
    
    if (this.socket?.connected) {
      return;
    }

    try {
      this.socket = io(socketUrl, {
        path: '/api/socket',  // Important: specify the Socket.io path
        transports: ['websocket', 'polling'],
        timeout: 20000,
        forceNew: true,
        autoConnect: true,
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: this.reconnectDelay,
        reconnectionDelayMax: 10000,
      });

      this.setupEventHandlers();
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.emitToListeners('connection_error', { error });
    }
  }

  private setupEventHandlers(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.emitToListeners('connected', { connected: true });
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.emitToListeners('disconnected', { reason });
      
      if (reason === 'io server disconnect') {
        // Server disconnected, try to reconnect
        this.scheduleReconnect();
      }
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.scheduleReconnect();
    });

    // Job-related events
    this.socket.on('job_update', (data) => {
      this.emitToListeners('job_update', data);
    });

    this.socket.on('step_update', (data) => {
      this.emitToListeners('step_update', data);
    });

    this.socket.on('job_completed', (data) => {
      this.emitToListeners('job_completed', data);
    });

    this.socket.on('job_failed', (data) => {
      this.emitToListeners('job_failed', data);
    });

    this.socket.on('system_status', (data) => {
      this.emitToListeners('system_status', data);
    });

    // Video generation specific events
    this.socket.on('video_generation_started', (data) => {
      this.emitToListeners('video_generation_started', data);
    });

    this.socket.on('video_generation_progress', (data) => {
      this.emitToListeners('video_generation_progress', data);
    });

    this.socket.on('video_generation_completed', (data) => {
      this.emitToListeners('video_generation_completed', data);
    });

    this.socket.on('video_generation_failed', (data) => {
      this.emitToListeners('video_generation_failed', data);
    });

    // Script parsing events
    this.socket.on('script_parsing_progress', (data) => {
      this.emitToListeners('script_parsing_progress', data);
    });

    // Image generation events
    this.socket.on('image_generation_progress', (data) => {
      this.emitToListeners('image_generation_progress', data);
    });

    // Audio generation events
    this.socket.on('audio_generation_progress', (data) => {
      this.emitToListeners('audio_generation_progress', data);
    });
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    setTimeout(() => {
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      this.connect();
    }, delay);
  }

  subscribe(event: string, callback: (data: any) => void): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  unsubscribe(event: string, callback: (data: any) => void): void {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.delete(callback);
    }
  }

  private emitToListeners(event: string, data: any): void {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach(callback => callback(data));
    }
  }

  subscribeToJob(jobId: string): void {
    if (this.socket?.connected) {
      this.socket.emit('subscribe_job', { jobId });
    }
  }

  unsubscribeFromJob(jobId: string): void {
    if (this.socket?.connected) {
      this.socket.emit('unsubscribe_job', { jobId });
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.listeners.clear();
    this.reconnectAttempts = 0;
  }

  // Server-side emit method for broadcasting events
  emit(event: string, data: any): void {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    }
    // Also emit to local listeners
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach(callback => callback(data));
    }
  }

  // Subscribe to video generation updates for a specific job
  subscribeToVideoGeneration(jobId: string): void {
    if (this.socket?.connected) {
      this.socket.emit('subscribe_video_generation', { jobId });
    }
  }

  // Unsubscribe from video generation updates
  unsubscribeFromVideoGeneration(jobId: string): void {
    if (this.socket?.connected) {
      this.socket.emit('unsubscribe_video_generation', { jobId });
    }
  }

  // Send video generation status update (server-side)
  sendVideoGenerationUpdate(jobId: string, status: string, progress?: number, data?: any): void {
    const updateData = {
      jobId,
      status,
      progress,
      timestamp: new Date().toISOString(),
      ...data
    };

    switch (status) {
      case 'started':
        this.emit('video_generation_started', updateData);
        break;
      case 'progress':
        this.emit('video_generation_progress', updateData);
        break;
      case 'completed':
        this.emit('video_generation_completed', updateData);
        break;
      case 'failed':
        this.emit('video_generation_failed', updateData);
        break;
      default:
        this.emit('video_generation_update', updateData);
    }
  }
}

// Export singleton instance
export const wsManager = new WebSocketManager();
export default wsManager;
