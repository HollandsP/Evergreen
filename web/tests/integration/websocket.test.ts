import { wsManager } from '@/lib/websocket';
import { io, Socket } from 'socket.io-client';
import { act } from 'react-dom/test-utils';

// Mock socket.io-client
jest.mock('socket.io-client');

// Mock console to reduce test noise
const consoleSpy = {
  log: jest.spyOn(console, 'log').mockImplementation(() => {}),
  error: jest.spyOn(console, 'error').mockImplementation(() => {}),
};

describe('WebSocket Integration', () => {
  let mockSocket: any;
  let mockIo: jest.MockedFunction<typeof io>;

  beforeEach(() => {
    jest.clearAllMocks();
    consoleSpy.log.mockClear();
    consoleSpy.error.mockClear();
    
    // Create comprehensive mock socket
    mockSocket = {
      connected: false,
      id: 'test-socket-id',
      on: jest.fn(),
      emit: jest.fn(),
      disconnect: jest.fn(),
      connect: jest.fn(),
      off: jest.fn(),
      removeAllListeners: jest.fn(),
    };
    
    mockIo = io as jest.MockedFunction<typeof io>;
    mockIo.mockReturnValue(mockSocket as any);
  });

  afterEach(async () => {
    // Clean up more thoroughly
    wsManager.disconnect();
    // Wait for any pending promises to resolve
    await new Promise(resolve => setTimeout(resolve, 0));
  });

  describe('Connection Management', () => {
    it('should establish WebSocket connection', () => {
      wsManager.connect('ws://localhost:8000');
      
      expect(mockIo).toHaveBeenCalledWith('ws://localhost:8000', {
        transports: ['websocket', 'polling'],
        timeout: 20000,
        forceNew: true,
      });
      
      expect(mockSocket.on).toHaveBeenCalledWith('connect', expect.any(Function));
      expect(mockSocket.on).toHaveBeenCalledWith('disconnect', expect.any(Function));
      expect(mockSocket.on).toHaveBeenCalledWith('connect_error', expect.any(Function));
    });

    it('should handle successful connection', () => {
      const connectedCallback = jest.fn();
      wsManager.subscribe('connected', connectedCallback);
      wsManager.connect();
      
      // Simulate connection
      const connectHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'connect',
      )?.[1];
      
      mockSocket.connected = true;
      connectHandler?.();
      
      expect(connectedCallback).toHaveBeenCalledWith({ connected: true });
    });

    it('should handle disconnection and attempt reconnect', async () => {
      jest.useFakeTimers();
      
      try {
        const disconnectedCallback = jest.fn();
        wsManager.subscribe('disconnected', disconnectedCallback);
        wsManager.connect();
        
        // Simulate disconnection
        const disconnectHandler = mockSocket.on.mock.calls.find(
          call => call[0] === 'disconnect',
        )?.[1];
        
        if (disconnectHandler) {
          disconnectHandler('io server disconnect');
          
          expect(disconnectedCallback).toHaveBeenCalledWith({
            reason: 'io server disconnect',
          });
          
          // Fast-forward through reconnect delay
          await act(async () => {
            jest.advanceTimersByTime(1000);
          });
          
          // Verify reconnection attempt
          expect(mockIo).toHaveBeenCalledTimes(2);
        }
      } finally {
        jest.useRealTimers();
      }
    });

    it('should respect max reconnection attempts', async () => {
      jest.useFakeTimers();
      
      try {
        wsManager.connect();
        
        const errorHandler = mockSocket.on.mock.calls.find(
          call => call[0] === 'connect_error',
        )?.[1];
        
        if (!errorHandler) {
          throw new Error('connect_error handler not found');
        }
        
        // Simulate multiple connection errors with proper error handling
        for (let i = 0; i < 6; i++) {
          try {
            errorHandler(new Error('Connection failed'));
            // Advance timers more carefully
            await act(async () => {
              jest.advanceTimersByTime(Math.pow(2, i) * 1000);
            });
          } catch (error) {
            // Expected errors during reconnection attempts
            console.debug(`Reconnection attempt ${i + 1} failed as expected`);
          }
        }
        
        // Should stop after 5 attempts
        expect(mockIo).toHaveBeenCalledTimes(6); // Initial + 5 retries
      } finally {
        jest.useRealTimers();
      }
    });

    it('should handle multiple connections to same URL', () => {
      wsManager.connect('ws://localhost:8000');
      
      // Mock socket as connected
      mockSocket.connected = true;
      
      // Try to connect again
      wsManager.connect('ws://localhost:8000');
      
      // Should not create new connection
      expect(mockIo).toHaveBeenCalledTimes(1);
    });
  });

  describe('Event Subscription', () => {
    beforeEach(() => {
      wsManager.connect();
    });

    it('should subscribe to job updates', () => {
      const jobUpdateCallback = jest.fn();
      wsManager.subscribe('job_update', jobUpdateCallback);
      
      // Simulate job update event
      const jobUpdateHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'job_update',
      )?.[1];
      
      const testData = {
        jobId: 'test-job-1',
        progress: 50,
        status: 'generating',
      };
      
      jobUpdateHandler?.(testData);
      
      expect(jobUpdateCallback).toHaveBeenCalledWith(testData);
    });

    it('should handle multiple subscribers for same event', () => {
      const callback1 = jest.fn();
      const callback2 = jest.fn();
      
      wsManager.subscribe('step_update', callback1);
      wsManager.subscribe('step_update', callback2);
      
      // Simulate step update
      const stepUpdateHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'step_update',
      )?.[1];
      
      const testData = { step: 'audio', progress: 75 };
      stepUpdateHandler?.(testData);
      
      expect(callback1).toHaveBeenCalledWith(testData);
      expect(callback2).toHaveBeenCalledWith(testData);
    });

    it('should unsubscribe from events', () => {
      const callback = jest.fn();
      wsManager.subscribe('job_completed', callback);
      wsManager.unsubscribe('job_completed', callback);
      
      // Simulate job completion
      const jobCompletedHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'job_completed',
      )?.[1];
      
      jobCompletedHandler?.({ jobId: 'test-job' });
      
      expect(callback).not.toHaveBeenCalled();
    });

    it('should handle job failure events', () => {
      const failureCallback = jest.fn();
      wsManager.subscribe('job_failed', failureCallback);
      
      const jobFailedHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'job_failed',
      )?.[1];
      
      const errorData = {
        jobId: 'test-job',
        error: 'Generation failed',
        stage: 'video',
      };
      
      jobFailedHandler?.(errorData);
      
      expect(failureCallback).toHaveBeenCalledWith(errorData);
    });

    it('should handle system status updates', () => {
      const statusCallback = jest.fn();
      wsManager.subscribe('system_status', statusCallback);
      
      const statusHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'system_status',
      )?.[1];
      
      const statusData = {
        activeJobs: 5,
        queueLength: 10,
        systemLoad: 0.75,
      };
      
      statusHandler?.(statusData);
      
      expect(statusCallback).toHaveBeenCalledWith(statusData);
    });
  });

  describe('Job Management', () => {
    beforeEach(() => {
      wsManager.connect();
      mockSocket.connected = true;
    });

    it('should subscribe to specific job updates', () => {
      wsManager.subscribeToJob('job-123');
      
      expect(mockSocket.emit).toHaveBeenCalledWith('subscribe_job', {
        jobId: 'job-123',
      });
    });

    it('should unsubscribe from job updates', () => {
      wsManager.unsubscribeFromJob('job-123');
      
      expect(mockSocket.emit).toHaveBeenCalledWith('unsubscribe_job', {
        jobId: 'job-123',
      });
    });

    it('should not emit when disconnected', () => {
      mockSocket.connected = false;
      
      wsManager.subscribeToJob('job-123');
      
      expect(mockSocket.emit).not.toHaveBeenCalled();
    });
  });

  describe('Connection Status', () => {
    it('should report connection status correctly', () => {
      expect(wsManager.isConnected()).toBe(false);
      
      wsManager.connect();
      expect(wsManager.isConnected()).toBe(false);
      
      mockSocket.connected = true;
      expect(wsManager.isConnected()).toBe(true);
      
      wsManager.disconnect();
      expect(wsManager.isConnected()).toBe(false);
    });

    it('should clean up on disconnect', () => {
      const callback = jest.fn();
      wsManager.subscribe('test_event', callback);
      
      wsManager.connect();
      wsManager.disconnect();
      
      expect(mockSocket.disconnect).toHaveBeenCalled();
      
      // Verify event listeners are cleared
      // (would need to expose listeners for full verification)
    });
  });

  describe('Real-time Pipeline Updates', () => {
    beforeEach(() => {
      wsManager.connect();
      mockSocket.connected = true;
    });

    it('should handle audio generation progress', () => {
      const progressCallback = jest.fn();
      wsManager.subscribe('job_update', progressCallback);
      
      // Simulate audio generation progress
      const jobUpdateHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'job_update',
      )?.[1];
      
      const updates = [
        { jobId: 'audio-1', stage: 'audio', progress: 0 },
        { jobId: 'audio-1', stage: 'audio', progress: 25 },
        { jobId: 'audio-1', stage: 'audio', progress: 50 },
        { jobId: 'audio-1', stage: 'audio', progress: 75 },
        { jobId: 'audio-1', stage: 'audio', progress: 100 },
      ];
      
      updates.forEach(update => {
        jobUpdateHandler?.(update);
      });
      
      expect(progressCallback).toHaveBeenCalledTimes(5);
      expect(progressCallback).toHaveBeenLastCalledWith({
        jobId: 'audio-1',
        stage: 'audio',
        progress: 100,
      });
    });

    it('should handle batch job updates', () => {
      const updateCallback = jest.fn();
      wsManager.subscribe('job_update', updateCallback);
      
      const jobUpdateHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'job_update',
      )?.[1];
      
      // Simulate batch image generation
      const batchUpdates = [
        { jobId: 'batch-1', stage: 'images', progress: 20, completed: 1, total: 5 },
        { jobId: 'batch-1', stage: 'images', progress: 40, completed: 2, total: 5 },
        { jobId: 'batch-1', stage: 'images', progress: 60, completed: 3, total: 5 },
        { jobId: 'batch-1', stage: 'images', progress: 80, completed: 4, total: 5 },
        { jobId: 'batch-1', stage: 'images', progress: 100, completed: 5, total: 5 },
      ];
      
      batchUpdates.forEach(update => {
        jobUpdateHandler?.(update);
      });
      
      const lastCall = updateCallback.mock.calls[updateCallback.mock.calls.length - 1][0];
      expect(lastCall.completed).toBe(5);
      expect(lastCall.total).toBe(5);
    });

    it('should handle concurrent job updates', () => {
      const updateCallback = jest.fn();
      wsManager.subscribe('job_update', updateCallback);
      
      const jobUpdateHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'job_update',
      )?.[1];
      
      // Simulate concurrent jobs
      jobUpdateHandler?.({ jobId: 'audio-1', stage: 'audio', progress: 50 });
      jobUpdateHandler?.({ jobId: 'image-1', stage: 'images', progress: 30 });
      jobUpdateHandler?.({ jobId: 'video-1', stage: 'video', progress: 10 });
      
      expect(updateCallback).toHaveBeenCalledTimes(3);
      
      // Verify each job update was received
      const calls = updateCallback.mock.calls;
      expect(calls.some(call => call[0].jobId === 'audio-1')).toBe(true);
      expect(calls.some(call => call[0].jobId === 'image-1')).toBe(true);
      expect(calls.some(call => call[0].jobId === 'video-1')).toBe(true);
    });

    it('should handle error recovery during job processing', () => {
      const updateCallback = jest.fn();
      const failureCallback = jest.fn();
      
      wsManager.subscribe('job_update', updateCallback);
      wsManager.subscribe('job_failed', failureCallback);
      
      const jobUpdateHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'job_update',
      )?.[1];
      
      const jobFailedHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'job_failed',
      )?.[1];
      
      // Simulate job progress then failure
      jobUpdateHandler?.({ jobId: 'video-1', stage: 'video', progress: 30 });
      jobFailedHandler?.({ 
        jobId: 'video-1', 
        stage: 'video', 
        error: 'GPU memory exhausted',
        canRetry: true, 
      });
      
      expect(updateCallback).toHaveBeenCalledWith({
        jobId: 'video-1',
        stage: 'video',
        progress: 30,
      });
      
      expect(failureCallback).toHaveBeenCalledWith({
        jobId: 'video-1',
        stage: 'video',
        error: 'GPU memory exhausted',
        canRetry: true,
      });
    });
  });
});
