import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import wsManager from '../websocket';

interface VideoGenerationState {
  status: 'idle' | 'processing' | 'completed' | 'failed';
  progress: number;
  videoUrl?: string;
  error?: string;
  jobId?: string;
}

interface UseVideoGenerationOptions {
  projectId?: string;
  sceneId?: string;
  onProgress?: (progress: number) => void;
  onComplete?: (videoUrl: string) => void;
  onError?: (error: string) => void;
}

export function useVideoGeneration(options: UseVideoGenerationOptions = {}) {
  const [state, setState] = useState<VideoGenerationState>({
    status: 'idle',
    progress: 0,
  });

  useEffect(() => {
    // Subscribe to WebSocket events
    const handleVideoStarted = (data: any) => {
      if (data.jobId === state.jobId) {
        setState(prev => ({
          ...prev,
          status: 'processing',
          progress: 0,
        }));
      }
    };

    const handleVideoProgress = (data: any) => {
      if (data.jobId === state.jobId) {
        setState(prev => ({
          ...prev,
          progress: data.progress || prev.progress,
        }));
        options.onProgress?.(data.progress);
      }
    };

    const handleVideoCompleted = (data: any) => {
      if (data.jobId === state.jobId) {
        setState(prev => ({
          ...prev,
          status: 'completed',
          videoUrl: data.videoUrl,
          progress: 100,
        }));
        options.onComplete?.(data.videoUrl);
      }
    };

    const handleVideoFailed = (data: any) => {
      if (data.jobId === state.jobId) {
        setState(prev => ({
          ...prev,
          status: 'failed',
          error: data.error || 'Video generation failed',
        }));
        options.onError?.(data.error || 'Video generation failed');
      }
    };

    wsManager.subscribe('video_generation_started', handleVideoStarted);
    wsManager.subscribe('video_generation_progress', handleVideoProgress);
    wsManager.subscribe('video_generation_completed', handleVideoCompleted);
    wsManager.subscribe('video_generation_failed', handleVideoFailed);

    // Connect WebSocket if not connected
    if (!wsManager.isConnected()) {
      wsManager.connect();
    }

    return () => {
      wsManager.unsubscribe('video_generation_started', handleVideoStarted);
      wsManager.unsubscribe('video_generation_progress', handleVideoProgress);
      wsManager.unsubscribe('video_generation_completed', handleVideoCompleted);
      wsManager.unsubscribe('video_generation_failed', handleVideoFailed);
    };
  }, [state.jobId, options]);

  const generateVideo = useCallback(async (params: {
    imageUrl: string;
    prompt: string;
    duration: number;
    cameraMovement?: string;
    motionIntensity?: number;
    lipSync?: boolean;
    audioUrl?: string;
  }) => {
    try {
      setState({
        status: 'processing',
        progress: 0,
      });

      const response = await axios.post('/api/videos/generate', {
        ...params,
        projectId: options.projectId,
        sceneId: options.sceneId,
      });

      setState(prev => ({
        ...prev,
        jobId: response.data.jobId,
      }));

      if (response.data.jobId && wsManager.isConnected()) {
        wsManager.subscribeToJob(response.data.jobId);
      }

      return response.data;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate video';
      setState({
        status: 'failed',
        progress: 0,
        error: errorMessage,
      });
      options.onError?.(errorMessage);
      throw error;
    }
  }, [options.projectId, options.sceneId, options.onError]);

  const checkStatus = useCallback(async () => {
    if (!state.jobId) return;

    try {
      const response = await axios.get(`/api/videos/status/${state.jobId}`);
      const { status, progress, videoUrl, error } = response.data;

      setState(prev => ({
        ...prev,
        status: status === 'completed' ? 'completed' : 
                status === 'failed' ? 'failed' : 
                'processing',
        progress: progress || prev.progress,
        videoUrl: videoUrl || prev.videoUrl,
        error: error || prev.error,
      }));

      if (status === 'completed' && videoUrl) {
        options.onComplete?.(videoUrl);
      } else if (status === 'failed') {
        options.onError?.(error || 'Video generation failed');
      }

      return response.data;
    } catch (error) {
      console.error('Failed to check video status:', error);
    }
  }, [state.jobId, options]);

  const reset = useCallback(() => {
    setState({
      status: 'idle',
      progress: 0,
    });
  }, []);

  return {
    ...state,
    generateVideo,
    checkStatus,
    reset,
  };
}