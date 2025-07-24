import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { 
  PlayCircle, 
  PauseCircle, 
  SkipBack, 
  SkipForward, 
  Volume2, 
  VolumeX,
  Maximize,
  Minimize,
  FastForward,
  Rewind,
  RefreshCw,
  Download,
  Share2,
  Settings,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle,
  Film,
  Camera,
  Info,
  Grid,
  Square,
  Sliders
} from 'lucide-react';

interface PreviewScrubberProps {
  videoUrl?: string;
  projectId?: string;
  currentTime?: number;
  duration?: number;
  frameRate?: number;
  onTimeUpdate?: (time: number) => void;
  onFrameCapture?: (frame: string) => void;
  onRangeSelect?: (start: number, end: number) => void;
  className?: string;
}

interface FrameData {
  time: number;
  thumbnail?: string;
  isKeyframe?: boolean;
}

// Professional playback rates
const PLAYBACK_RATES = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 2, 4];

// Frame navigation presets
const FRAME_JUMPS = {
  SINGLE: 1,
  SMALL: 5,
  MEDIUM: 15,
  LARGE: 30,
  SECOND: 30 // Assuming 30fps
};

export default function PreviewScrubber({ 
  videoUrl,
  projectId,
  currentTime: externalTime,
  duration: externalDuration,
  frameRate = 30,
  onTimeUpdate,
  onFrameCapture,
  onRangeSelect,
  className = '' 
}: PreviewScrubberProps) {
  // State management
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(externalTime || 0);
  const [duration, setDuration] = useState(externalDuration || 0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFrameGrid, setShowFrameGrid] = useState(false);
  const [showWaveform, setShowWaveform] = useState(true);
  const [selectedRange, setSelectedRange] = useState<{ start: number; end: number } | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);
  const [hoveredTime, setHoveredTime] = useState<number | null>(null);
  const [frameCache, setFrameCache] = useState<Map<number, FrameData>>(new Map());
  const [isCapturing, setIsCapturing] = useState(false);
  const [resolution, setResolution] = useState({ width: 0, height: 0 });
  const [buffered, setBuffered] = useState<{ start: number; end: number }[]>([]);

  // Refs
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);
  const scrubberRef = useRef<HTMLDivElement>(null);

  // Animation frame for smooth playback
  const animationFrameRef = useRef<number>();
  const lastUpdateRef = useRef<number>(0);

  // Load video metadata
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !videoUrl) return;

    const handleLoadedMetadata = () => {
      setDuration(video.duration);
      setResolution({ width: video.videoWidth, height: video.videoHeight });
      setIsLoading(false);
      
      // Generate initial frame cache
      generateFrameCache();
    };

    const handleTimeUpdate = () => {
      // Throttle updates for performance
      const now = performance.now();
      if (now - lastUpdateRef.current > 16) { // ~60fps
        setCurrentTime(video.currentTime);
        lastUpdateRef.current = now;
      }
    };

    const handleError = () => {
      setError('Failed to load video');
      setIsLoading(false);
    };

    const handleEnded = () => {
      setIsPlaying(false);
    };

    const handleProgress = () => {
      // Update buffered ranges
      const bufferedRanges: { start: number; end: number }[] = [];
      for (let i = 0; i < video.buffered.length; i++) {
        bufferedRanges.push({
          start: video.buffered.start(i),
          end: video.buffered.end(i)
        });
      }
      setBuffered(bufferedRanges);
    };

    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('error', handleError);
    video.addEventListener('ended', handleEnded);
    video.addEventListener('progress', handleProgress);

    return () => {
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('error', handleError);
      video.removeEventListener('ended', handleEnded);
      video.removeEventListener('progress', handleProgress);
    };
  }, [videoUrl]);

  // Sync with external time changes
  useEffect(() => {
    if (externalTime !== undefined && Math.abs(externalTime - currentTime) > 0.1) {
      seekToTime(externalTime);
    }
  }, [externalTime]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      const video = videoRef.current;
      if (!video) return;

      switch (e.key) {
        case ' ':
          e.preventDefault();
          handlePlayPause();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          if (e.shiftKey) {
            seekByFrames(-FRAME_JUMPS.LARGE);
          } else if (e.ctrlKey || e.metaKey) {
            seekByFrames(-FRAME_JUMPS.SECOND);
          } else {
            seekByFrames(-FRAME_JUMPS.SINGLE);
          }
          break;
        case 'ArrowRight':
          e.preventDefault();
          if (e.shiftKey) {
            seekByFrames(FRAME_JUMPS.LARGE);
          } else if (e.ctrlKey || e.metaKey) {
            seekByFrames(FRAME_JUMPS.SECOND);
          } else {
            seekByFrames(FRAME_JUMPS.SINGLE);
          }
          break;
        case 'Home':
          e.preventDefault();
          seekToTime(0);
          break;
        case 'End':
          e.preventDefault();
          seekToTime(duration);
          break;
        case 'm':
          e.preventDefault();
          handleMuteToggle();
          break;
        case 'f':
          e.preventDefault();
          handleFullscreen();
          break;
        case 'i':
          e.preventDefault();
          if (selectedRange) {
            seekToTime(selectedRange.start);
          }
          break;
        case 'o':
          e.preventDefault();
          if (selectedRange) {
            seekToTime(selectedRange.end);
          }
          break;
        case 'c':
          e.preventDefault();
          handleFrameCapture();
          break;
        case '-':
        case '_':
          e.preventDefault();
          changePlaybackRate(-1);
          break;
        case '=':
        case '+':
          e.preventDefault();
          changePlaybackRate(1);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [currentTime, duration, selectedRange]);

  // Generate frame cache for timeline
  const generateFrameCache = useCallback(async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || !duration) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Generate thumbnails at regular intervals
    const interval = Math.max(1, duration / 100); // 100 thumbnails max
    const frames = new Map<number, FrameData>();

    for (let time = 0; time < duration; time += interval) {
      frames.set(time, {
        time,
        isKeyframe: time % 5 === 0 // Mark every 5 seconds as keyframe
      });
    }

    setFrameCache(frames);
  }, [duration]);

  // Playback controls
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

  const seekToTime = (time: number) => {
    const video = videoRef.current;
    if (!video) return;

    const clampedTime = Math.max(0, Math.min(time, duration));
    video.currentTime = clampedTime;
    setCurrentTime(clampedTime);
    
    if (onTimeUpdate) {
      onTimeUpdate(clampedTime);
    }
  };

  const seekByFrames = (frames: number) => {
    const frameDuration = 1 / frameRate;
    seekToTime(currentTime + (frames * frameDuration));
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

  const changePlaybackRate = (direction: number) => {
    const currentIndex = PLAYBACK_RATES.indexOf(playbackRate);
    const newIndex = Math.max(0, Math.min(PLAYBACK_RATES.length - 1, currentIndex + direction));
    const newRate = PLAYBACK_RATES[newIndex];
    
    const video = videoRef.current;
    if (video) {
      video.playbackRate = newRate;
    }
    setPlaybackRate(newRate);
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

  // Frame capture
  const handleFrameCapture = async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    setIsCapturing(true);

    try {
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      const frameData = canvas.toDataURL('image/png');
      
      if (onFrameCapture) {
        onFrameCapture(frameData);
      }

      // Download the frame
      const link = document.createElement('a');
      link.download = `frame_${formatTimecode(currentTime)}.png`;
      link.href = frameData;
      link.click();
    } catch (error) {
      console.error('Error capturing frame:', error);
    }

    setIsCapturing(false);
  };

  // Timeline interaction
  const handleTimelineClick = (e: React.MouseEvent) => {
    if (!timelineRef.current) return;

    const rect = timelineRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const clickTime = (x / rect.width) * duration;

    if (e.shiftKey && !isSelecting) {
      // Start range selection
      setIsSelecting(true);
      setSelectedRange({ start: clickTime, end: clickTime });
    } else if (isSelecting) {
      // Complete range selection
      if (selectedRange) {
        const newRange = {
          start: Math.min(selectedRange.start, clickTime),
          end: Math.max(selectedRange.start, clickTime)
        };
        setSelectedRange(newRange);
        setIsSelecting(false);
        
        if (onRangeSelect) {
          onRangeSelect(newRange.start, newRange.end);
        }
      }
    } else {
      // Normal seek
      seekToTime(clickTime);
    }
  };

  const handleTimelineMouseMove = (e: React.MouseEvent) => {
    if (!timelineRef.current) return;

    const rect = timelineRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const hoverTime = (x / rect.width) * duration;
    
    setHoveredTime(hoverTime);

    if (isSelecting && selectedRange) {
      setSelectedRange({
        start: selectedRange.start,
        end: hoverTime
      });
    }
  };

  const handleTimelineMouseLeave = () => {
    setHoveredTime(null);
    if (isSelecting) {
      setIsSelecting(false);
    }
  };

  // Format helpers
  const formatTimecode = (time: number) => {
    const hours = Math.floor(time / 3600);
    const minutes = Math.floor((time % 3600) / 60);
    const seconds = Math.floor(time % 60);
    const frames = Math.floor((time % 1) * frameRate);

    if (hours > 0) {
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}:${frames.toString().padStart(2, '0')}`;
    } else {
      return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}:${frames.toString().padStart(2, '0')}`;
    }
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const getCurrentFrame = () => {
    return Math.floor(currentTime * frameRate);
  };

  const getTotalFrames = () => {
    return Math.floor(duration * frameRate);
  };

  if (!videoUrl) {
    return (
      <Card className={`h-full flex items-center justify-center bg-zinc-900 border-zinc-700 ${className}`}>
        <div className="text-center text-zinc-400">
          <Film className="w-12 h-12 mx-auto mb-2" />
          <p>No video loaded</p>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`h-full flex items-center justify-center bg-zinc-900 border-zinc-700 ${className}`}>
        <div className="text-center text-red-400">
          <AlertCircle className="w-12 h-12 mx-auto mb-2" />
          <p>{error}</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className={`h-full flex flex-col bg-zinc-900 border-zinc-700 ${className}`}>
      <CardHeader className="flex-shrink-0 border-b border-zinc-700">
        <CardTitle className="flex items-center justify-between text-white">
          <div className="flex items-center gap-2">
            <Film className="w-5 h-5" />
            Frame-Accurate Preview
            {resolution.width > 0 && (
              <Badge variant="outline" className="text-xs">
                {resolution.width}×{resolution.height} @ {frameRate}fps
              </Badge>
            )}
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-zinc-400">
              <span>Frame {getCurrentFrame()} / {getTotalFrames()}</span>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowFrameGrid(!showFrameGrid)}
                className={showFrameGrid ? 'text-blue-400' : 'text-zinc-400'}
              >
                <Grid className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowWaveform(!showWaveform)}
                className={showWaveform ? 'text-blue-400' : 'text-zinc-400'}
              >
                <Volume2 className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleFrameCapture}
                disabled={isCapturing}
                className="text-zinc-400 hover:text-white"
              >
                {isCapturing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Camera className="w-4 h-4" />}
              </Button>
            </div>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        {/* Video Container */}
        <div 
          ref={containerRef}
          className="relative flex-1 bg-black overflow-hidden"
        >
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-zinc-800 z-20">
              <div className="text-center text-zinc-400">
                <Loader2 className="w-8 h-8 mx-auto mb-2 animate-spin" />
                <p>Loading video...</p>
              </div>
            </div>
          )}

          <video
            ref={videoRef}
            src={videoUrl}
            className="w-full h-full object-contain"
            onLoadStart={() => setIsLoading(true)}
            crossOrigin="anonymous"
          />

          {/* Frame grid overlay */}
          {showFrameGrid && (
            <div className="absolute inset-0 pointer-events-none">
              <svg className="w-full h-full">
                <defs>
                  <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                    <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="1"/>
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />
              </svg>
            </div>
          )}

          {/* Hidden canvas for frame capture */}
          <canvas ref={canvasRef} className="hidden" />
        </div>

        {/* Timeline Scrubber */}
        <div className="border-t border-zinc-700 p-4 bg-zinc-950">
          {/* Timecode Display */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-4">
              <div className="font-mono text-2xl text-white">
                {formatTimecode(currentTime)}
              </div>
              <div className="text-sm text-zinc-400">
                / {formatTimecode(duration)}
              </div>
              {selectedRange && (
                <Badge variant="outline" className="text-xs">
                  Range: {formatTime(selectedRange.end - selectedRange.start)}
                </Badge>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              <Badge 
                variant={playbackRate === 1 ? 'secondary' : 'default'}
                className="text-xs"
              >
                {playbackRate}x
              </Badge>
            </div>
          </div>

          {/* Timeline */}
          <div 
            ref={timelineRef}
            className="relative h-16 bg-zinc-800 rounded-lg mb-3 cursor-pointer"
            onClick={handleTimelineClick}
            onMouseMove={handleTimelineMouseMove}
            onMouseLeave={handleTimelineMouseLeave}
          >
            {/* Buffered ranges */}
            {buffered.map((range, index) => (
              <div
                key={index}
                className="absolute top-0 bottom-0 bg-zinc-700 opacity-50"
                style={{
                  left: `${(range.start / duration) * 100}%`,
                  width: `${((range.end - range.start) / duration) * 100}%`
                }}
              />
            ))}

            {/* Selected range */}
            {selectedRange && (
              <div
                className="absolute top-0 bottom-0 bg-blue-500 opacity-30"
                style={{
                  left: `${(Math.min(selectedRange.start, selectedRange.end) / duration) * 100}%`,
                  width: `${(Math.abs(selectedRange.end - selectedRange.start) / duration) * 100}%`
                }}
              />
            )}

            {/* Waveform visualization */}
            {showWaveform && (
              <div className="absolute inset-0 flex items-center opacity-30">
                {Array.from({ length: 100 }, (_, i) => (
                  <div
                    key={i}
                    className="flex-1 h-full flex items-center justify-center"
                  >
                    <div 
                      className="w-full bg-green-500"
                      style={{ height: `${20 + Math.random() * 60}%` }}
                    />
                  </div>
                ))}
              </div>
            )}

            {/* Frame markers */}
            <div className="absolute inset-0">
              {Array.from(frameCache.entries()).map(([time, frame]) => (
                <div
                  key={time}
                  className={`absolute top-0 bottom-0 w-px ${
                    frame.isKeyframe ? 'bg-yellow-500' : 'bg-zinc-600'
                  }`}
                  style={{ left: `${(time / duration) * 100}%` }}
                />
              ))}
            </div>

            {/* Playhead */}
            <div
              ref={scrubberRef}
              className="absolute top-0 bottom-0 w-1 bg-red-500"
              style={{ left: `${(currentTime / duration) * 100}%` }}
            >
              <div className="absolute -top-2 -left-2 w-5 h-5 bg-red-500 rounded-full" />
              <div className="absolute -bottom-8 -left-12 bg-red-500 text-white text-xs px-2 py-1 rounded">
                {formatTimecode(currentTime)}
              </div>
            </div>

            {/* Hover indicator */}
            {hoveredTime !== null && (
              <div
                className="absolute top-0 bottom-0 w-px bg-white opacity-50"
                style={{ left: `${(hoveredTime / duration) * 100}%` }}
              >
                <div className="absolute -top-6 -left-12 bg-zinc-700 text-white text-xs px-2 py-1 rounded">
                  {formatTimecode(hoveredTime)}
                </div>
              </div>
            )}
          </div>

          {/* Transport Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {/* Frame navigation */}
              <Button
                variant="outline"
                size="sm"
                onClick={() => seekByFrames(-FRAME_JUMPS.SECOND)}
                className="bg-zinc-800 border-zinc-600"
                title="Back 1 second (Ctrl+←)"
              >
                <Rewind className="w-4 h-4" />
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => seekByFrames(-FRAME_JUMPS.SINGLE)}
                className="bg-zinc-800 border-zinc-600"
                title="Previous frame (←)"
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              
              <Button
                onClick={handlePlayPause}
                className="bg-blue-600 hover:bg-blue-700 px-4"
                title="Play/Pause (Space)"
              >
                {isPlaying ? <PauseCircle className="w-5 h-5" /> : <PlayCircle className="w-5 h-5" />}
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => seekByFrames(FRAME_JUMPS.SINGLE)}
                className="bg-zinc-800 border-zinc-600"
                title="Next frame (→)"
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => seekByFrames(FRAME_JUMPS.SECOND)}
                className="bg-zinc-800 border-zinc-600"
                title="Forward 1 second (Ctrl+→)"
              >
                <FastForward className="w-4 h-4" />
              </Button>

              <div className="w-px h-6 bg-zinc-700 mx-2" />

              {/* Volume controls */}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleMuteToggle}
                className="text-zinc-400 hover:text-white"
              >
                {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
              </Button>
              
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={isMuted ? 0 : volume}
                onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                className="w-20 h-1 bg-zinc-700 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <div className="flex items-center gap-2">
              {/* Playback rate */}
              <Button
                variant="outline"
                size="sm"
                onClick={() => changePlaybackRate(-1)}
                className="bg-zinc-800 border-zinc-600"
                title="Decrease speed (-)"
              >
                <ChevronLeft className="w-3 h-3" />
              </Button>
              
              <span className="text-sm text-zinc-400 w-12 text-center">
                {playbackRate}x
              </span>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => changePlaybackRate(1)}
                className="bg-zinc-800 border-zinc-600"
                title="Increase speed (+)"
              >
                <ChevronRight className="w-3 h-3" />
              </Button>

              <div className="w-px h-6 bg-zinc-700 mx-2" />

              {/* Range controls */}
              {selectedRange && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => seekToTime(selectedRange.start)}
                    className="bg-zinc-800 border-zinc-600"
                    title="Go to range start (I)"
                  >
                    <SkipBack className="w-4 h-4" />
                  </Button>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => seekToTime(selectedRange.end)}
                    className="bg-zinc-800 border-zinc-600"
                    title="Go to range end (O)"
                  >
                    <SkipForward className="w-4 h-4" />
                  </Button>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedRange(null)}
                    className="bg-zinc-800 border-zinc-600 text-red-400"
                  >
                    Clear Range
                  </Button>
                  
                  <div className="w-px h-6 bg-zinc-700 mx-2" />
                </>
              )}

              {/* Other controls */}
              <Button
                variant="outline"
                size="sm"
                onClick={handleFullscreen}
                className="bg-zinc-800 border-zinc-600"
                title="Fullscreen (F)"
              >
                {isFullscreen ? <Minimize className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleFrameCapture}
                disabled={isCapturing}
                className="bg-zinc-800 border-zinc-600"
                title="Capture frame (C)"
              >
                {isCapturing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              </Button>
            </div>
          </div>

          {/* Keyboard shortcuts help */}
          <div className="mt-3 pt-3 border-t border-zinc-700 text-xs text-zinc-500">
            <div className="flex items-center gap-1">
              <Info className="w-3 h-3" />
              <span>Keyboard shortcuts:</span>
              <kbd className="px-1 py-0.5 bg-zinc-800 rounded ml-2">Space</kbd> Play/Pause
              <kbd className="px-1 py-0.5 bg-zinc-800 rounded ml-2">←/→</kbd> Frame step
              <kbd className="px-1 py-0.5 bg-zinc-800 rounded ml-2">Shift+←/→</kbd> 30 frames
              <kbd className="px-1 py-0.5 bg-zinc-800 rounded ml-2">-/+</kbd> Speed
              <kbd className="px-1 py-0.5 bg-zinc-800 rounded ml-2">C</kbd> Capture
              <kbd className="px-1 py-0.5 bg-zinc-800 rounded ml-2">F</kbd> Fullscreen
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}