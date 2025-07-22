/**
 * Real-time preview component for video generation pipeline
 * Provides live previews of content as it's being generated
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';
import { 
  Play, 
  Pause, 
  Square, 
  Volume2, 
  VolumeX, 
  Maximize2, 
  Download,
  RefreshCw,
  Eye,
  EyeOff,
  Settings
} from 'lucide-react';
import { useWebSocket } from '../../lib/websocket';
import { performanceMonitor } from '../../lib/performance-monitor';

interface PreviewFrame {
  id: string;
  type: 'image' | 'video' | 'audio' | 'text';
  data: string | ArrayBuffer;
  timestamp: number;
  metadata: {
    quality?: number;
    resolution?: string;
    format?: string;
    duration?: number;
    size?: number;
  };
}

interface PreviewState {
  isActive: boolean;
  currentFrame?: PreviewFrame;
  frames: PreviewFrame[];
  isPlaying: boolean;
  isMuted: boolean;
  volume: number;
  playbackSpeed: number;
  quality: 'low' | 'medium' | 'high' | 'auto';
  autoRefresh: boolean;
}

interface RealTimePreviewProps {
  jobId?: string;
  stage?: 'script' | 'images' | 'audio' | 'video' | 'assembly';
  enableAudio?: boolean;
  enableVideo?: boolean;
  enableControls?: boolean;
  maxFrames?: number;
  refreshInterval?: number;
  quality?: 'low' | 'medium' | 'high' | 'auto';
  onPreviewReady?: (preview: PreviewFrame) => void;
  onError?: (error: string) => void;
}

export const RealTimePreview: React.FC<RealTimePreviewProps> = ({
  jobId,
  stage = 'images',
  enableAudio = true,
  enableVideo = true,
  enableControls = true,
  maxFrames = 50,
  refreshInterval = 1000,
  quality = 'auto',
  onPreviewReady,
  onError
}) => {
  const [state, setState] = useState<PreviewState>({
    isActive: false,
    frames: [],
    isPlaying: false,
    isMuted: false,
    volume: 0.7,
    playbackSpeed: 1.0,
    quality,
    autoRefresh: true
  });

  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');

  const previewRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const refreshIntervalRef = useRef<NodeJS.Timeout>();

  const { socket, isConnected } = useWebSocket();

  // Initialize preview system
  useEffect(() => {
    if (jobId && isConnected) {
      startPreview();
    } else {
      stopPreview();
    }

    return () => {
      stopPreview();
    };
  }, [jobId, isConnected]);

  // Handle WebSocket messages
  useEffect(() => {
    if (!socket) return;

    const handlePreviewFrame = (data: any) => {
      if (data.jobId === jobId) {
        handleNewFrame(data.frame);
      }
    };

    const handlePreviewUpdate = (data: any) => {
      if (data.jobId === jobId) {
        updatePreviewState(data);
      }
    };

    const handlePreviewError = (data: any) => {
      if (data.jobId === jobId) {
        onError?.(data.error);
        performanceMonitor.recordInteraction('preview_error', 'RealTimePreview', 0, false, data.error);
      }
    };

    socket.on('preview_frame', handlePreviewFrame);
    socket.on('preview_update', handlePreviewUpdate);
    socket.on('preview_error', handlePreviewError);

    return () => {
      socket.off('preview_frame', handlePreviewFrame);
      socket.off('preview_update', handlePreviewUpdate);
      socket.off('preview_error', handlePreviewError);
    };
  }, [socket, jobId, onError]);

  // Auto-refresh logic
  useEffect(() => {
    if (state.autoRefresh && state.isActive) {
      refreshIntervalRef.current = setInterval(() => {
        requestPreviewUpdate();
      }, refreshInterval);
    } else {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
        refreshIntervalRef.current = undefined;
      }
    }

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [state.autoRefresh, state.isActive, refreshInterval]);

  const startPreview = useCallback(() => {
    setConnectionStatus('connecting');
    
    setState(prev => ({ ...prev, isActive: true }));

    // Request initial preview data
    if (socket && jobId) {
      socket.emit('start_preview', {
        jobId,
        stage,
        quality: state.quality,
        options: {
          enableAudio,
          enableVideo,
          maxFrames
        }
      });

      performanceMonitor.recordInteraction('preview_start', 'RealTimePreview', 0, true);
      setConnectionStatus('connected');
    }
  }, [socket, jobId, stage, enableAudio, enableVideo, maxFrames, state.quality]);

  const stopPreview = useCallback(() => {
    setState(prev => ({
      ...prev,
      isActive: false,
      isPlaying: false
    }));

    if (socket && jobId) {
      socket.emit('stop_preview', { jobId });
    }

    setConnectionStatus('disconnected');
    performanceMonitor.recordInteraction('preview_stop', 'RealTimePreview', 0, true);
  }, [socket, jobId]);

  const requestPreviewUpdate = useCallback(() => {
    if (socket && jobId && state.isActive) {
      socket.emit('request_preview_update', {
        jobId,
        stage,
        timestamp: Date.now()
      });
    }
  }, [socket, jobId, stage, state.isActive]);

  const handleNewFrame = useCallback((frame: PreviewFrame) => {
    setState(prev => {
      const newFrames = [...prev.frames, frame];
      
      // Limit frame buffer size
      if (newFrames.length > maxFrames) {
        newFrames.splice(0, newFrames.length - maxFrames);
      }

      const newState = {
        ...prev,
        frames: newFrames,
        currentFrame: frame
      };

      return newState;
    });

    // Render the new frame
    renderFrame(frame);

    onPreviewReady?.(frame);
    performanceMonitor.recordMetric('preview_frame_received', 1, { 
      type: frame.type, 
      stage,
      quality: frame.metadata.quality?.toString() || 'unknown'
    });
  }, [maxFrames, onPreviewReady, stage]);

  const updatePreviewState = useCallback((update: any) => {
    setState(prev => ({
      ...prev,
      ...update
    }));
  }, []);

  const renderFrame = useCallback((frame: PreviewFrame) => {
    if (!previewRef.current) return;

    const startTime = performance.now();

    try {
      switch (frame.type) {
        case 'image':
          renderImageFrame(frame);
          break;
        case 'video':
          renderVideoFrame(frame);
          break;
        case 'audio':
          renderAudioFrame(frame);
          break;
        case 'text':
          renderTextFrame(frame);
          break;
      }

      const renderTime = performance.now() - startTime;
      performanceMonitor.recordMetric('preview_render_time', renderTime, {
        type: frame.type,
        stage
      });

    } catch (error) {
      console.error('Failed to render preview frame:', error);
      onError?.(error instanceof Error ? error.message : 'Render failed');
      
      performanceMonitor.recordInteraction(
        'preview_render_error', 
        'RealTimePreview', 
        performance.now() - startTime,
        false,
        error instanceof Error ? error.message : 'Unknown error'
      );
    }
  }, [onError, stage]);

  const renderImageFrame = (frame: PreviewFrame) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      // Adjust canvas size to maintain aspect ratio
      const aspectRatio = img.width / img.height;
      const maxWidth = canvas.parentElement?.clientWidth || 400;
      const maxHeight = canvas.parentElement?.clientHeight || 300;

      let canvasWidth = maxWidth;
      let canvasHeight = maxWidth / aspectRatio;

      if (canvasHeight > maxHeight) {
        canvasHeight = maxHeight;
        canvasWidth = maxHeight * aspectRatio;
      }

      canvas.width = canvasWidth;
      canvas.height = canvasHeight;

      // Clear and draw
      ctx.clearRect(0, 0, canvasWidth, canvasHeight);
      ctx.drawImage(img, 0, 0, canvasWidth, canvasHeight);

      // Add quality indicator
      if (frame.metadata.quality !== undefined) {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(5, 5, 80, 20);
        ctx.fillStyle = 'white';
        ctx.font = '12px Arial';
        ctx.fillText(`Q: ${Math.round(frame.metadata.quality * 100)}%`, 10, 18);
      }
    };

    if (typeof frame.data === 'string') {
      img.src = frame.data.startsWith('data:') ? frame.data : `data:image/jpeg;base64,${frame.data}`;
    }
  };

  const renderVideoFrame = (frame: PreviewFrame) => {
    const video = videoRef.current;
    if (!video || !enableVideo) return;

    if (typeof frame.data === 'string') {
      video.src = frame.data.startsWith('data:') ? frame.data : `data:video/mp4;base64,${frame.data}`;
      video.volume = state.isMuted ? 0 : state.volume;
      video.playbackRate = state.playbackSpeed;

      if (state.isPlaying) {
        video.play().catch(error => {
          console.warn('Video playback failed:', error);
        });
      }
    }
  };

  const renderAudioFrame = (frame: PreviewFrame) => {
    const audio = audioRef.current;
    if (!audio || !enableAudio) return;

    if (typeof frame.data === 'string') {
      audio.src = frame.data.startsWith('data:') ? frame.data : `data:audio/wav;base64,${frame.data}`;
      audio.volume = state.isMuted ? 0 : state.volume;

      if (state.isPlaying) {
        audio.play().catch(error => {
          console.warn('Audio playback failed:', error);
        });
      }
    }
  };

  const renderTextFrame = (frame: PreviewFrame) => {
    if (!previewRef.current) return;

    const textDisplay = previewRef.current.querySelector('.text-preview');
    if (textDisplay && typeof frame.data === 'string') {
      textDisplay.textContent = frame.data;
    }
  };

  const togglePlayback = useCallback(() => {
    setState(prev => ({ ...prev, isPlaying: !prev.isPlaying }));
    
    if (videoRef.current) {
      if (state.isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play().catch(console.warn);
      }
    }

    if (audioRef.current) {
      if (state.isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play().catch(console.warn);
      }
    }

    performanceMonitor.recordInteraction('preview_playback_toggle', 'RealTimePreview', 0, true);
  }, [state.isPlaying]);

  const toggleMute = useCallback(() => {
    setState(prev => ({ ...prev, isMuted: !prev.isMuted }));
    
    if (videoRef.current) {
      videoRef.current.muted = !state.isMuted;
    }
    if (audioRef.current) {
      audioRef.current.muted = !state.isMuted;
    }

    performanceMonitor.recordInteraction('preview_mute_toggle', 'RealTimePreview', 0, true);
  }, [state.isMuted]);

  const handleVolumeChange = useCallback((volume: number) => {
    setState(prev => ({ ...prev, volume }));
    
    if (videoRef.current) {
      videoRef.current.volume = volume;
    }
    if (audioRef.current) {
      audioRef.current.volume = volume;
    }
  }, []);

  const toggleFullscreen = useCallback(() => {
    if (!isFullscreen && previewRef.current) {
      previewRef.current.requestFullscreen?.().catch(console.warn);
      setIsFullscreen(true);
    } else if (document.fullscreenElement) {
      document.exitFullscreen().catch(console.warn);
      setIsFullscreen(false);
    }

    performanceMonitor.recordInteraction('preview_fullscreen_toggle', 'RealTimePreview', 0, true);
  }, [isFullscreen]);

  const downloadCurrentFrame = useCallback(() => {
    if (!state.currentFrame) return;

    const link = document.createElement('a');
    const filename = `preview_${state.currentFrame.type}_${Date.now()}.${getFileExtension(state.currentFrame)}`;
    
    if (typeof state.currentFrame.data === 'string') {
      link.href = state.currentFrame.data;
      link.download = filename;
      link.click();
    }

    performanceMonitor.recordInteraction('preview_download', 'RealTimePreview', 0, true);
  }, [state.currentFrame]);

  const getFileExtension = (frame: PreviewFrame): string => {
    switch (frame.type) {
      case 'image': return 'jpg';
      case 'video': return 'mp4';
      case 'audio': return 'wav';
      case 'text': return 'txt';
      default: return 'bin';
    }
  };

  const getConnectionStatusColor = (): string => {
    switch (connectionStatus) {
      case 'connected': return 'bg-green-500';
      case 'connecting': return 'bg-yellow-500';
      case 'disconnected': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">
          Real-time Preview
          {stage && (
            <Badge variant="secondary" className="ml-2">
              {stage.charAt(0).toUpperCase() + stage.slice(1)}
            </Badge>
          )}
        </CardTitle>
        
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${getConnectionStatusColor()}`} />
          <span className="text-xs text-muted-foreground">
            {connectionStatus}
          </span>
          
          {enableControls && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setState(prev => ({ ...prev, autoRefresh: !prev.autoRefresh }))}
              >
                {state.autoRefresh ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSettings(!showSettings)}
              >
                <Settings className="w-4 h-4" />
              </Button>
            </>
          )}
        </div>
      </CardHeader>

      <CardContent>
        <div 
          ref={previewRef}
          className={`relative bg-black rounded-lg overflow-hidden ${
            isFullscreen ? 'fixed inset-0 z-50' : 'aspect-video'
          }`}
        >
          {/* Canvas for image rendering */}
          <canvas
            ref={canvasRef}
            className="w-full h-full object-contain"
            style={{ display: stage === 'images' ? 'block' : 'none' }}
          />

          {/* Video element */}
          {enableVideo && (
            <video
              ref={videoRef}
              className="w-full h-full object-contain"
              style={{ display: stage === 'video' ? 'block' : 'none' }}
              controls={false}
              muted={state.isMuted}
            />
          )}

          {/* Audio element */}
          {enableAudio && (
            <audio
              ref={audioRef}
              style={{ display: 'none' }}
              controls={false}
              muted={state.isMuted}
            />
          )}

          {/* Text preview */}
          {stage === 'script' && (
            <div className="text-preview w-full h-full p-4 text-white overflow-auto">
              {state.currentFrame?.type === 'text' && typeof state.currentFrame.data === 'string' 
                ? state.currentFrame.data 
                : 'No text content available'
              }
            </div>
          )}

          {/* Loading state */}
          {!state.currentFrame && state.isActive && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="flex flex-col items-center space-y-2">
                <RefreshCw className="w-8 h-8 animate-spin text-white" />
                <p className="text-white text-sm">Loading preview...</p>
              </div>
            </div>
          )}

          {/* Frame info overlay */}
          {state.currentFrame && (
            <div className="absolute bottom-2 left-2 bg-black bg-opacity-70 text-white px-2 py-1 rounded text-xs">
              {state.currentFrame.type} | 
              {state.currentFrame.metadata.resolution && ` ${state.currentFrame.metadata.resolution} |`}
              {state.currentFrame.metadata.size && ` ${formatBytes(state.currentFrame.metadata.size)}`}
            </div>
          )}

          {/* Controls overlay */}
          {enableControls && state.currentFrame && (
            <div className="absolute bottom-2 right-2 flex space-x-2">
              {(enableVideo || enableAudio) && (
                <>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={togglePlayback}
                  >
                    {state.isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </Button>
                  
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={toggleMute}
                  >
                    {state.isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                  </Button>
                </>
              )}

              <Button
                variant="secondary"
                size="sm"
                onClick={downloadCurrentFrame}
              >
                <Download className="w-4 h-4" />
              </Button>

              <Button
                variant="secondary"
                size="sm"
                onClick={toggleFullscreen}
              >
                <Maximize2 className="w-4 h-4" />
              </Button>
            </div>
          )}
        </div>

        {/* Status and progress */}
        {state.isActive && (
          <div className="mt-4 space-y-2">
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>Frames: {state.frames.length}/{maxFrames}</span>
              {state.currentFrame && (
                <span>
                  Quality: {state.currentFrame.metadata.quality 
                    ? `${Math.round(state.currentFrame.metadata.quality * 100)}%`
                    : 'Unknown'
                  }
                </span>
              )}
            </div>
            
            <Progress value={(state.frames.length / maxFrames) * 100} className="h-2" />
          </div>
        )}

        {/* Settings panel */}
        {showSettings && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg space-y-3">
            <div className="flex justify-between items-center">
              <label className="text-sm font-medium">Quality</label>
              <select
                value={state.quality}
                onChange={(e) => setState(prev => ({ 
                  ...prev, 
                  quality: e.target.value as 'low' | 'medium' | 'high' | 'auto'
                }))}
                className="px-2 py-1 border rounded text-sm"
              >
                <option value="auto">Auto</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>

            {(enableVideo || enableAudio) && (
              <>
                <div className="flex justify-between items-center">
                  <label className="text-sm font-medium">Volume</label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={state.volume}
                    onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                    className="w-24"
                  />
                </div>

                <div className="flex justify-between items-center">
                  <label className="text-sm font-medium">Playback Speed</label>
                  <select
                    value={state.playbackSpeed}
                    onChange={(e) => setState(prev => ({ 
                      ...prev, 
                      playbackSpeed: parseFloat(e.target.value)
                    }))}
                    className="px-2 py-1 border rounded text-sm"
                  >
                    <option value="0.5">0.5x</option>
                    <option value="1">1x</option>
                    <option value="1.5">1.5x</option>
                    <option value="2">2x</option>
                  </select>
                </div>
              </>
            )}

            <div className="flex justify-between items-center">
              <label className="text-sm font-medium">Auto Refresh</label>
              <input
                type="checkbox"
                checked={state.autoRefresh}
                onChange={(e) => setState(prev => ({ 
                  ...prev, 
                  autoRefresh: e.target.checked
                }))}
              />
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="mt-4 flex space-x-2">
          {!state.isActive ? (
            <Button onClick={startPreview} disabled={!jobId || !isConnected}>
              <Play className="w-4 h-4 mr-2" />
              Start Preview
            </Button>
          ) : (
            <Button onClick={stopPreview} variant="outline">
              <Square className="w-4 h-4 mr-2" />
              Stop Preview
            </Button>
          )}

          <Button
            variant="outline"
            onClick={requestPreviewUpdate}
            disabled={!state.isActive}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default RealTimePreview;