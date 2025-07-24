import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { 
  PlayCircle, 
  PauseCircle, 
  Download, 
  RefreshCw, 
  Volume2, 
  VolumeX,
  Maximize,
  SkipBack,
  SkipForward,
  Clock,
  FileVideo,
  AlertCircle,
  Loader2
} from 'lucide-react';

interface VideoPreviewProps {
  operationId?: string;
  previewUrl?: string;
  outputPath?: string;
  operation?: {
    operation: string;
    parameters: any;
    confidence: number;
    explanation: string;
  };
  onDownload?: (operationId: string, outputPath: string) => void;
  className?: string;
}

export default function VideoPreview({ 
  operationId,
  previewUrl,
  outputPath,
  operation,
  onDownload,
  className = '' 
}: VideoPreviewProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [volume, setVolume] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleLoadedData = () => {
      setIsLoading(false);
      setDuration(video.duration);
    };

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
    };

    const handleError = () => {
      setError('Failed to load video preview');
      setIsLoading(false);
    };

    const handleEnded = () => {
      setIsPlaying(false);
    };

    video.addEventListener('loadeddata', handleLoadedData);
    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('error', handleError);
    video.addEventListener('ended', handleEnded);

    return () => {
      video.removeEventListener('loadeddata', handleLoadedData);
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('error', handleError);
      video.removeEventListener('ended', handleEnded);
    };
  }, [previewUrl]);

  const handlePlayPause = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.pause();
    } else {
      video.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleMuteToggle = () => {
    const video = videoRef.current;
    if (!video) return;

    video.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const handleVolumeChange = (newVolume: number) => {
    const video = videoRef.current;
    if (!video) return;

    video.volume = newVolume;
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
  };

  const handleSeek = (time: number) => {
    const video = videoRef.current;
    if (!video) return;

    video.currentTime = time;
    setCurrentTime(time);
  };

  const handleFullscreen = () => {
    const container = containerRef.current;
    if (!container) return;

    if (!isFullscreen) {
      if (container.requestFullscreen) {
        container.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
    setIsFullscreen(!isFullscreen);
  };

  const handleSkipBackward = () => {
    handleSeek(Math.max(0, currentTime - 10));
  };

  const handleSkipForward = () => {
    handleSeek(Math.min(duration, currentTime + 10));
  };

  const handleDownloadClick = () => {
    if (operationId && outputPath && onDownload) {
      onDownload(operationId, outputPath);
    }
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const getOperationBadgeColor = (op: string) => {
    const colors: Record<string, string> = {
      'CUT': 'bg-red-600',
      'FADE': 'bg-blue-600',
      'SPEED': 'bg-green-600',
      'TRANSITION': 'bg-purple-600',
      'OVERLAY': 'bg-yellow-600',
      'AUDIO_MIX': 'bg-orange-600',
      'SYNC': 'bg-pink-600'
    };
    return colors[op] || 'bg-zinc-600';
  };

  if (!previewUrl && !operationId) {
    return (
      <Card className={`bg-zinc-900 border-zinc-700 ${className}`}>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center text-zinc-400">
            <FileVideo className="w-12 h-12 mx-auto mb-2" />
            <p>No video preview available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={`bg-zinc-900 border-zinc-700 ${className}`}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-white">
          <div className="flex items-center gap-2">
            <FileVideo className="w-5 h-5" />
            Video Preview
            {operation && (
              <Badge 
                className={`${getOperationBadgeColor(operation.operation)} text-white`}
              >
                {operation.operation}
              </Badge>
            )}
          </div>
          
          {operation && (
            <Badge 
              variant={operation.confidence > 0.8 ? "default" : "secondary"}
              className="text-xs"
            >
              {Math.round(operation.confidence * 100)}% confident
            </Badge>
          )}
        </CardTitle>
        
        {operation && (
          <p className="text-sm text-zinc-400">{operation.explanation}</p>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Video Player */}
        <div 
          ref={containerRef}
          className="relative bg-black rounded-lg overflow-hidden aspect-video"
        >
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-zinc-800">
              <div className="text-center text-zinc-400">
                <Loader2 className="w-8 h-8 mx-auto mb-2 animate-spin" />
                <p>Loading preview...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-zinc-800">
              <div className="text-center text-red-400">
                <AlertCircle className="w-8 h-8 mx-auto mb-2" />
                <p>{error}</p>
              </div>
            </div>
          )}

          {previewUrl && (
            <video
              ref={videoRef}
              src={previewUrl}
              className="w-full h-full object-contain"
              onLoadStart={() => setIsLoading(true)}
            />
          )}

          {/* Video Controls Overlay */}
          {!isLoading && !error && (
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 hover:opacity-100 transition-opacity">
              <div className="absolute bottom-0 left-0 right-0 p-4 space-y-2">
                {/* Progress Bar */}
                <div className="w-full bg-zinc-700 rounded-full h-1">
                  <div 
                    className="bg-blue-600 h-1 rounded-full transition-all"
                    style={{ width: `${(currentTime / duration) * 100}%` }}
                  />
                </div>

                {/* Controls */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleSkipBackward}
                      className="text-white hover:bg-zinc-700"
                    >
                      <SkipBack className="w-4 h-4" />
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handlePlayPause}
                      className="text-white hover:bg-zinc-700"
                    >
                      {isPlaying ? (
                        <PauseCircle className="w-5 h-5" />
                      ) : (
                        <PlayCircle className="w-5 h-5" />
                      )}
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleSkipForward}
                      className="text-white hover:bg-zinc-700"
                    >
                      <SkipForward className="w-4 h-4" />
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleMuteToggle}
                      className="text-white hover:bg-zinc-700"
                    >
                      {isMuted ? (
                        <VolumeX className="w-4 h-4" />
                      ) : (
                        <Volume2 className="w-4 h-4" />
                      )}
                    </Button>

                    <div className="flex items-center gap-1 text-white text-xs">
                      <Clock className="w-3 h-3" />
                      {formatTime(currentTime)} / {formatTime(duration)}
                    </div>
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleFullscreen}
                    className="text-white hover:bg-zinc-700"
                  >
                    <Maximize className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Operation Details */}
        {operation && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-zinc-400">Operation:</span>
              <Badge variant="outline" className="text-xs">
                {operation.operation}
              </Badge>
            </div>
            
            {operation.parameters && (
              <div className="text-xs text-zinc-500">
                <span className="font-medium">Parameters:</span>
                <pre className="mt-1 p-2 bg-zinc-800 rounded text-zinc-400 overflow-x-auto">
                  {JSON.stringify(operation.parameters, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2">
          {previewUrl && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(previewUrl, '_blank')}
              className="flex-1"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Open in New Tab
            </Button>
          )}

          {operationId && outputPath && (
            <Button
              variant="default"
              size="sm"
              onClick={handleDownloadClick}
              className="flex-1 bg-blue-600 hover:bg-blue-700"
            >
              <Download className="w-4 h-4 mr-2" />
              Download Result
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}